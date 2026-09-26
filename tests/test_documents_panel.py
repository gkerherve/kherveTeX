"""The Documents panel: always visible, lists a single document, and
turns it into a project the moment a second document is added."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QInputDialog  # noqa: E402

from khervedoc.model import (  # noqa: E402
    DocMeta, Document, Paragraph, Section, Text,
)


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, monkeypatch):
    from khervedoc.mainwindow import MainWindow
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)
    w = MainWindow()
    yield w
    w.close()


def _names(w):
    lst = w._project_sidebar._list
    return [lst.item(i).text() for i in range(lst.count())]


def test_single_document_is_listed(window, tmp_path):
    assert not window._project_dock.isHidden()
    assert len(_names(window)) == 1
    path = tmp_path / "thesis.ktex.json"
    window._current_path = path
    window._write_to(path)
    window._update_title()
    assert "thesis" in _names(window)[0]


def test_adding_a_document_shows_both(window, tmp_path, monkeypatch):
    doc = Document(meta=DocMeta(title="My thesis"), children=[
        Section(level=1, children=[Text("Introduction")]),
        Paragraph(children=[Text("Original words.")])])
    window._editor.set_document(doc)
    path = tmp_path / "thesis.ktex.json"
    window._current_path = path
    window._write_to(path)
    monkeypatch.setattr(QInputDialog, "getText",
                        lambda *a, **k: ("Methods", True))
    window._on_add_document()
    proj = window._project
    assert proj is not None and len(proj.chapters) == 2
    assert len(_names(window)) == 2
    assert "Methods" in window._editor.text_edit.toPlainText()
    window._switch_chapter(0)
    assert "Original words." in window._editor.text_edit.toPlainText()
    assert (tmp_path / "thesis.kdocproj.json").exists()
    master = (tmp_path / "thesis.tex").read_text()
    assert "\\begin{document}" in master           # not a chapter body
    assert "\\include{thesis-1}" in master and "\\include{methods}" in master
    assert "Original words." in (tmp_path / "thesis-1.tex").read_text()


def test_section_numbers_continue_across_documents(window, tmp_path,
                                                   monkeypatch):
    from khervedoc.editor import _P_HEADING_NUMBER
    window._editor.set_document(Document(children=[
        Section(level=1, children=[Text("Introduction")]),
        Section(level=2, children=[Text("Background")]),
        Paragraph(children=[Text("x")])]))
    path = tmp_path / "thesis.ktex.json"
    window._current_path = path
    window._write_to(path)
    monkeypatch.setattr(QInputDialog, "getText",
                        lambda *a, **k: ("Methods", True))
    window._on_add_document()

    def first_number():
        block = window._editor.text_edit.document().firstBlock()
        return block.blockFormat().property(_P_HEADING_NUMBER)

    assert first_number() == "2"          # continues after "1 Introduction"
    window._switch_chapter(0)
    assert first_number() == "1"
    from PySide6.QtCore import Qt
    window._project_sidebar._list.item(0).setCheckState(Qt.Unchecked)
    window._switch_chapter(1)
    assert first_number() == "1"          # ...so Methods is section 1
