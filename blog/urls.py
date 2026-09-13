from django.urls import path

from . import views
from .feeds import LatestPostsFeed


app_name = "blog"

urlpatterns = [
    path("", views.home, name="home"),
    path("articles/", views.post_list, name="post_list"),
    path("search/", views.search, name="search"),
    path("feed/", LatestPostsFeed(), name="feed"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("articles/<str:slug>/comments/", views.add_comment, name="add_comment"),
    path("articles/<str:slug>/", views.post_detail, name="post_detail"),
    path("category/<str:slug>/", views.category_posts, name="category"),
    path("tag/<str:slug>/", views.tag_posts, name="tag"),
    path("archive/", views.archive, name="archive"),
    path("about/", views.about, name="about"),
    path("register/", views.register, name="register"),
    path("login/", views.AccountLoginView.as_view(), name="login"),
    path("profile/", views.profile, name="profile"),
    path(
        "password/change/",
        views.AccountPasswordChangeView.as_view(),
        name="password_change",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/posts/new/", views.dashboard_post_create, name="dashboard_post_create"),
    path(
        "dashboard/posts/<int:pk>/edit/",
        views.dashboard_post_update,
        name="dashboard_post_update",
    ),
    path(
        "dashboard/posts/<int:pk>/delete/",
        views.dashboard_post_delete,
        name="dashboard_post_delete",
    ),
    path(
        "dashboard/posts/<int:pk>/status/",
        views.dashboard_post_status,
        name="dashboard_post_status",
    ),
    path("dashboard/comments/", views.comment_moderation, name="comment_moderation"),
    path(
        "dashboard/comments/<int:pk>/status/",
        views.comment_change_status,
        name="comment_change_status",
    ),
    path(
        "dashboard/comments/<int:pk>/delete/",
        views.comment_delete,
        name="comment_delete",
    ),
]
