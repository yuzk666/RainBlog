from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from .accounts import account_with_same_name
from .models import Comment, Post, Profile


class AccountAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "账号或密码不正确，请重新输入。",
        "inactive": "账号或密码不正确，请重新输入。",
    }
    username = forms.CharField(
        label="账号",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="密码",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        existing = account_with_same_name(username)
        return existing.get_username() if existing else username


class RegistrationForm(UserCreationForm):
    display_name = forms.CharField(
        label="昵称",
        min_length=2,
        max_length=40,
        widget=forms.TextInput(
            attrs={"autocomplete": "nickname", "placeholder": "公开显示的名字"}
        ),
        help_text="会显示在你发表的评论旁，可以和别人重名。",
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username", "display_name", "password1", "password2")
        widgets = {
            "username": forms.TextInput(
                attrs={"autocomplete": "username", "placeholder": "用于登录的唯一账号"}
            )
        }
        help_texts = {
            "username": "只用于登录，不会代替你的公开昵称。",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "账号"
        self.fields["password1"].label = "密码"
        self.fields["password2"].label = "确认密码"

    def clean_username(self):
        username = self.cleaned_data["username"].strip().casefold()
        if account_with_same_name(username):
            raise forms.ValidationError("这个账号已经被使用，请换一个。")
        return username

    def clean_display_name(self):
        return self.cleaned_data["display_name"].strip()

    def save(self, commit=True):
        user = super().save(commit=False)
        if not commit:
            return user
        with transaction.atomic():
            user.save()
            Profile.objects.create(
                user=user,
                display_name=self.cleaned_data["display_name"],
            )
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name",)
        widgets = {
            "display_name": forms.TextInput(
                attrs={"autocomplete": "nickname", "placeholder": "公开显示的名字"}
            )
        }
        help_texts = {
            "display_name": "修改后用于新的评论；已经发表的评论会保留原来的名字。",
        }

    def clean_display_name(self):
        return self.cleaned_data["display_name"].strip()


class PostForm(forms.ModelForm):
    published_at = forms.DateTimeField(
        label="发布时间",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
        help_text="留空时，文章首次发布会自动填写当前时间；也可以设置未来时间。",
    )

    class Meta:
        model = Post
        fields = (
            "title",
            "slug",
            "summary",
            "content",
            "cover",
            "category",
            "tags",
            "is_featured",
            "status",
            "visibility",
            "published_at",
        )
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "文章标题"}),
            "slug": forms.TextInput(attrs={"placeholder": "留空则根据标题自动生成"}),
            "summary": forms.Textarea(
                attrs={"rows": 3, "placeholder": "用一两句话概括文章（可选）"}
            ),
            "content": forms.Textarea(
                attrs={"rows": 24, "placeholder": "使用 Markdown 写作……", "spellcheck": "true"}
            ),
            "tags": forms.SelectMultiple(attrs={"size": 7}),
        }
        help_texts = {
            "slug": "用于文章网址，可填写英文、数字、连字符或中文。留空会自动生成。",
            "content": "支持标题、列表、引用、链接、图片和代码块；原始 HTML 不会执行。",
            "cover": "可选。支持 Pillow 能识别的常见图片格式。",
            "tags": "按住 Ctrl（macOS 为 Command）可多选。",
        }


class CommentForm(forms.ModelForm):
    # 保留隐藏蜜罐；它不会向登录用户展示，也不接受任何身份字段。
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")

    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 5, "placeholder": "写下你的想法……", "maxlength": 2000}
            ),
        }

    def clean_content(self):
        return self.cleaned_data["content"].strip()
