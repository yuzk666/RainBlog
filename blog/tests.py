from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Category, Comment, Post, Profile, Tag


class BlogVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="生活", slug="life")
        cls.tag = Tag.objects.create(name="随笔", slug="essay")
        cls.public_post = Post.objects.create(
            title="公开文章",
            slug="public-post",
            summary="任何人都可以阅读",
            content="# 正文\n\n这是一篇公开文章。",
            category=cls.category,
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
        )
        cls.public_post.tags.add(cls.tag)
        cls.private_post = Post.objects.create(
            title="私密文章",
            slug="private-post",
            content="只允许管理员阅读。",
            category=cls.category,
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PRIVATE,
        )
        cls.private_post.tags.add(cls.tag)
        cls.draft_post = Post.objects.create(
            title="草稿文章",
            slug="draft-post",
            content="尚未发布。",
            category=cls.category,
            status=Post.Status.DRAFT,
            visibility=Post.Visibility.PUBLIC,
        )
        cls.draft_post.tags.add(cls.tag)
        cls.admin = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password-123",
        )

    def test_home_returns_200(self):
        response = self.client.get(reverse("blog:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_post.title)

    def test_public_post_is_visible_to_visitor(self):
        response = self.client.get(self.public_post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1 id="正文">正文</h1>', html=True)

    def test_private_post_is_hidden_from_visitor(self):
        response = self.client.get(self.private_post.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_draft_post_is_hidden_from_visitor(self):
        response = self.client.get(self.draft_post.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_list_does_not_leak_private_or_draft_posts(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertContains(response, self.public_post.title)
        self.assertNotContains(response, self.private_post.title)
        self.assertNotContains(response, self.draft_post.title)

    def test_category_page_only_shows_public_posts(self):
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_post.title)
        self.assertNotContains(response, self.private_post.title)
        self.assertNotContains(response, self.draft_post.title)

    def test_tag_page_only_shows_public_posts(self):
        response = self.client.get(self.tag.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_post.title)
        self.assertNotContains(response, self.private_post.title)
        self.assertNotContains(response, self.draft_post.title)

    def test_archive_only_shows_public_posts(self):
        response = self.client.get(reverse("blog:archive"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_post.title)
        self.assertNotContains(response, self.private_post.title)
        self.assertNotContains(response, self.draft_post.title)

    def test_staff_can_view_private_and_draft_posts(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.private_post.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(self.draft_post.get_absolute_url()).status_code, 200)

    @override_settings(DEBUG=False)
    def test_unknown_page_returns_custom_404(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_raw_html_in_markdown_is_not_rendered(self):
        self.public_post.content = '<script>alert("xss")</script>'
        self.public_post.save()
        response = self.client.get(self.public_post.get_absolute_url())
        self.assertNotContains(response, '<script>alert("xss")</script>')
        self.assertContains(response, "&lt;script&gt;")


class ModelTests(TestCase):
    def test_slug_and_published_time_are_created_automatically(self):
        post = Post.objects.create(
            title="第一篇文章",
            content="正文",
            status=Post.Status.PUBLISHED,
        )
        self.assertEqual(post.slug, "第一篇文章")
        self.assertIsNotNone(post.published_at)

    def test_reading_time_has_a_minimum_of_one_minute(self):
        post = Post(title="短文", content="很短的一段话。")
        self.assertEqual(post.reading_time, 1)


class DiscoveryAndReadingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="阅读", slug="reading")
        cls.tag = Tag.objects.create(name="记忆", slug="memory")
        now = timezone.now()
        cls.older_post = Post.objects.create(
            title="旧日记忆",
            slug="older-memory",
            summary="关于旧日时光",
            content="## 起点\n\n一段关于旧日的文字。\n\n## 回望\n\n继续记录。",
            category=cls.category,
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
            published_at=now - timedelta(days=2),
        )
        cls.older_post.tags.add(cls.tag)
        cls.current_post = Post.objects.create(
            title="被精选的文章",
            slug="featured-memory",
            summary="一篇首页精选文章",
            content="## 相遇\n\n正文。\n\n### 后来\n\n仍有回声。",
            category=cls.category,
            is_featured=True,
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
            published_at=now - timedelta(days=1),
        )
        cls.current_post.tags.add(cls.tag)
        cls.newer_post = Post.objects.create(
            title="新的记录",
            slug="newer-note",
            content="正文里写着独特关键词星河。",
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
            published_at=now,
        )
        cls.private_post = Post.objects.create(
            title="星河私密记录",
            slug="private-search-result",
            content="不应出现在公开搜索中。",
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PRIVATE,
            published_at=now,
        )

    def test_featured_post_is_presented_once_on_homepage(self):
        response = self.client.get(reverse("blog:home"))
        self.assertEqual(response.context["featured_posts"], [self.current_post])
        self.assertContains(response, self.current_post.title, count=1)
        self.assertNotContains(response, self.private_post.title)

    def test_search_matches_title_summary_and_content_without_leaking_private_posts(self):
        title_response = self.client.get(reverse("blog:search"), {"q": "精选"})
        summary_response = self.client.get(reverse("blog:search"), {"q": "旧日时光"})
        content_response = self.client.get(reverse("blog:search"), {"q": "星河"})
        self.assertContains(title_response, self.current_post.title)
        self.assertContains(summary_response, self.older_post.title)
        self.assertContains(content_response, self.newer_post.title)
        self.assertNotContains(content_response, self.private_post.title)

    def test_search_pagination_preserves_keyword(self):
        for number in range(11):
            Post.objects.create(
                title=f"分页词 {number}",
                slug=f"paged-{number}",
                content="正文",
                status=Post.Status.PUBLISHED,
                visibility=Post.Visibility.PUBLIC,
            )
        response = self.client.get(reverse("blog:search"), {"q": "分页词"})
        self.assertContains(response, "q=%E5%88%86%E9%A1%B5%E8%AF%8D")
        self.assertContains(response, "page=2")

    def test_detail_has_toc_neighbors_and_related_posts(self):
        response = self.client.get(self.current_post.get_absolute_url())
        self.assertEqual(response.context["previous_post"], self.older_post)
        self.assertEqual(response.context["next_post"], self.newer_post)
        self.assertIn(self.older_post, response.context["related_posts"])
        self.assertContains(response, 'href="#相遇"')
        self.assertContains(response, 'id="相遇"')

    def test_article_has_canonical_and_open_graph_metadata(self):
        response = self.client.get(self.current_post.get_absolute_url())
        canonical = f'content="http://testserver{self.current_post.get_absolute_url()}"'
        self.assertContains(response, canonical)
        self.assertContains(response, 'property="og:type" content="article"')


class SiteResourceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.public_post = Post.objects.create(
            title="订阅可见文章",
            slug="feed-visible",
            content="公开正文",
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
        )
        cls.private_post = Post.objects.create(
            title="订阅不可见文章",
            slug="feed-private",
            content="私密正文",
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PRIVATE,
        )

    def test_rss_contains_only_public_posts(self):
        response = self.client.get(reverse("blog:feed"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/rss+xml"))
        self.assertContains(response, self.public_post.title)
        self.assertNotContains(response, self.private_post.title)

    def test_sitemap_contains_only_public_post_urls(self):
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_post.get_absolute_url())
        self.assertNotContains(response, self.private_post.get_absolute_url())

    def test_robots_points_to_request_host_sitemap(self):
        response = self.client.get(reverse("blog:robots_txt"))
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")


class DashboardAndLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="editor",
            email="editor@example.com",
            password="strong-test-password",
        )
        cls.regular_user = get_user_model().objects.create_user(
            username="reader",
            password="reader-test-password",
        )
        cls.category = Category.objects.create(name="Notes", slug="notes")
        cls.tag = Tag.objects.create(name="Daily", slug="daily")
        cls.post = Post.objects.create(
            title="Editable post",
            slug="editable-post",
            content="Original content",
            status=Post.Status.DRAFT,
            visibility=Post.Visibility.PUBLIC,
        )

    def test_login_page_is_available(self):
        response = self.client.get(reverse("blog:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_staff_can_log_in_and_open_dashboard(self):
        response = self.client.post(
            reverse("blog:login"),
            {"username": "editor", "password": "strong-test-password"},
        )
        self.assertRedirects(response, reverse("blog:dashboard"))
        self.assertEqual(self.client.get(reverse("blog:dashboard")).status_code, 200)

    def test_regular_user_can_log_in_and_is_sent_home(self):
        response = self.client.post(
            reverse("blog:login"),
            {"username": "reader", "password": "reader-test-password"},
        )
        self.assertRedirects(response, reverse("blog:home"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertTrue(Profile.objects.filter(user=self.regular_user).exists())

    def test_regular_user_cannot_open_dashboard_or_admin(self):
        self.client.force_login(self.regular_user)
        dashboard_response = self.client.get(reverse("blog:dashboard"))
        create_response = self.client.get(reverse("blog:dashboard_post_create"))
        admin_response = self.client.get(reverse("admin:index"))
        self.assertEqual(dashboard_response.status_code, 302)
        self.assertEqual(create_response.status_code, 302)
        self.assertEqual(admin_response.status_code, 302)
        self.assertIn(reverse("blog:login"), dashboard_response.url)
        self.assertIn(reverse("admin:login"), admin_response.url)

    def test_visitor_cannot_open_dashboard_or_create_post(self):
        dashboard_response = self.client.get(reverse("blog:dashboard"))
        create_response = self.client.get(reverse("blog:dashboard_post_create"))
        self.assertEqual(dashboard_response.status_code, 302)
        self.assertEqual(create_response.status_code, 302)
        self.assertIn(reverse("blog:login"), dashboard_response.url)

    def test_staff_can_create_article(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("blog:dashboard_post_create"),
            {
                "title": "Created in dashboard",
                "slug": "",
                "summary": "A summary",
                "content": "# New article",
                "category": self.category.pk,
                "tags": [self.tag.pk],
                "status": Post.Status.DRAFT,
                "visibility": Post.Visibility.PUBLIC,
                "published_at": "",
            },
        )
        created = Post.objects.get(title="Created in dashboard")
        self.assertRedirects(response, created.get_absolute_url())
        self.assertEqual(created.status, Post.Status.DRAFT)
        self.assertEqual(list(created.tags.all()), [self.tag])

    def test_staff_can_update_article(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("blog:dashboard_post_update", args=[self.post.pk]),
            {
                "title": "Updated title",
                "slug": self.post.slug,
                "summary": "Updated summary",
                "content": "Updated content",
                "category": self.category.pk,
                "tags": [self.tag.pk],
                "status": Post.Status.PUBLISHED,
                "visibility": Post.Visibility.PRIVATE,
                "published_at": "",
            },
        )
        self.post.refresh_from_db()
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(self.post.title, "Updated title")
        self.assertEqual(self.post.status, Post.Status.PUBLISHED)
        self.assertEqual(self.post.visibility, Post.Visibility.PRIVATE)
        self.assertIsNotNone(self.post.published_at)

    def test_staff_can_publish_and_delete_article(self):
        self.client.force_login(self.admin)
        publish_response = self.client.post(
            reverse("blog:dashboard_post_status", args=[self.post.pk]),
            {"status": Post.Status.PUBLISHED},
        )
        self.assertRedirects(publish_response, reverse("blog:dashboard"))
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.Status.PUBLISHED)
        self.assertIsNotNone(self.post.published_at)

        delete_response = self.client.post(
            reverse("blog:dashboard_post_delete", args=[self.post.pk])
        )
        self.assertRedirects(delete_response, reverse("blog:dashboard"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class AccountTests(TestCase):
    password = "Rain-reader-2026!"

    def registration_data(self, **overrides):
        data = {
            "username": "NewReader",
            "display_name": "  一位读者  ",
            "password1": self.password,
            "password2": self.password,
        }
        data.update(overrides)
        return data

    def test_registration_creates_profile_hashes_password_and_logs_user_in(self):
        response = self.client.post(reverse("blog:register"), self.registration_data())
        user = get_user_model().objects.get(username="newreader")
        self.assertRedirects(response, reverse("blog:home"))
        self.assertEqual(user.profile.display_name, "一位读者")
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_rejects_weak_and_mismatched_passwords(self):
        weak_response = self.client.post(
            reverse("blog:register"),
            self.registration_data(username="weak-user", password1="123", password2="123"),
        )
        mismatch_response = self.client.post(
            reverse("blog:register"),
            self.registration_data(
                username="mismatch-user",
                password1=self.password,
                password2="Different-reader-2026!",
            ),
        )
        self.assertEqual(weak_response.status_code, 200)
        self.assertEqual(mismatch_response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username="weak-user").exists())
        self.assertFalse(
            get_user_model().objects.filter(username="mismatch-user").exists()
        )

    def test_registration_rejects_duplicate_username_ignoring_case(self):
        get_user_model().objects.create_user(username="Rain", password=self.password)
        response = self.client.post(
            reverse("blog:register"),
            self.registration_data(username="rAiN"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "这个账号已经被使用")
        self.assertEqual(get_user_model().objects.filter(username__iexact="rain").count(), 1)

    def test_login_failure_uses_one_generic_message(self):
        response = self.client.post(
            reverse("blog:login"),
            {"username": "missing-reader", "password": "Wrong-reader-2026!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "账号或密码不正确")
        self.assertNotContains(response, "账号不存在")

    def test_registration_and_login_respect_only_safe_next_urls(self):
        profile_url = reverse("blog:profile")
        register_response = self.client.post(
            reverse("blog:register"),
            self.registration_data(username="next-reader", next=profile_url),
        )
        self.assertRedirects(register_response, profile_url)
        self.client.post(reverse("blog:logout"))

        login_response = self.client.post(
            reverse("blog:login"),
            {
                "username": "NEXT-READER",
                "password": self.password,
                "next": profile_url,
            },
        )
        self.assertRedirects(login_response, profile_url)
        self.client.post(reverse("blog:logout"))

        external_response = self.client.post(
            reverse("blog:login"),
            {
                "username": "next-reader",
                "password": self.password,
                "next": "https://attacker.example/escape",
            },
        )
        self.assertRedirects(external_response, reverse("blog:home"))

    def test_profile_can_change_nickname_and_password(self):
        user = get_user_model().objects.create_user(
            username="settings-reader", password=self.password
        )
        self.client.force_login(user)
        profile_response = self.client.post(
            reverse("blog:profile"), {"display_name": "  新名字  "}
        )
        self.assertRedirects(profile_response, reverse("blog:profile"))
        self.assertEqual(user.profile.display_name, "新名字")

        new_password = "Changed-reader-2026!"
        password_response = self.client.post(
            reverse("blog:password_change"),
            {
                "old_password": self.password,
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )
        self.assertRedirects(password_response, reverse("blog:profile"))
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_authenticated_register_redirects(self):
        user = get_user_model().objects.create_user(
            username="signed-in-reader", password=self.password
        )
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("blog:register")), reverse("blog:home"))
        self.assertEqual(self.client.get(reverse("blog:logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("blog:logout")), reverse("blog:home"))
        self.assertNotIn("_auth_user_id", self.client.session)


class CommentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="comment-admin",
            email="admin@example.com",
            password="strong-test-password",
        )
        cls.reader = get_user_model().objects.create_user(
            username="comment-reader",
            password="comment-reader-password",
        )
        Profile.objects.create(user=cls.reader, display_name="安静读者")
        cls.public_post = Post.objects.create(
            title="Public comments",
            slug="public-comments",
            content="Public content",
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
        )
        cls.private_post = Post.objects.create(
            title="Private comments",
            slug="private-comments",
            content="Private content",
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PRIVATE,
        )
        cls.draft_post = Post.objects.create(
            title="Draft comments",
            slug="draft-comments",
            content="Draft content",
            status=Post.Status.DRAFT,
            visibility=Post.Visibility.PUBLIC,
        )
        cls.future_post = Post.objects.create(
            title="Future comments",
            slug="future-comments",
            content="Future content",
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
            published_at=timezone.now() + timedelta(days=1),
        )

    def comment_data(self, content="A thoughtful comment"):
        return {
            "content": content,
            "website": "",
        }

    def test_anonymous_visitor_cannot_submit_comment(self):
        response = self.client.post(
            reverse("blog:add_comment", args=[self.public_post.slug]),
            self.comment_data(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("blog:login")))
        self.assertIn("%23comments", response.url)
        self.assertEqual(Comment.objects.count(), 0)
        detail = self.client.get(self.public_post.get_absolute_url())
        self.assertContains(detail, "登录后评论")
        self.assertNotContains(detail, "提交评论")

    def test_logged_in_user_comment_is_immediately_public(self):
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse("blog:add_comment", args=[self.public_post.slug]),
            self.comment_data(),
        )
        self.assertRedirects(response, f"{self.public_post.get_absolute_url()}#comments")
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.reader)
        self.assertEqual(comment.name, "安静读者")
        self.assertEqual(comment.email, "")
        self.assertEqual(comment.status, Comment.Status.APPROVED)
        detail = self.client.get(self.public_post.get_absolute_url())
        self.assertContains(detail, comment.content)

    def test_client_cannot_forge_comment_identity_or_status(self):
        other = get_user_model().objects.create_user(
            username="other-reader", password="other-reader-password"
        )
        self.client.force_login(self.reader)
        forged = self.comment_data("Identity stays trustworthy")
        forged.update(
            {
                "name": "Forged name",
                "email": "forged@example.com",
                "author": other.pk,
                "status": Comment.Status.REJECTED,
            }
        )
        self.client.post(
            reverse("blog:add_comment", args=[self.public_post.slug]), forged
        )
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.reader)
        self.assertEqual(comment.name, "安静读者")
        self.assertEqual(comment.email, "")
        self.assertEqual(comment.status, Comment.Status.APPROVED)

    def test_nickname_change_does_not_rewrite_historical_comment(self):
        self.client.force_login(self.reader)
        self.client.post(
            reverse("blog:add_comment", args=[self.public_post.slug]),
            self.comment_data("Keep the old name"),
        )
        profile = self.reader.profile
        profile.display_name = "后来改名"
        profile.save()
        self.assertEqual(Comment.objects.get().name, "安静读者")

    def test_approved_comment_is_visible_but_email_is_private(self):
        comment = Comment.objects.create(
            post=self.public_post,
            name="Visible visitor",
            email="private-email@example.com",
            content="This comment is approved.",
            status=Comment.Status.APPROVED,
        )
        response = self.client.get(self.public_post.get_absolute_url())
        self.assertContains(response, comment.name)
        self.assertContains(response, comment.content)
        self.assertNotContains(response, comment.email)

    def test_comment_html_is_escaped(self):
        self.client.force_login(self.reader)
        self.client.post(
            reverse("blog:add_comment", args=[self.public_post.slug]),
            self.comment_data("<script>alert('comment')</script>"),
        )
        response = self.client.get(self.public_post.get_absolute_url())
        self.assertNotContains(response, "<script>alert('comment')</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_comments_cannot_be_submitted_to_private_draft_or_future_posts(self):
        self.client.force_login(self.reader)
        private_response = self.client.post(
            reverse("blog:add_comment", args=[self.private_post.slug]),
            self.comment_data(),
        )
        draft_response = self.client.post(
            reverse("blog:add_comment", args=[self.draft_post.slug]),
            self.comment_data(),
        )
        future_response = self.client.post(
            reverse("blog:add_comment", args=[self.future_post.slug]),
            self.comment_data(),
        )
        self.assertEqual(private_response.status_code, 404)
        self.assertEqual(draft_response.status_code, 404)
        self.assertEqual(future_response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 0)

    def test_honeypot_discards_bot_comment(self):
        self.client.force_login(self.reader)
        data = self.comment_data()
        data["website"] = "https://spam.example"
        response = self.client.post(
            reverse("blog:add_comment", args=[self.public_post.slug]), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_submission_has_session_cooldown(self):
        self.client.force_login(self.reader)
        url = reverse("blog:add_comment", args=[self.public_post.slug])
        self.client.post(url, self.comment_data("First comment"))
        response = self.client.post(url, self.comment_data("Second comment"))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "请稍等片刻", status_code=400)
        self.assertEqual(Comment.objects.count(), 1)

    def test_staff_can_approve_and_delete_comment(self):
        comment = Comment.objects.create(
            post=self.public_post,
            name="Pending visitor",
            email="pending@example.com",
            content="Waiting for review",
        )
        self.client.force_login(self.admin)
        approve_response = self.client.post(
            reverse("blog:comment_change_status", args=[comment.pk]),
            {"status": Comment.Status.APPROVED},
        )
        self.assertRedirects(approve_response, reverse("blog:comment_moderation"))
        comment.refresh_from_db()
        self.assertEqual(comment.status, Comment.Status.APPROVED)

        delete_response = self.client.post(reverse("blog:comment_delete", args=[comment.pk]))
        self.assertRedirects(delete_response, reverse("blog:comment_moderation"))
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
