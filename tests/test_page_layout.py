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
    from khervedoc.latex_fonts import baselineskip_pt
    ed = _editor(DocMeta(line_spacing=2.0))
    z = ed.zoom_percent() / 100
    fmt = _blocks(ed)[1].blockFormat()
    assert fmt.lineHeightType() == 2      # FixedHeight
    assert fmt.lineHeight() == pytest.approx(
        baselineskip_pt(12, 2.0) * 96 / 72 * z)
    assert baselineskip_pt(12, 1.0) == pytest.approx(14.5)
    assert baselineskip_pt(12, 2.0) == pytest.approx(14.5 * 1.655)


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


def test_citations_display_resolved_but_roundtrip_keys(qapp):
    from khervedoc.model import Citation, CrossRef
    ed = DocumentEditor()
    doc = Document(children=[
        Section(level=1, label="sec:intro", children=[Text("Intro")]),
        Paragraph(children=[Text("See "), Citation(keys=["k1"]),
                            Text(" and "), CrossRef(label="sec:intro")]),
    ])
    ed.set_document(doc)
    text = ed._edit.toPlainText()
    assert "[1]" in text and "k1" not in text
    para = ed.get_document().children[1]
    assert any(isinstance(c, Citation) and c.keys == ["k1"]
               for c in para.children)
    assert any(isinstance(c, CrossRef) and c.label == "sec:intro"
               for c in para.children)


def test_headings_scale_like_latex_and_are_numbered(qapp):
    from khervedoc.editor import _P_HEADING_NUMBER
    ed = DocumentEditor()
    ed.set_fit_to_width(False)
    ed.set_document(Document(children=[
        Section(level=1, children=[Text("A")]),
        Section(level=2, children=[Text("A1")]),
        Section(level=1, numbered=False, children=[Text("Star")]),
        Section(level=1, children=[Text("B")]),
    ]))
    blocks = _blocks(ed)
    z = ed.zoom_percent() / 100
    size = blocks[0].begin().fragment().charFormat().font().pointSizeF()
    assert size == pytest.approx(12 * 17.28 / 12 * z)
    numbers = [b.blockFormat().property(_P_HEADING_NUMBER) for b in blocks]
    assert numbers == ["1", "1.1", None, "2"]
    assert blocks[0].blockFormat().textIndent() > 0


def test_bold_first_word_stays_a_paragraph(qapp):
    ed = _editor(DocMeta())
    ed.set_document(Document(children=[Paragraph(children=[
        Text("Note:", marks=["bold"]), Text(" plain")])]))
    assert isinstance(ed.get_document().children[0], Paragraph)


def test_table_cells_keep_their_latex_through_the_editor(qapp):
    from khervedoc.model import Table
    ed = DocumentEditor()
    t = Table(rows=[["\\textbf{Area}", "$x^2$"], ["1", "2"]],
              caption="Peaks", alignment="l|c", style="booktabs")
    ed.set_document(Document(children=[t]))
    back = next(b for b in ed.get_document().children
                if isinstance(b, Table))
    assert back.rows == t.rows
    assert back.style == "booktabs" and back.alignment == "l|c"
    assert back.caption == "Peaks"
    assert "Table 1: Peaks" in ed._edit.toPlainText()


def test_document_is_laid_out_on_whole_pages(qapp):
    ed = DocumentEditor()
    ed.resize(1000, 800)
    ed.set_document(Document(children=[Paragraph(children=[Text("x")])]))
    edit = ed._edit
    page_h = edit.page_height_px()
    assert edit.document().pageCount() == 1
    assert ed._page.maximumHeight() == page_h    # a full, empty sheet
    long = [Paragraph(children=[Text("word " * 120)]) for _ in range(40)]
    ed.set_document(Document(children=long))
    edit.resize(edit.width(), edit.height() + 1)  # a relayout must not
    pages = edit.document().pageCount()           # switch paging off
    assert pages > 1
    assert edit.document().pageSize().height() == page_h
    assert ed._page.maximumHeight() == page_h * pages


def test_sheets_start_where_the_pdf_pages_start(qapp):
    ed = DocumentEditor()
    ed.resize(1000, 800)
    long = "word " * 60
    ed.set_document(Document(children=[
        Section(level=1, children=[Text("Intro")]),
        Paragraph(children=[Text("Lists are mentioned here. " + long)]),
        Section(level=1, children=[Text("Lists")]),
        Paragraph(children=[Text(long)]),
    ]))
    edit = ed._edit
    # The PDF put the "Lists" heading at the top of page 2; the earlier
    # paragraph that merely mentions the word must not take the break.
    edit.set_page_anchors([(2, "Lists")])
    ed.sync_pages_to_pdf()
    heading = edit.document().findBlockByNumber(2)
    from PySide6.QtGui import QTextFormat
    assert heading.blockFormat().pageBreakPolicy() & \
        QTextFormat.PageBreak_AlwaysBefore
    assert edit.document().pageCount() == 2
    assert edit._sheet_labels(2) == ["1", "2"]


def test_first_text_snippet_drops_section_numbers():
    from khervedoc.mainwindow import _first_text_snippet

    class _Page:
        def get_text(self, kind):
            return "2.2\nLists\nBulleted and numbered\n3\n"
    assert _first_text_snippet(_Page()) == "Lists"

    class _Page2:
        def get_text(self, kind):
            return "A guided tour of the editor\n"
    assert _first_text_snippet(_Page2()).startswith("A guided")
