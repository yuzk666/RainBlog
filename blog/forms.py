from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Comment, Post


class StaffAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="密码",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


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
    # 隐藏蜜罐字段：正常访客不会填写，简单机器人通常会自动填写。
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")

    class Meta:
        model = Comment
        fields = ("name", "email", "content")
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "怎么称呼你", "autocomplete": "name", "maxlength": 80}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "仅用于管理，不会公开", "autocomplete": "email"}
            ),
            "content": forms.Textarea(
                attrs={"rows": 5, "placeholder": "写下你的想法……", "maxlength": 2000}
            ),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_content(self):
        return self.cleaned_data["content"].strip()
