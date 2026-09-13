from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST

from .accounts import get_or_create_profile
from .forms import (
    AccountAuthenticationForm,
    CommentForm,
    PostForm,
    ProfileForm,
    RegistrationForm,
)
from .markdown import render_markdown_document
from .models import Category, Comment, Post, Tag
from .site_content import ABOUT_PROFILE


COMMENT_COOLDOWN_SECONDS = 30


class AccountLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = AccountAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        get_or_create_profile(form.get_user())
        messages.success(self.request, "欢迎回来。")
        return super().form_valid(form)

    def get_success_url(self):
        redirect_url = self.get_redirect_url()
        if redirect_url:
            return redirect_url
        if self.request.user.is_staff:
            return reverse("blog:dashboard")
        return reverse("blog:home")


class AccountPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("blog:profile")

    def form_valid(self, form):
        messages.success(self.request, "密码已经更新。")
        return super().form_valid(form)


def safe_next_url(request):
    candidate = request.POST.get("next") or request.GET.get("next") or ""
    if url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return ""


def register(request):
    if request.user.is_authenticated:
        return redirect("blog:dashboard" if request.user.is_staff else "blog:home")

    next_url = safe_next_url(request)
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, "账号已经创建，欢迎来到这里。")
        return redirect(next_url or "blog:home")
    return render(
        request,
        "registration/register.html",
        {"form": form, "next": next_url},
    )


@login_required(login_url="blog:login")
def profile(request):
    account_profile = get_or_create_profile(request.user)
    form = ProfileForm(request.POST or None, instance=account_profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "公开昵称已经更新。")
        return redirect("blog:profile")
    return render(request, "registration/profile.html", {"form": form})


def visible_posts(user):
    return (
        Post.objects.visible_to(user)
        .select_related("category")
        .prefetch_related("tags")
    )


def post_detail_context(request, post, comment_form=None):
    rendered_content, toc = render_markdown_document(post.content)
    neighboring_posts = visible_posts(request.user).exclude(published_at__isnull=True)
    previous_post = None
    next_post = None
    if post.published_at:
        previous_post = neighboring_posts.filter(
            published_at__lt=post.published_at
        ).order_by("-published_at", "-pk").first()
        next_post = neighboring_posts.filter(
            published_at__gt=post.published_at
        ).order_by("published_at", "pk").first()

    related_filter = Q()
    has_related_filter = False
    if post.category_id:
        related_filter |= Q(category_id=post.category_id)
        has_related_filter = True
    tag_ids = list(post.tags.values_list("pk", flat=True))
    if tag_ids:
        related_filter |= Q(tags__in=tag_ids)
        has_related_filter = True
    related_posts = []
    if has_related_filter:
        related_posts = list(
            visible_posts(request.user)
            .exclude(pk=post.pk)
            .filter(related_filter)
            .distinct()
            .order_by("-is_featured", "-published_at", "-created_at")[:3]
        )

    return {
        "post": post,
        "rendered_content": rendered_content,
        "toc": toc if len(toc) > 1 else [],
        "previous_post": previous_post,
        "next_post": next_post,
        "related_posts": related_posts,
        "canonical_url": request.build_absolute_uri(post.get_absolute_url()),
        "og_image_url": request.build_absolute_uri(post.cover.url) if post.cover else "",
        "approved_comments": post.comments.approved().select_related("author"),
        "comment_form": comment_form or CommentForm(),
        "comment_login_url": (
            f"{reverse('blog:login')}?"
            f"{urlencode({'next': f'{post.get_absolute_url()}#comments'})}"
        ),
    }


def home(request):
    all_posts = visible_posts(request.user)
    featured_posts = list(all_posts.filter(is_featured=True)[:2])
    if not featured_posts:
        featured_posts = list(all_posts[:1])
    featured_ids = [post.pk for post in featured_posts]
    posts = all_posts.exclude(pk__in=featured_ids)[:6]
    return render(
        request,
        "blog/home.html",
        {"featured_posts": featured_posts, "posts": posts},
    )


def post_list(request):
    paginator = Paginator(visible_posts(request.user), 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "blog/post_list.html", {"page_obj": page_obj})


def search(request):
    keyword = request.GET.get("q", "").strip()[:100]
    posts = visible_posts(request.user).none()
    if keyword:
        posts = visible_posts(request.user).filter(
            Q(title__icontains=keyword)
            | Q(summary__icontains=keyword)
            | Q(content__icontains=keyword)
        )
    page_obj = Paginator(posts, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "blog/search.html",
        {"page_obj": page_obj, "keyword": keyword},
    )


def post_detail(request, slug):
    post = get_object_or_404(visible_posts(request.user), slug=slug)
    return render(request, "blog/post_detail.html", post_detail_context(request, post))


@require_POST
def add_comment(request, slug):
    post = get_object_or_404(
        Post.objects.public().select_related("category").prefetch_related("tags"),
        slug=slug,
    )

    if not request.user.is_authenticated:
        login_url = reverse("blog:login")
        next_url = f"{post.get_absolute_url()}#comments"
        return redirect(f"{login_url}?{urlencode({'next': next_url})}")

    # 蜜罐字段被填写时静默丢弃，避免向机器人暴露拦截规则。
    if request.POST.get("website", "").strip():
        return redirect(f"{post.get_absolute_url()}#comments")

    form = CommentForm(request.POST)
    last_submitted = request.session.get("last_comment_at", 0)
    too_frequent = timezone.now().timestamp() - last_submitted < COMMENT_COOLDOWN_SECONDS

    if too_frequent:
        form.add_error(None, "提交得有些快，请稍等片刻再试。")

    if form.is_valid() and not too_frequent:
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.name = get_or_create_profile(request.user).display_name
        comment.email = ""
        comment.status = Comment.Status.APPROVED
        comment.save()
        request.session["last_comment_at"] = timezone.now().timestamp()
        messages.success(request, "评论已经发布。")
        return redirect(f"{post.get_absolute_url()}#comments")

    context = post_detail_context(request, post, comment_form=form)
    return render(request, "blog/post_detail.html", context, status=400)


def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = visible_posts(request.user).filter(category=category)
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "blog/category_posts.html",
        {"category": category, "page_obj": page_obj},
    )


def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = visible_posts(request.user).filter(tags=tag)
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "blog/tag_posts.html", {"tag": tag, "page_obj": page_obj})


def archive(request):
    posts = visible_posts(request.user).exclude(published_at__isnull=True).order_by("-published_at")
    archive_years = []

    for post in posts:
        local_date = timezone.localtime(post.published_at).date()
        if not archive_years or archive_years[-1]["year"] != local_date.year:
            archive_years.append({"year": local_date.year, "months": []})
        months = archive_years[-1]["months"]
        if not months or months[-1]["month"] != local_date.month:
            months.append({"month": local_date.month, "date": local_date, "posts": []})
        months[-1]["posts"].append(post)

    return render(request, "blog/archive.html", {"archive_years": archive_years})


def about(request):
    return render(request, "blog/about.html", {"profile": ABOUT_PROFILE})


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    content = f"User-agent: *\nAllow: /\n\nSitemap: {sitemap_url}\n"
    return HttpResponse(content, content_type="text/plain; charset=utf-8")


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "你已安全退出。")
    return redirect("blog:home")


@staff_member_required(login_url="blog:login")
def dashboard(request):
    posts = Post.objects.select_related("category").prefetch_related("tags")
    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    visibility = request.GET.get("visibility", "")

    if keyword:
        posts = posts.filter(Q(title__icontains=keyword) | Q(summary__icontains=keyword))
    if status in Post.Status.values:
        posts = posts.filter(status=status)
    if visibility in Post.Visibility.values:
        posts = posts.filter(visibility=visibility)

    page_obj = Paginator(posts, 15).get_page(request.GET.get("page"))
    statistics = Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
    )
    statistics["pending_comments"] = Comment.objects.filter(
        status=Comment.Status.PENDING
    ).count()

    return render(
        request,
        "dashboard/index.html",
        {
            "page_obj": page_obj,
            "statistics": statistics,
            "keyword": keyword,
            "selected_status": status,
            "selected_visibility": visibility,
            "status_choices": Post.Status.choices,
            "visibility_choices": Post.Visibility.choices,
        },
    )


@staff_member_required(login_url="blog:login")
def dashboard_post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save()
        messages.success(request, f"《{post.title}》已创建。")
        return redirect(post.get_absolute_url())
    return render(request, "dashboard/post_form.html", {"form": form, "mode": "create"})


@staff_member_required(login_url="blog:login")
def dashboard_post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        post = form.save()
        messages.success(request, f"《{post.title}》已保存。")
        return redirect(post.get_absolute_url())
    return render(
        request,
        "dashboard/post_form.html",
        {"form": form, "post": post, "mode": "update"},
    )


@staff_member_required(login_url="blog:login")
def dashboard_post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        title = post.title
        post.delete()
        messages.success(request, f"《{title}》已删除。")
        return redirect("blog:dashboard")
    return render(request, "dashboard/post_confirm_delete.html", {"post": post})


@require_POST
@staff_member_required(login_url="blog:login")
def dashboard_post_status(request, pk):
    post = get_object_or_404(Post, pk=pk)
    target_status = request.POST.get("status")
    if target_status not in Post.Status.values:
        messages.error(request, "无法识别文章状态。")
        return redirect("blog:dashboard")
    post.status = target_status
    post.save(update_fields=["status", "updated_at"])
    messages.success(request, f"《{post.title}》已设为{post.get_status_display()}。")
    return redirect("blog:dashboard")


@staff_member_required(login_url="blog:login")
def comment_moderation(request):
    selected_status = request.GET.get("status", "all")
    comments = Comment.objects.select_related("post", "author")
    if selected_status in Comment.Status.values:
        comments = comments.filter(status=selected_status)
    else:
        selected_status = "all"
    page_obj = Paginator(comments.order_by("-created_at"), 20).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/comments.html",
        {
            "page_obj": page_obj,
            "selected_status": selected_status,
            "status_choices": Comment.Status.choices,
        },
    )


@require_POST
@staff_member_required(login_url="blog:login")
def comment_change_status(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    target_status = request.POST.get("status")
    if target_status not in Comment.Status.values:
        messages.error(request, "无法识别评论状态。")
        return redirect("blog:comment_moderation")
    comment.status = target_status
    comment.save(update_fields=["status", "updated_at"])
    messages.success(request, f"评论已设为{comment.get_status_display()}。")
    return redirect("blog:comment_moderation")


@staff_member_required(login_url="blog:login")
def comment_delete(request, pk):
    comment = get_object_or_404(Comment.objects.select_related("post"), pk=pk)
    if request.method == "POST":
        comment.delete()
        messages.success(request, "评论已删除。")
        return redirect("blog:comment_moderation")
    return render(request, "dashboard/comment_confirm_delete.html", {"comment": comment})


def custom_404(request, exception):
    return render(request, "errors/404.html", status=404)


def custom_500(request):
    return render(request, "errors/500.html", status=500)
