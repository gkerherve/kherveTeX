"""Affiliation and Correspondence title-block styles."""
from khervedoc.model import (
    Affiliation, Author, Correspondence, Document, DocMeta, Paragraph, Text,
    Title, from_json, to_json,
)
from khervedoc.serializer import serialize_document
from khervedoc.typst_serializer import serialize_document as to_typst


def _doc(cls="article"):
    return Document(meta=DocMeta(documentclass=cls), children=[
        Title(children=[Text(text="T")]),
        Author(children=[Text(text="A. One")]),
        Affiliation(children=[Text(text="Imperial College London")]),
        Correspondence(children=[Text(text="a.one@example.org")]),
        Paragraph(children=[Text(text="Body")]),
    ])


def test_json_round_trip():
    doc = _doc()
    assert from_json(to_json(doc)) == doc


def test_article_puts_affiliation_under_author_and_thanks_on_first():
    out = serialize_document(_doc())
    author = out[out.index("\\author{"):out.index("\\begin{document}")]
    assert "A. One\\thanks{a.one@example.org}" in author
    assert "{\\small\\itshape Imperial College London}" in author
    body = out[out.index("\\begin{document}"):]
    assert "Imperial College" not in body
    assert "a.one@example.org" not in body.replace("\\thanks", "")


def test_elsarticle_uses_address_and_cortext():
    out = serialize_document(_doc("elsarticle"))
    assert "\\address{Imperial College London}" in out
    assert "\\corref{cor1}" in out
    assert "\\cortext[cor1]{a.one@example.org}" in out


def test_typst_prints_affiliation():
    out = to_typst(_doc())
    assert "Imperial College London" in out
    assert "a.one\\@example.org" in out


def test_editor_round_trip_and_combo_codes():
    import os
    import pytest
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QTextCursor
    from khervedoc.editor import DocumentEditor
    QApplication.instance() or QApplication([])

    e = DocumentEditor()
    e.set_document(_doc())
    kinds = [type(b).__name__ for b in e.get_document().children]
    assert kinds[:4] == ["Title", "Author", "Affiliation", "Correspondence"]

    body = e._edit.document().findBlockByNumber(4)
    e.apply_heading(-7, block=body)
    assert isinstance(e.get_document().children[4], Affiliation)
    e._edit.setTextCursor(QTextCursor(body))
    assert e.current_heading_level() == -7
    e.apply_heading(-8, block=body)
    assert isinstance(e.get_document().children[4], Correspondence)


def test_author_and_affiliation_fonts_follow_zoom_and_stay_put():
    import os
    import pytest
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QTextCharFormat, QTextCursor
    from khervedoc.editor import DocumentEditor
    QApplication.instance() or QApplication([])

    e = DocumentEditor()
    e.set_document(_doc())
    doc = e._edit.document()
    author, aff = doc.findBlockByNumber(1), doc.findBlockByNumber(2)
    a_pt = author.begin().fragment().charFormat().fontPointSize()
    f_pt = aff.begin().fragment().charFormat().fontPointSize()
    assert a_pt > f_pt

    # Typing with a stray huge font must not survive in the author line.
    c = QTextCursor(author)
    c.movePosition(QTextCursor.EndOfBlock)
    big = QTextCharFormat(); big.setFontPointSize(40)
    c.insertText(" Jr", big)
    it = author.begin()
    while not it.atEnd():
        assert abs(it.fragment().charFormat().fontPointSize() - a_pt) < 0.01
        it += 1

    e.set_zoom_percent(200)
    a2 = author.begin().fragment().charFormat().fontPointSize()
    assert abs(a2 - 2 * a_pt) < 0.1


def test_formatting_marks_are_display_only():
    import os
    import pytest
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QTextOption
    from khervedoc.editor import DocumentEditor
    QApplication.instance() or QApplication([])

    e = DocumentEditor()
    e.set_document(_doc())
    before = e.get_document()
    e.set_show_formatting_marks(True)
    opt = e._edit.document().defaultTextOption()
    assert opt.flags() & QTextOption.ShowTabsAndSpaces
    assert e.get_document() == before
    e.set_show_formatting_marks(False)
    assert not (e._edit.document().defaultTextOption().flags()
                & QTextOption.ShowTabsAndSpaces)


def test_table_cell_given_as_list_does_not_crash_get_document():
    import os
    import pytest
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from khervedoc.editor import DocumentEditor
    from khervedoc.model import Table
    QApplication.instance() or QApplication([])

    e = DocumentEditor()
    e.set_document(Document(meta=DocMeta(), children=[
        Table(rows=[["a", ["b", "c"]], ["1", "2"]])]))
    tables = [b for b in e.get_document().children if isinstance(b, Table)]
    assert tables[0].rows[0][1] == "b c"
