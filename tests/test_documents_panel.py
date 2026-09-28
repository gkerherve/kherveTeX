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


# ---------------------------------------------------------- order / remove

def _three_docs(window, tmp_path, monkeypatch):
    """Intro (this file), then Methods, then Results."""
    window._editor.set_document(Document(children=[
        Section(level=1, children=[Text("Introduction")]),
        Paragraph(children=[Text("intro words")])]))
    path = tmp_path / "thesis.ktex.json"
    window._current_path = path
    window._write_to(path)
    for name in ("Methods", "Results"):
        monkeypatch.setattr(QInputDialog, "getText",
                            lambda *a, n=name, **k: (n, True))
        window._on_add_document()
    return window._project


def _labels(window):
    return [ch.label or ch.path for ch in window._project.chapters]


def _first_number(window):
    from khervedoc.editor import _P_HEADING_NUMBER
    block = window._editor.text_edit.document().firstBlock()
    return block.blockFormat().property(_P_HEADING_NUMBER)


def _includes(tmp_path):
    import re
    return re.findall(r"\\include\{([^}]+)\}",
                      (tmp_path / "thesis.tex").read_text())


def test_move_down_reorders_project_and_master(window, tmp_path, monkeypatch):
    _three_docs(window, tmp_path, monkeypatch)
    window._save_project()
    before = _includes(tmp_path)
    assert len(before) == 3
    window._project_sidebar._list.setCurrentRow(0)
    window._project_sidebar._move_down()
    assert _includes(tmp_path) == [before[1], before[0], before[2]]
    assert "Methods" in _labels(window)[0]


def test_reordering_keeps_each_document_with_its_text(window, tmp_path,
                                                      monkeypatch):
    _three_docs(window, tmp_path, monkeypatch)
    window._reorder_chapters([2, 0, 1])
    window._switch_chapter(1)
    assert "intro words" in window._editor.text_edit.toPlainText()
    window._switch_chapter(0)
    assert "Results" in window._editor.text_edit.toPlainText()


def test_open_document_is_renumbered_when_moved(window, tmp_path, monkeypatch):
    _three_docs(window, tmp_path, monkeypatch)
    window._switch_chapter(2)                  # Results: section 3
    assert _first_number(window) == "3"
    window._project_sidebar._list.setCurrentRow(2)
    window._project_sidebar._move_up()
    window._project_sidebar._move_up()         # now first
    assert window._project_chapter_idx == 0
    assert _first_number(window) == "1"
    assert "Results" in window._editor.text_edit.toPlainText()


def test_other_document_renumbers_when_open_one_moves(window, tmp_path,
                                                      monkeypatch):
    _three_docs(window, tmp_path, monkeypatch)
    window._switch_chapter(0)                  # Introduction: 1
    window._reorder_chapters([1, 0, 2])        # Methods goes first
    assert window._project_chapter_idx == 1
    assert _first_number(window) == "2"


def test_drag_and_drop_reorders(window, tmp_path, monkeypatch, qapp):
    from PySide6.QtCore import QModelIndex
    _three_docs(window, tmp_path, monkeypatch)
    lst = window._project_sidebar._list
    assert lst.model().moveRow(QModelIndex(), 2, QModelIndex(), 0)
    qapp.processEvents()
    assert "Results" in _labels(window)[0]
    assert len(window._project.chapters) == 3


def test_remove_button_takes_document_out(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    _three_docs(window, tmp_path, monkeypatch)
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: QMessageBox.Yes)
    window._switch_chapter(2)
    window._project_sidebar._list.setCurrentRow(1)
    window._project_sidebar._remove_current()
    assert len(window._project.chapters) == 2
    assert not any("Methods" in x for x in _labels(window))
    assert len(_includes(tmp_path)) == 2
    assert window._project_chapter_idx == 1    # Results, moved up
    assert "Results" in window._editor.text_edit.toPlainText()
    assert _first_number(window) == "2"
    assert (tmp_path / "methods.kdoc.json").exists() or \
        any(p.name.startswith("methods") for p in tmp_path.iterdir())


def test_removing_the_open_document_opens_a_neighbour(window, tmp_path,
                                                      monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    _three_docs(window, tmp_path, monkeypatch)
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: QMessageBox.Yes)
    window._switch_chapter(0)
    window._remove_chapter(0)
    assert window._project_chapter_idx == 0
    assert "Methods" in window._editor.text_edit.toPlainText()


def test_remove_cancelled_keeps_document(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    _three_docs(window, tmp_path, monkeypatch)
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: QMessageBox.No)
    window._remove_chapter(1)
    assert len(window._project.chapters) == 3


def test_remove_button_only_shown_for_projects(window, tmp_path, monkeypatch):
    sb = window._project_sidebar
    assert sb._remove_btn.isHidden()
    _three_docs(window, tmp_path, monkeypatch)
    assert not sb._remove_btn.isHidden()


def test_page_ranges_follow_new_order(window, tmp_path, monkeypatch):
    proj = _three_docs(window, tmp_path, monkeypatch)
    proj.auto_page_numbers = True
    for ch, pages in zip(proj.chapters, (10, 4, 6)):
        ch.last_known_pages = pages
    window._project_sidebar.recompute_auto_pages()
    assert [c.start_page for c in proj.chapters] == [1, 11, 15]
    window._project_sidebar._list.setCurrentRow(0)
    window._project_sidebar._move_down()
    assert [c.last_known_pages for c in proj.chapters] == [4, 10, 6]
    assert [c.start_page for c in proj.chapters] == [1, 5, 15]


# ---------------------------------------------------------- add existing

def test_add_existing_files_from_elsewhere(window, tmp_path, monkeypatch):
    from khervedoc import kdocz
    from khervedoc.model import from_json, to_json
    proj = _three_docs(window, tmp_path, monkeypatch)
    other = tmp_path / "elsewhere"
    other.mkdir()
    a = other / "appendix.kdoc.json"
    a.write_text(to_json(Document(children=[
        Paragraph(children=[Text("appendix words")])])), encoding="utf-8")
    b = other / "notes.ktexz"
    kdocz.save_kdocz(Document(children=[
        Paragraph(children=[Text("bundle words")])]), b)

    window._add_existing_documents([str(a), str(b)])
    assert [ch.label for ch in proj.chapters][-2:] == ["appendix", "notes"]
    texts = [(tmp_path / ch.path).read_text() for ch in proj.chapters[-2:]]
    assert "appendix words" in texts[0] and "bundle words" in texts[1]
    # Adding the same file again does not duplicate it.
    added = tmp_path / proj.chapters[-2].path
    window._add_existing_documents([str(added)])
    assert len(proj.chapters) == 5
    assert from_json(added.read_text()).children


def test_dropping_files_on_the_list_adds_them(window, tmp_path, monkeypatch,
                                              qapp):
    from PySide6.QtCore import QMimeData, QPoint, QUrl, Qt
    from PySide6.QtGui import QDropEvent
    from khervedoc.model import to_json
    got = []
    # Only the signal is under test here, not the window's handler.
    window._project_sidebar.addExistingRequested.disconnect()
    window._project_sidebar.addExistingRequested.connect(got.append)
    f = tmp_path / "x.kdoc.json"
    f.write_text(to_json(Document(children=[])), encoding="utf-8")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(f)),
                  QUrl.fromLocalFile(str(tmp_path / "pic.png"))])
    ev = QDropEvent(QPoint(5, 5), Qt.CopyAction, mime, Qt.LeftButton,
                    Qt.NoModifier)
    vp = window._project_sidebar._list.viewport()
    assert window._project_sidebar.eventFilter(vp, ev)
    qapp.processEvents()
    assert got == [[str(f)]]
