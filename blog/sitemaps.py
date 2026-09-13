from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Post


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return ("blog:home", "blog:post_list", "blog:archive", "blog:about")

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Post.objects.public().only("slug", "updated_at")

    def lastmod(self, item):
        return item.updated_at
