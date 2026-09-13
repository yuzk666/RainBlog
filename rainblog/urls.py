from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

from blog.sitemaps import PostSitemap, StaticViewSitemap


admin.site.site_header = "RainBlog 管理"
admin.site.site_title = "RainBlog"
admin.site.index_title = "内容管理"

sitemaps = {
    "posts": PostSitemap,
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=static_url("favicon.svg"), permanent=True),
        name="favicon",
    ),
    path("", include("blog.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "blog.views.custom_404"
handler500 = "blog.views.custom_500"
