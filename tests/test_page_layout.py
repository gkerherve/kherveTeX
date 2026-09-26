"""The on-screen page mirrors the PDF's geometry: margins, line spacing,
paragraph indentation and a body font close to the LaTeX one."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc.editor import (  # noqa: E402
    DocumentEditor, _PX_PER_CM, screen_font_for,
)
from khervedoc.model import (  # noqa: E402
    DocMeta, Document, Paragraph, Section, Text,
)


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


def _editor(meta: DocMeta) -> DocumentEditor:
    ed = DocumentEditor()
    ed.set_fit_to_width(False)
    ed.set_document(Document(meta=meta, children=[
        Section(level=1, children=[Text("Intro")]),
        Paragraph(children=[Text("First paragraph.")]),
        Paragraph(children=[Text("Second paragraph.")]),
    ]))
    return ed


def _blocks(ed):
    b = ed._edit.document().firstBlock()
    out = []
    while b.isValid():
        out.append(b)
        b = b.next()
    return out


def test_margins_follow_document_settings(qapp):
    meta = DocMeta(margin_left_cm=4.0, margin_top_cm=1.0)
    ed = _editor(meta)
    ff = ed._edit.document().rootFrame().frameFormat()
    z = ed.zoom_percent() / 100
    assert ff.leftMargin() == pytest.approx(4.0 * _PX_PER_CM * z)
    assert ff.topMargin() == pytest.approx(1.0 * _PX_PER_CM * z)


def test_indent_skips_first_paragraph_after_heading(qapp):
    ed = _editor(DocMeta(paragraph_indent=True))
    _, first, second = _blocks(ed)
    assert first.blockFormat().textIndent() == 0
    assert second.blockFormat().textIndent() > 0


def test_no_indent_mode_uses_paragraph_spacing(qapp):
    ed = _editor(DocMeta(paragraph_indent=False))
    _, first, second = _blocks(ed)
    assert second.blockFormat().textIndent() == 0
    assert second.blockFormat().bottomMargin() > 0


def test_line_spacing_applied(qapp):
    ed = _editor(DocMeta(line_spacing=2.0))
    assert _blocks(ed)[1].blockFormat().lineHeight() == pytest.approx(200)


def test_explicit_visual_font_is_respected(qapp):
    assert screen_font_for(DocMeta(visual_font_family="Arial")) == "Arial"


def test_default_visual_font_tracks_latex_font(qapp):
    from PySide6.QtGui import QFontDatabase
    installed = set(QFontDatabase.families())
    got = screen_font_for(DocMeta(body_font_family="times"))
    if {"Times New Roman", "Times"} & installed:
        assert got in {"Times New Roman", "Times"}
    else:
        assert got == "Georgia"
