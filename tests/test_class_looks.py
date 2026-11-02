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


def test_measured_values_of_a_broken_class_fall_back_to_article():
    assert is_broken("svjour3")
    assert look_for("svjour3", 12) is look_for("article", 12)
    assert not is_broken("article")


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
