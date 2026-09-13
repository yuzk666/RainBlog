from django.contrib.auth import get_user_model

from .models import Profile


def account_with_same_name(username: str):
    return get_user_model().objects.filter(username__iexact=username.strip()).first()


def fallback_display_name(user) -> str:
    """为迁移前的用户提供稳定、可公开显示的名称。"""
    full_name = user.get_full_name().strip()
    return (full_name or user.get_username() or "读者")[:40]


def get_or_create_profile(user) -> Profile:
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"display_name": fallback_display_name(user)},
    )
    return profile


def display_name_for(user) -> str:
    if not getattr(user, "is_authenticated", False):
        return ""
    try:
        return user.profile.display_name
    except Profile.DoesNotExist:
        return fallback_display_name(user)


def account_with_same_name(username: str, *, exclude_pk=None):
    queryset = get_user_model().objects.filter(username__iexact=username)
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    return queryset.first()
