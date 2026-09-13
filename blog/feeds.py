from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import Post


class LatestPostsFeed(Feed):
    title = "Rainzk"
    description = "Rainzk 的最近文章：生活、思考和偶尔冒出来的想法。"
    link = "/"

    def items(self):
        return Post.objects.public().select_related("category")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.seo_description

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def get_feed_url(self, obj):
        return reverse("blog:feed")
