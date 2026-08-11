from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "RainBlog 管理"
admin.site.site_title = "RainBlog"
admin.site.index_title = "内容管理"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("blog.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "blog.views.custom_404"
handler500 = "blog.views.custom_500"
