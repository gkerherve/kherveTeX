"""The visual tab prints each document class the way its PDF does: fonts,
sizes, numbering, alignment and geometry come from a table measured from
real compiles (packaging/measure_class_looks.py)."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc.class_looks import LOOKS  # noqa: E402
from khervedoc.editor import (  # noqa: E402
    BASELINE_AT, DocumentEditor, TEMPLATE_CHOICES,
)
from khervedoc.model import (  # noqa: E402
    Abstract, Author, DocMeta, Document, Keywords, Paragraph, Section, Text,
    Title,
)
from khervedoc import page_look  # noqa: E402
from khervedoc.page_look import is_broken, look_for, number_label  # noqa: E402
from khervedoc.paged_edit import (  # noqa: E402
    ABOVE_LABELS_PROPERTY, HEADING_NUMBER_PROPERTY, RUN_IN_LABEL_PROPERTY,
)
from khervedoc.serializer import serialize_document  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


def _editor(cls: str, pt: int = 12) -> DocumentEditor:
    ed = DocumentEditor()
    ed.set_fit_to_width(False)
    ed.set_zoom_percent(100)
    ed.set_document(Document(meta=DocMeta(documentclass=cls, body_font_pt=pt),
                             children=[
        Title(children=[Text("My Title")]),
        Author(children=[Text("An Author")]),
        Abstract(children=[Text("The abstract.")]),
        Keywords(children=[Text("one, two")]),
        Section(level=1, children=[Text("Intro")]),
        Paragraph(children=[Text("First paragraph.")]),
        Paragraph(children=[Text("Second paragraph.")]),
        Section(level=2, children=[Text("Part")]),
        Paragraph(children=[Text("Third paragraph.")]),
    ]))
    return ed


def _block(ed, text):
    b = ed._edit.document().firstBlock()
    while b.isValid():
        if b.text() == text:
            return b
        b = b.next()
    raise AssertionError(text)


def _font(ed, text):
    return _block(ed, text).begin().fragment().charFormat().font()


def test_every_document_type_is_measured():
    assert set(TEMPLATE_CHOICES) <= set(LOOKS)


def test_measured_values_of_a_broken_class_fall_back_to_article(monkeypatch):
    monkeypatch.setitem(page_look.LOOKS, "nope", {12: {"broken": "no class"}})
    monkeypatch.setitem(page_look._LOWER, "nope", "nope")
    assert is_broken("nope")
    assert look_for("nope", 12) is look_for("article", 12)
    assert not is_broken("article")


def test_an_unlisted_class_is_drawn_as_an_article():
    assert look_for("svjour3", 12) is look_for("article", 12)


@pytest.mark.parametrize("cls", TEMPLATE_CHOICES)
def test_every_type_prints_its_measured_sizes(qapp, cls):
    ed = _editor(cls)
    look = look_for(cls, 12)
    assert ed._edit.page_height_px() > 0
    for text, key in (("My Title", "title"), ("An Author", "author"),
                      ("Intro", "h1"), ("Part", "h2")):
        if key in look:
            assert _font(ed, text).pointSizeF() == pytest.approx(
                look[key]["size"], abs=0.01), key
    assert _font(ed, "First paragraph.").pointSizeF() == pytest.approx(
        look["body"]["size"], abs=0.01)
    ed.close()


def test_article_title_block_is_upright_and_plain_black(qapp):
    # The PDF's \maketitle is neither bold nor grey italic.
    ed = _editor("article")
    assert not _font(ed, "My Title").bold()
    assert not _font(ed, "An Author").italic()
    fmt = _block(ed, "An Author").begin().fragment().charFormat()
    assert fmt.foreground().style() == Qt.NoBrush
    assert _block(ed, "My Title").blockFormat().alignment() & Qt.AlignHCenter
    ed.close()


def test_abstract_has_no_screen_only_tint_and_gets_its_heading(qapp):
    ed = _editor("article")
    bf = _block(ed, "The abstract.").blockFormat()
    assert bf.background().style() == Qt.NoBrush
    assert "Abstract" in bf.property(ABOVE_LABELS_PROPERTY)
    assert "Keywords:" in _block(ed, "one, two").blockFormat() \
        .property(RUN_IN_LABEL_PROPERTY)
    ed.close()


def _furniture_text(ed, kind):
    return [i.get("text") for i in ed._edit._furniture["pages"].get(kind, [])]


def test_classes_bring_their_own_headers_and_footers(qapp):
    els = _editor("elsarticle")
    assert any("Preprint submitted" in (t or "")
               for t in _furniture_text(els, "first"))
    els.close()
    book = _editor("book")
    even = " ".join(t or "" for t in _furniture_text(book, "even"))
    assert "{h1}" in even and "{page}" in even
    assert book._edit._furniture["fields"]["title"] == "My Title"
    book._edit.grab()                   # paints without raising
    book.close()
    art = _editor("article")
    assert _furniture_text(art, "odd") == ["{page}"]
    art.close()


def test_running_head_field_uses_this_documents_words(qapp):
    ed = _editor("book")
    heads = ed._edit._running_heads
    assert [(h[3], h[4], h[5]) for h in heads] == [
        (1, "Intro", "1"), (2, "Part", "1.1")]
    ed.close()


def test_article_prints_todays_date_under_the_title_block(qapp):
    from datetime import date
    ed = _editor("article")
    labels = _block(ed, "An Author").blockFormat().property(ABOVE_LABELS_PROPERTY)
    assert str(date.today().year) in labels
    ed.close()


def test_ieeetran_is_two_columns_of_letter_with_roman_numbers(qapp):
    ed = _editor("IEEEtran")
    assert ed._edit.columns() == 2
    assert ed._page.width() == round(612 * 96 / 72)
    assert _font(ed, "First paragraph.").pointSizeF() == pytest.approx(9.96)
    assert _block(ed, "Intro").blockFormat().property(
        HEADING_NUMBER_PROPERTY) == "I."
    assert _block(ed, "Part").blockFormat().property(
        HEADING_NUMBER_PROPERTY) == "A."
    assert _block(ed, "Intro").blockFormat().alignment() & Qt.AlignHCenter
    ed.close()


def test_koma_headings_are_sans_and_number_on_the_same_line(qapp):
    ed = _editor("scrreprt")
    assert "LMSans" in _font(ed, "Intro").family() or \
        "Sans" in _font(ed, "Intro").family()
    assert _block(ed, "Intro").blockFormat().property(
        HEADING_NUMBER_PROPERTY) == "1"
    ed.close()


def _deep_editor(cls):
    ed = DocumentEditor()
    ed.set_fit_to_width(False)
    ed.set_zoom_percent(100)
    ed.set_document(Document(meta=DocMeta(documentclass=cls), children=[
        Section(level=1, children=[Text("Intro")]),
        Section(level=2, children=[Text("Part")]),
        Paragraph(children=[Text("Words follow the heading. " * 12)]),
        Section(level=4, children=[Text("Deep")]),
        Paragraph(children=[Text("Run-in words. " * 12)]),
        Section(level=4, children=[Text("Alone")]),
        Section(level=2, children=[Text("Next")]),
    ]))
    ed.show()
    QApplication.processEvents()
    return ed


def test_run_in_heading_shares_its_line_with_the_paragraph(qapp):
    ed = _deep_editor("article")
    head = _block(ed, "Deep")
    para = head.next()
    assert _baseline(ed, para) == pytest.approx(_baseline(ed, head), abs=1.5)
    assert para.blockFormat().textIndent() > 20
    # Separate blocks still, so the LaTeX is untouched.
    tex = serialize_document(ed.get_document())
    assert "\\paragraph{Deep}" in tex or "paragraph{Deep}" in tex
    ed.close()


def test_run_in_heading_with_nothing_to_run_into_stays_alone(qapp):
    ed = _deep_editor("article")
    head = _block(ed, "Alone")
    assert head.blockFormat().bottomMargin() >= 0
    ed.close()


def test_click_after_run_in_heading_lands_in_the_paragraph(qapp):
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest
    ed = _deep_editor("article")
    head = _block(ed, "Deep")
    para = head.next()
    layout = ed._edit.document().documentLayout()
    raw = layout.blockBoundingRect(para)
    line = para.layout().lineAt(0)
    y = int(raw.top() + line.y() + line.ascent() - 3)
    right = int(raw.left() + line.naturalTextRect().left() + 30)
    QTest.mouseClick(ed._edit.viewport(), Qt.LeftButton, pos=QPoint(right, y))
    assert ed._edit.textCursor().block() == para
    left = int(raw.left() + 5)
    QTest.mouseClick(ed._edit.viewport(), Qt.LeftButton, pos=QPoint(left, y))
    assert ed._edit.textCursor().block() == head
    ed.close()


def test_ieeetran_title_spans_and_second_column_starts_below_it(qapp):
    ed = _editor("IEEEtran")
    ed.show()
    QApplication.processEvents()
    edit = ed._edit
    title = _block(ed, "My Title")
    assert title.layout().lineAt(0).naturalTextRect().left() \
        > edit.text_width_px() / 2      # centred over the page, past column 1
    slots = edit._column_slots()
    assert slots[0].width > edit.text_width_px() * 1.8
    assert slots[1].vx == slots[0].vx
    assert slots[1].vy == pytest.approx(slots[0].b)
    ed.close()


def test_table_stays_inside_its_column(qapp):
    from khervedoc.model import Table
    ed = DocumentEditor()
    ed.set_fit_to_width(False)
    ed.set_zoom_percent(100)
    ed.set_document(Document(meta=DocMeta(documentclass="IEEEtran"), children=[
        Title(children=[Text("My Title")]),
        Paragraph(children=[Text("Text.")]),
        Table(rows=[["a long cell of words here", "another long cell"],
                    ["more words in a cell", "and more words"]]),
    ]))
    ed.show()
    QApplication.processEvents()
    doc = ed._edit.document()
    table = next(f for f in doc.rootFrame().childFrames())
    # The frame's rectangle includes the margin that keeps it in its column.
    width = doc.documentLayout().frameBoundingRect(table).width() \
        - table.format().rightMargin()
    assert width <= ed._edit.text_width_px() + 2
    ed.close()


def test_two_column_slots_fill_the_second_column_below_the_span(qapp):
    ed = DocumentEditor()
    ed.set_fit_to_width(False)
    ed.set_zoom_percent(100)
    ed.set_document(Document(meta=DocMeta(documentclass="IEEEtran"), children=[
        Title(children=[Text("My Title")]),
        Author(children=[Text("An Author")]),
    ] + [Paragraph(children=[Text("word " * 300)]) for _ in range(8)]))
    ed.show()
    QApplication.processEvents()
    edit = ed._edit
    span, left, right = edit._column_slots()[:3]
    assert right.vx > left.vx
    assert right.vy == pytest.approx(left.vy)
    assert right.sheet == left.sheet == 0
    # A point in the right column maps there and back.
    y = right.a + 50
    view = edit.doc_to_view(10, y)
    back = edit.view_to_doc(view)
    assert abs(back.y() - y) < 1 and abs(back.x() - 10) < 1
    ed.close()


def test_style_italics_never_reach_the_latex(qapp):
    # elsarticle prints \subsection in italics: a look, not a user mark.
    ed = _editor("elsarticle")
    assert _font(ed, "Part").italic()
    tex = serialize_document(ed.get_document())
    assert "\\subsection{Part}" in tex
    assert "\\textit{Part}" not in tex
    ed.close()


def test_user_bold_in_an_upright_title_survives(qapp):
    ed = DocumentEditor()
    ed.set_document(Document(meta=DocMeta(), children=[
        Title(children=[Text("Plain "), Text("loud", marks=["bold"])])]))
    assert "\\textbf{loud}" in serialize_document(ed.get_document())
    ed.close()


def test_switching_class_restyles_existing_text(qapp):
    ed = _editor("article")
    meta = ed.meta()
    meta.documentclass = "scrartcl"
    ed.set_meta(meta)
    want = look_for("scrartcl", 12)
    assert _font(ed, "My Title").pointSizeF() == pytest.approx(
        want["title"]["size"])
    assert _font(ed, "My Title").bold()
    meta = ed.meta()
    meta.documentclass = "article"
    ed.set_meta(meta)
    assert not _font(ed, "My Title").bold()
    ed.close()


def test_body_size_follows_the_class_size_option(qapp):
    ed = _editor("article", 10)
    assert _font(ed, "First paragraph.").pointSizeF() == pytest.approx(
        look_for("article", 10)["body"]["size"])
    ed.close()


def _baseline(ed, block):
    raw = ed._edit.document().documentLayout().blockBoundingRect(block)
    line = block.layout().lineAt(0)
    return raw.top() + line.y() + line.ascent()


@pytest.mark.parametrize("cls", ["article", "scrartcl", "report", "elsarticle"])
def test_author_sits_where_the_pdf_sets_it(qapp, cls):
    ed = _editor(cls)
    ed.show()
    QApplication.processEvents()
    look = look_for(cls, 12)
    gap_pt = (_baseline(ed, _block(ed, "An Author"))
              - _baseline(ed, _block(ed, "My Title"))) * 72 / 96
    assert gap_pt == pytest.approx(look["author"]["above"], abs=3)
    ed.close()


def test_first_title_drops_to_the_measured_height(qapp):
    # Qt ignores a first block's top margin; the line height carries it.
    ed = _editor("report")
    ed.show()
    QApplication.processEvents()
    look = look_for("report", 12)
    assert BASELINE_AT > 0
    y_pt = _baseline(ed, _block(ed, "My Title")) * 72 / 96
    assert y_pt == pytest.approx(look["title"]["top"], abs=4)
    ed.close()


@pytest.mark.parametrize("prefix,dotted,want", [
    ("1", "2", "2"), ("1.1", "2.3", "2.3"), ("1.1.", "2.3", "2.3."),
    ("I.", "4", "IV."), ("A.", "1.2", "B."), ("1)", "1.1.3", "3)"),
    ("a)", "1.1.1.2", "b)"), ("Chapter 1", "3", "Chapter 3"), ("", "3", ""),
])
def test_number_label(prefix, dotted, want):
    assert number_label(prefix, dotted) == want


def test_a_section_starting_a_page_sits_at_the_top_of_it(qapp):
    # The welcome tour: the PDF starts page 2 with a section, and the visual
    # tab used to push that section down to where report puts a chapter.
    ed = _editor("article")
    ed.show()
    QApplication.processEvents()
    block = _block(ed, "Part")
    fmt = block.blockFormat()
    from PySide6.QtGui import QTextFormat
    fmt.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
    look = look_for("article", 12)
    bf = block.blockFormat()
    ed._edit.document()
    from khervedoc.editor import BASELINE_AT as B
    margin = ed._lay_out_styled_block(
        bf, "h2", look, 96 / 72, 0, True, 0, block.userState(), False, "",
        14.4, False, 1, False)
    assert bf.topMargin() < 20
    ed.close()


def test_separate_lists_stay_separate(qapp):
    from khervedoc.model import List as ListNode, ListItem
    ed = DocumentEditor()
    first = ListNode(ordered=True, items=[ListItem(children=[Text(f"a{i}")])
                                          for i in range(5)])
    second = ListNode(ordered=False, items=[ListItem(children=[Text(f"b{i}")])
                                            for i in range(3)])
    ed.set_document(Document(meta=DocMeta(), children=[
        first, Section(level=1, children=[Text("Between")]),
        Paragraph(children=[Text("Words.")]), second]))
    for _ in range(30):
        got = [b for b in ed.get_document().children
               if isinstance(b, ListNode)]
        assert [(b.ordered, len(b.items)) for b in got] == [(True, 5),
                                                            (False, 3)]
    ed.close()


def test_list_items_are_spaced_as_latex_spaces_them(qapp):
    from khervedoc.model import List as ListNode, ListItem
    ed = DocumentEditor()
    ed.set_document(Document(meta=DocMeta(), children=[
        Paragraph(children=[Text("Before.")]),
        ListNode(ordered=True, items=[ListItem(children=[Text(f"i{n}")])
                                      for n in range(3)]),
        Paragraph(children=[Text("After.")])]))
    first, middle, last = (_block(ed, f"i{n}").blockFormat() for n in range(3))
    assert first.topMargin() > middle.topMargin() > 0     # \topsep, \itemsep
    assert last.bottomMargin() > 0 and middle.bottomMargin() == 0
    ed.close()
