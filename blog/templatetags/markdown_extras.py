from django import template

from blog.markdown import render_markdown_document


register = template.Library()

@register.filter(name="markdown")
def render_markdown(value):
    rendered, _ = render_markdown_document(value or "")
    return rendered
