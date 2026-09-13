import math
import re

from django.conf import settings
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.text import slugify


def build_unique_slug(instance, value: str) -> str:
    """生成可读且唯一的 slug，保留中文字符。"""
    field = instance._meta.get_field("slug")
    max_length = field.max_length
    base = slugify(value, allow_unicode=True)[:max_length] or "item"
    candidate = base
    number = 2
    queryset = type(instance).objects.exclude(pk=instance.pk)

    while queryset.filter(slug=candidate).exists():
        suffix = f"-{number}"
        candidate = f"{base[: max_length - len(suffix)]}{suffix}"
        number += 1
    return candidate


class Category(models.Model):
    name = models.CharField("名称", max_length=100, unique=True)
    slug = models.SlugField("URL 标识", max_length=100, unique=True, blank=True, allow_unicode=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "分类"
        verbose_name_plural = "分类"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:category", kwargs={"slug": self.slug})


class Tag(models.Model):
    name = models.CharField("名称", max_length=100, unique=True)
    slug = models.SlugField("URL 标识", max_length=100, unique=True, blank=True, allow_unicode=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "标签"
        verbose_name_plural = "标签"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:tag", kwargs={"slug": self.slug})


class PostQuerySet(models.QuerySet):
    def public(self):
        return self.filter(
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
            published_at__lte=timezone.now(),
        )

    def visible_to(self, user):
        if getattr(user, "is_staff", False):
            return self
        return self.public()


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "公开"
        PRIVATE = "private", "私密"

    title = models.CharField("标题", max_length=200)
    slug = models.SlugField("URL 标识", max_length=220, unique=True, blank=True, allow_unicode=True)
    summary = models.CharField("摘要", max_length=300, blank=True)
    content = models.TextField("正文（Markdown）")
    cover = models.ImageField("封面", upload_to="posts/covers/%Y/%m/", blank=True)
    category = models.ForeignKey(
        Category,
        verbose_name="分类",
        related_name="posts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(Tag, verbose_name="标签", related_name="posts", blank=True)
    is_featured = models.BooleanField("首页精选", default=False, db_index=True)
    status = models.CharField("状态", max_length=10, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(
        "可见性", max_length=10, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("最后修改", auto_now=True)
    published_at = models.DateTimeField("发布时间", null=True, blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(
                fields=["status", "visibility", "published_at"],
                name="post_public_idx",
            )
        ]
        verbose_name = "文章"
        verbose_name_plural = "文章"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        changed_fields = set(kwargs.get("update_fields") or [])
        if not self.slug:
            self.slug = build_unique_slug(self, self.title)
            changed_fields.add("slug")
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
            changed_fields.add("published_at")
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = changed_fields
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    @property
    def reading_time(self) -> int:
        """按中文字符与英文单词的常见阅读速度估算分钟数。"""
        text = re.sub(r"```.*?```", " ", self.content or "", flags=re.DOTALL)
        chinese_characters = len(re.findall(r"[\u3400-\u9fff]", text))
        latin_words = len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'-]*\b", text))
        return max(1, math.ceil(chinese_characters / 400 + latin_words / 220))

    @property
    def seo_description(self) -> str:
        source = self.summary or self.content or self.title
        plain_text = re.sub(r"[`*_>#\[\]()!~-]+", " ", source)
        plain_text = " ".join(plain_text.split())
        return Truncator(plain_text).chars(155)

    @property
    def is_publicly_visible(self) -> bool:
        return bool(
            self.status == self.Status.PUBLISHED
            and self.visibility == self.Visibility.PUBLIC
            and self.published_at
            and self.published_at <= timezone.now()
        )


class CommentQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=Comment.Status.APPROVED)


class Comment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已拒绝"

    post = models.ForeignKey(
        Post,
        verbose_name="文章",
        related_name="comments",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="登录用户",
        related_name="blog_comments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField("昵称", max_length=80)
    email = models.EmailField("邮箱")
    content = models.TextField(
        "评论内容",
        validators=[MinLengthValidator(2), MaxLengthValidator(2000)],
        max_length=2000,
    )
    status = models.CharField(
        "审核状态",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField("提交时间", auto_now_add=True)
    updated_at = models.DateTimeField("修改时间", auto_now=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["post", "status", "created_at"],
                name="comment_review_idx",
            )
        ]
        verbose_name = "评论"
        verbose_name_plural = "评论"

    def __str__(self) -> str:
        return f"{self.name} 评论《{self.post.title}》"
