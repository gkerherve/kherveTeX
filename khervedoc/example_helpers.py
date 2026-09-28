"""Compact constructors shared by the example document modules."""
from __future__ import annotations

from .model import DocMeta, List as ListNode, ListItem, Paragraph, Text


def _meta(**overrides) -> DocMeta:
    """Build a DocMeta with the KherveTeX defaults and let callers tweak
    a few fields. Avoids each example repeating the same boilerplate."""
    base = DocMeta(
        title="", author="",
        body_font_pt=11,
        line_spacing=1.15,
        paragraph_indent=False,
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def _p(*runs) -> Paragraph:
    """Compact constructor: _p('hello ', ('world', ['bold']), '.')"""
    children: list = []
    for r in runs:
        if isinstance(r, str):
            children.append(Text(text=r))
        elif isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], str):
            children.append(Text(text=r[0], marks=list(r[1])))
        else:
            children.append(r)
    return Paragraph(children=children)


def _items(*labels) -> ListNode:
    return ListNode(ordered=False, items=[
        ListItem(children=[Text(text=s)]) for s in labels])


def _ord_items(*labels) -> ListNode:
    return ListNode(ordered=True, items=[
        ListItem(children=[Text(text=s)]) for s in labels])
