from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt


register = template.Library()

# 禁用 Markdown 中的原始 HTML；输出只包含解析器生成的安全标签。
markdown_renderer = MarkdownIt(
    "commonmark",
    {"html": False, "linkify": False, "typographer": False},
)


@register.filter(name="markdown")
def render_markdown(value):
    return mark_safe(markdown_renderer.render(value or ""))
