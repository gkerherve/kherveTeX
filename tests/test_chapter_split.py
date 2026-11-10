"""A long imported document with chapters splits into a project with one
document per chapter, printing the same book."""
from pathlib import Path

from khervedoc import chapter_split, project_store
from khervedoc.model import (
    Document, DocMeta, InlineRaw, Paragraph, Section, Text, Title,
)
from khervedoc.serializer import serialize_project_master


def _para(n=1):
    return Paragraph(children=[Text(text="word " * 600)] * n)


def _chapter(name, level=0, paras=4):
    return [Section(level=level, children=[Text(text=name)])] + [_para() for _ in range(paras)]


def _thesis(cls="report", level=0, paras=10):
    return Document(meta=DocMeta(documentclass=cls), children=[
        Title(children=[Text(text="A Thesis")]),
        *_chapter("Introduction", level, paras),
        *_chapter("Methods", level, paras),
        *_chapter("Results", level, paras),
        Paragraph(children=[InlineRaw(latex="\\appendix")]),
        *_chapter("Derivations", level, 1),
    ])


def test_plan_front_matter_chapters_and_appendix():
    plan = chapter_split.chapter_plan(_thesis())
    assert [(label, kind) for label, kind, _ in plan] == [
        ("Front matter", "frontmatter"), ("Introduction", "chapter"),
        ("Methods", "chapter"), ("Results", "chapter"), ("Derivations", "appendix")]
    # The \appendix mark is left out: the project writes it.
    assert all(not chapter_split._is_appendix_mark(b) for _, _, bs in plan for b in bs)
    assert isinstance(plan[1][2][0], Section) and len(plan[1][2]) == 11


def test_offered_only_for_long_documents_with_chapters():
    assert chapter_split.should_offer(_thesis())
    assert not chapter_split.should_offer(_thesis(paras=1))          # short
    one = Document(meta=DocMeta(documentclass="report"), children=_chapter("Only", paras=40))
    assert not chapter_split.should_offer(one)                       # one chapter
    letter = Document(meta=DocMeta(documentclass="letter"), children=_thesis().children)
    assert chapter_split.chapter_plan(letter) == []


def test_word_thesis_heading_1_chapters_become_a_report(tmp_path: Path):
    doc = _thesis(cls="article", level=1)
    main = chapter_split.write_chapter_project(doc, tmp_path / "split", "thesis")
    proj = project_store.read_project(main)
    assert proj.meta.documentclass == "report"
    assert [c.chapter_type for c in proj.chapters] == [
        "frontmatter", "chapter", "chapter", "chapter", "appendix"]
    first = project_store.read_doc(tmp_path / "split" / proj.chapters[1].path)
    assert first.meta.documentclass == "report"
    assert [type(b).__name__ for b in first.children][:2] == ["Section", "Paragraph"]


def test_project_prints_the_appendix_after_appendix(tmp_path: Path):
    main = chapter_split.write_chapter_project(_thesis(), tmp_path / "split", "thesis")
    proj = project_store.read_project(main)
    assert main.name == proj.chapters[0].path == "Front matter.ktex"
    assert [c.path for c in proj.chapters[1:]] == [
        "01 Introduction.ktex", "02 Methods.ktex", "03 Results.ktex", "04 Derivations.ktex"]
    docs = [project_store.read_doc(tmp_path / "split" / c.path) for c in proj.chapters]
    master = serialize_project_master(proj, docs)
    assert master.index("\\include{03_Results}") < master.index("\\appendix") \
        < master.index("\\include{04_Derivations}")


def test_project_folder_is_new(tmp_path: Path):
    src = tmp_path / "thesis.pdf"
    assert chapter_split.project_folder(src).name == "thesis (chapters)"
    (tmp_path / "thesis (chapters)").mkdir()
    assert chapter_split.project_folder(src).name == "thesis (chapters) 2"


def test_pdf_thesis_headings_are_gathered_into_chapters():
    """A PDF import: the thesis title and the pages before Chapter 1 as
    headings, "CHAPTER I" on a line of its own, a title in two halves."""
    h = lambda t: Section(level=1, children=[Text(text=t)])
    doc = Document(meta=DocMeta(documentclass="article"), children=[
        h("Production of metal clusters"), _para(),
        h("Acknowledgement"), _para(), h("Contents"), _para(), h("List of Figures"), _para(),
        h("CHAPTERI"), h("Introduction"), *[_para() for _ in range(10)],
        h("CHAPTER II"), h("Investigation of clusters grown by"), h("Volmer-Weber mode"),
        *[_para() for _ in range(10)],
        h("Chapter 3"), h("Summary"), _para(),
        h("Appendix A"), _para(), h("Bibliography"), _para(),
    ])
    plan = chapter_split.chapter_plan(doc)
    assert [(label, kind, len(blocks)) for label, kind, blocks in plan] == [
        ("Front matter", "frontmatter", 8),
        ("Introduction", "chapter", 12),
        ("Investigation of clusters grown by Volmer-Weber mode", "chapter", 13),
        ("Summary", "chapter", 3),
        ("Appendix A", "appendix", 2),
        ("Bibliography", "appendix", 2)]
    assert chapter_split.should_offer(doc)


def test_split_by_section_runs_on_in_its_chapter(tmp_path: Path):
    h = lambda t, lv: Section(level=lv, children=[Text(text=t)])  # noqa: E731
    doc = Document(meta=DocMeta(documentclass="report"), children=[
        Title(children=[Text(text="A Thesis")]),
        h("Introduction", 0), _para(), h("Background", 2), *[_para() for _ in range(10)],
        h("Aims", 2), *[_para() for _ in range(10)],
        h("Methods", 0), *[_para() for _ in range(10)],
    ])
    plan = chapter_split.chapter_plan(doc, "section")
    assert [(label, kind) for label, kind, _ in plan] == [
        ("Front matter", "frontmatter"), ("Introduction", "chapter"),
        ("Background", "section"), ("Aims", "section"), ("Methods", "chapter")]
    main = chapter_split.write_chapter_project(doc, tmp_path / "split", "thesis", by="section")
    proj = project_store.read_project(main)
    assert [c.path for c in proj.chapters] == [
        "Front matter.ktex", "01 Introduction.ktex", "01.1 Background.ktex",
        "01.2 Aims.ktex", "02 Methods.ktex"]
    docs = [project_store.read_doc(tmp_path / "split" / c.path) for c in proj.chapters]
    master = serialize_project_master(proj, docs)
    # Sections continue their chapter's page; the chapter before them is
    # \input too (\include would leave its title on a page alone).
    assert "\\input{01_Introduction}" in master
    assert "\\input{01_1_Background}" in master and "\\input{01_2_Aims}" in master
    assert "\\include{02_Methods}" in master
    assert master.count("\\setcounter{chapter}") == 2
    # By chapter, the same document keeps \include.
    assert len(chapter_split.chapter_plan(doc)) == 3


def test_split_into_documents_command_opens_the_project(tmp_path: Path, monkeypatch):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from khervedoc.mainwindow import MainWindow
    from khervedoc import kdocz
    w = MainWindow(theme_name="Light")
    w._settings = QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)
    src = tmp_path / "thesis.ktex"
    kdocz.save_kdocz(_thesis(), src)
    w._open_path(src)
    asked = []
    monkeypatch.setattr(w, "_ask_split", lambda name, doc, folder, keep: asked.append((name, folder.name, keep)) or "chapter")
    w._split_into_documents()
    assert asked == [("thesis.ktex", "thesis (chapters)", "Cancel")]
    assert w._project is not None
    assert [c.label for c in w._project.chapters] == [
        "Front matter", "Introduction", "Methods", "Results", "Derivations"]
    assert w._project_path == tmp_path / "thesis (chapters)" / "Front matter.ktex"
