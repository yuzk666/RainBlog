from __future__ import annotations

from dataclasses import dataclass

from django.utils.safestring import SafeString, mark_safe
from django.utils.text import slugify
from markdown_it import MarkdownIt


# 原始 HTML 保持禁用；页面只信任解析器生成的标签。
markdown_renderer = MarkdownIt(
    "commonmark",
    {"html": False, "linkify": False, "typographer": False},
)


@dataclass(frozen=True)
class TocItem:
    level: int
    title: str
    anchor: str


def render_markdown_document(value: str) -> tuple[SafeString, list[TocItem]]:
    """渲染 Markdown，并为一至三级标题生成稳定且唯一的页内锚点。"""
    tokens = markdown_renderer.parse(value or "")
    toc: list[TocItem] = []
    anchors: dict[str, int] = {}

    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.tag not in {"h1", "h2", "h3"}:
            continue
        if index + 1 >= len(tokens) or tokens[index + 1].type != "inline":
            continue

        title = tokens[index + 1].content.strip()
        base = slugify(title, allow_unicode=True) or "section"
        anchors[base] = anchors.get(base, 0) + 1
        anchor = base if anchors[base] == 1 else f"{base}-{anchors[base]}"
        token.attrSet("id", anchor)
        toc.append(TocItem(level=int(token.tag[1]), title=title, anchor=anchor))

    rendered = markdown_renderer.renderer.render(tokens, markdown_renderer.options, {})
    return mark_safe(rendered), toc
