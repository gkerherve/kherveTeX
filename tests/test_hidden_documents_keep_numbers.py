"""A document unticked in the Documents panel is left out of the PDF, but
the others keep their numbers: Chapter 3 stays Chapter 3, Appendix B
stays B, section 1.3 stays 1.3, in the PDF and on the page."""

import os

import pytest

from khervedoc.model import (
    ChapterEntry, DocMeta, Document, Paragraph, Project, Section, Text,
)
from khervedoc.serializer import serialize_project_master


def _doc(*heads):
    blocks = []
    for level, text in heads:
        blocks.append(Section(level=level, children=[Text(text)]))
        blocks.append(Paragraph(children=[Text("Words.")]))
    return Document(children=blocks)


def _project(cls, entries):
    proj = Project()
    proj.meta = DocMeta(title="Thesis", documentclass=cls)
    proj.chapters = [ChapterEntry(path=f"{name}.ktex", label=name, enabled=on,
                                  chapter_type=ctype)
                     for name, ctype, on in entries]
    return proj


def _between(master, a, b):
    return master.split(f"{{{a}}}", 1)[1].split(f"{{{b}}}", 1)[0]


def test_chapter_after_a_hidden_one_keeps_its_number():
    proj = _project("report", [("one", "chapter", True), ("two", "chapter", False),
                               ("three", "chapter", True)])
    docs = [_doc((1, "One")), _doc((1, "Two")), _doc((1, "Three"))]
    master = serialize_project_master(proj, docs)
    assert "\\include{two}" not in master
    assert "\\setcounter{chapter}{2}" in _between(master, "one", "three")


def test_appendix_after_a_hidden_one_keeps_its_letter():
    proj = _project("report", [("one", "chapter", True), ("a", "appendix", False),
                               ("b", "appendix", True)])
    docs = [_doc((1, "One")), _doc((1, "Data")), _doc((1, "Code"))]
    master = serialize_project_master(proj, docs)
    # \appendix (written before the hidden A, it must not go with it),
    # then B: the chapter counter at 1 before its \chapter.
    assert "\\appendix" in _between(master, "one", "b")
    assert "\\setcounter{chapter}{1}" in _between(master, "one", "b")


def test_section_document_after_a_hidden_one_keeps_its_number():
    proj = _project("report", [("ch1", "chapter", True), ("s1", "section", True),
                               ("s2", "section", False), ("s3", "section", True)])
    docs = [_doc((1, "Intro")), _doc((2, "Aims")), _doc((2, "Scope")),
            _doc((2, "Plan"))]
    master = serialize_project_master(proj, docs)
    # Plan is 1.3 with Scope (1.2) left out.
    assert "\\setcounter{section}{2}" in _between(master, "s1", "s3")


def test_article_part_after_a_hidden_one_keeps_its_sections():
    proj = _project("article", [("p1", "chapter", True), ("p2", "chapter", False),
                                ("p3", "chapter", True)])
    docs = [_doc((1, "A"), (2, "A.1")), _doc((1, "B"), (1, "C")), _doc((1, "D"))]
    master = serialize_project_master(proj, docs)
    assert "\\setcounter{section}{3}" in _between(master, "p1", "p3")
    assert "\\setcounter{subsection}{0}" in _between(master, "p1", "p3")


def test_nothing_set_when_every_document_is_in():
    proj = _project("article", [("p1", "chapter", True), ("p2", "chapter", True)])
    master = serialize_project_master(proj, [_doc((1, "A")), _doc((1, "B"))])
    assert "\\setcounter{section}" not in master


# ---- the page view ----

@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    yield QApplication.instance() or QApplication([])


def test_page_view_counts_hidden_documents(qapp, tmp_path, monkeypatch):
    from khervedoc.mainwindow import MainWindow
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)
    w = MainWindow()
    try:
        proj = _project("report", [("one", "chapter", True), ("two", "chapter", False),
                                   ("three", "chapter", True)])
        w._project = proj
        w._project_path = tmp_path / "one.ktex"
        w._project_chapter_docs = {0: _doc((1, "One")), 1: _doc((1, "Two")),
                                   2: _doc((1, "Three"))}
        # Two chapters come before the third, the hidden one too.
        assert w._heading_offset_before(2)[1] == 2
        w._on_chapter_toggled(0, False)
        assert w._heading_offset_before(2)[1] == 2
    finally:
        w.close()
