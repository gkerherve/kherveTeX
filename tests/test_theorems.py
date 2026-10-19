"""Theorem-like environments are editable blocks, not raw LaTeX."""
import os
import re

import pytest

from khervedoc.importers import import_body_fragment
from khervedoc.model import (
    Document, Paragraph, RawLatex, Section, Text, Theorem, from_json, to_json,
)
from khervedoc.serializer import serialize_document
from khervedoc.typst_serializer import serialize_document as typst


def _doc(*blocks):
    return Document(children=[Section(children=[Text("S")]), *blocks])


def test_paragraphs_of_one_environment_serialize_together():
    tex = serialize_document(_doc(
        Theorem(kind="lemma", title="Key", children=[Text("A.")]),
        Theorem(kind="proof", children=[Text("B.")]),
        Theorem(kind="proof", children=[Text("C.")], start=False)))
    assert "\\begin{lemma}[Key]\nA.\n\\end{lemma}" in tex
    assert "\\begin{proof}\nB.\n\nC.\n\\end{proof}" in tex
    assert tex.count("\\begin{proof}") == 1


def test_preamble_defines_only_missing_environments():
    tex = serialize_document(_doc(Theorem(kind="definition",
                                          children=[Text("x")])))
    assert r"\@ifundefined{theorem}{\newtheorem{theorem}{Theorem}[section]}" in tex
    assert r"\@ifundefined{definition}{\newtheorem{definition}[theorem]" in tex
    assert "lemma" not in tex.split("\\begin{document}")[0]
    assert "\\newtheorem" not in serialize_document(_doc())


def test_import_round_trip_and_json():
    src = ("\\begin{theorem}[Heine--Borel]\nA set is compact.\n"
           "\\end{theorem}\n\n\\begin{proof}\nOne.\n\nTwo.\n\\end{proof}")
    blocks = import_body_fragment(src)
    assert [(b.kind, b.start) for b in blocks] == [
        ("theorem", True), ("proof", True), ("proof", False)]
    assert blocks[0].title == "Heine--Borel"
    doc = from_json(to_json(Document(children=blocks)))
    assert doc.children[2].start is False
    tex = serialize_document(doc)
    assert "\\begin{theorem}[Heine--Borel]" in tex


def test_typst_labels():
    out = typst(Document(children=[
        Theorem(kind="example", title="", children=[Text("e")])]))
    assert "*Example.* e" in out


def test_lecture_notes_example_has_no_raw_theorems():
    from khervedoc.examples import lecture_notes
    doc = lecture_notes()
    assert any(isinstance(b, Theorem) for b in doc.children)
    assert not any(isinstance(b, RawLatex) and re.match(
        r"\s*\\begin\{(theorem|lemma|definition|proof|example)\}", b.text)
        for b in doc.children)


# ---------- editor ----------

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_editor_round_trip_enter_and_kind(tmp_path):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from khervedoc.editor import DocumentEditor
    ed = DocumentEditor()
    ed.set_document_dir(tmp_path)
    src = Document(children=[
        Paragraph(children=[Text("intro")]),
        Theorem(kind="definition", title="Open", children=[Text("D")])])
    ed.set_document(src)
    got = [b for b in ed.get_document().children if isinstance(b, Theorem)]
    assert [(b.kind, b.title, b.start) for b in got] == [
        ("definition", "Open", True)]
    c = ed._edit.textCursor()
    c.movePosition(QTextCursor.End)
    ed._edit.setTextCursor(c)
    assert ed.context_object() == "theorem"
    QTest.keyClick(ed._edit, Qt.Key_Return)
    ed._edit.insertPlainText("more")
    QTest.keyClick(ed._edit, Qt.Key_Return)
    QTest.keyClick(ed._edit, Qt.Key_Return)      # empty: leaves the theorem
    ed._edit.insertPlainText("body")
    ed.set_theorem_kind  # noqa: B018 - API exists
    kinds = [(type(b).__name__, getattr(b, "start", None))
             for b in ed.get_document().children]
    assert kinds[-3:] == [("Theorem", True), ("Theorem", False),
                          ("Paragraph", None)]
