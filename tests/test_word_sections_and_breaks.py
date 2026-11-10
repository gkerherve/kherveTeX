"""Word files from the web (an IEEE template): line and column breaks,
authors Word sets in columns, the section that holds most of the text,
empty paragraphs at the start, a project in a synced folder."""
import copy
from pathlib import Path

import docx
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn

from khervedoc import compiler, project_store
from khervedoc.importers import import_docx
from khervedoc.model import Author, InlineRaw, Paragraph, Text, Title


def _section_end(par, cols: int, src) -> None:
    """End a Word section at `par`, laid out in `cols` columns."""
    sect = copy.deepcopy(src.sections[0]._sectPr)
    c = sect.find(qn("w:cols"))
    if c is None:
        c = sect.makeelement(qn("w:cols"), {})
        sect.append(c)
    c.set(qn("w:num"), str(cols))
    par._p.get_or_add_pPr().append(sect)


def _ieee_like(tmp_path: Path) -> Path:
    d = docx.Document()
    d.add_paragraph("")
    d.add_paragraph("", style="Title")
    d.add_paragraph("A Paper", style="Title")
    _section_end(d.add_paragraph(""), 1, d)
    # Six authors in three columns, as Word stores them: 1, 4 | 2, 5 | 3, 6.
    for names in (["1"], ["4", "2"], ["5", "3"], ["6"]):
        p = d.add_paragraph(style="Subtitle")
        for k, n in enumerate(names):
            if k:
                p.add_run().add_break(WD_BREAK.COLUMN)
            p.add_run(f"Author {n}")
            p.add_run().add_break()
            p.add_run(f"Dept {n}")
    _section_end(p, 3, d)
    for _ in range(20):
        d.add_paragraph("Body text of the paper, in two columns. " * 8)
    _section_end(d.add_paragraph(""), 2, d)
    d.add_paragraph("end")
    out = tmp_path / "ieee.docx"
    d.save(out)
    return out


def test_ieee_like_paper(tmp_path: Path):
    doc = import_docx(_ieee_like(tmp_path), tmp_path / "img")
    # No empty paragraph before the title; one title.
    assert isinstance(doc.children[0], Title)
    assert sum(isinstance(b, Title) for b in doc.children) == 1
    # The body's section is in two columns.
    assert doc.meta.column_count == 2
    # The authors in reading order, side by side, each on two lines.
    authors = [b for b in doc.children if isinstance(b, Author)]
    assert len(authors) == 1
    parts = authors[0].children
    names = [x.text for x in parts if isinstance(x, Text) and x.text.startswith("Author")]
    assert names == [f"Author {n}" for n in range(1, 7)]
    raws = [x.latex for x in parts if isinstance(x, InlineRaw)]
    assert raws.count("\\and{}") == 5 and raws.count("\\\\") == 6
    assert not any(isinstance(b, Paragraph) and b.children and isinstance(b.children[0], InlineRaw)
                   for b in doc.children)


def test_line_breaks_inside_a_paragraph(tmp_path: Path):
    d = docx.Document()
    p = d.add_paragraph()
    p.add_run().add_break()
    r = p.add_run("12 Harbour Road")
    r.add_break()
    r.add_break()
    p.add_run("Bristol")
    p.add_run().add_break()
    d.save(tmp_path / "a.docx")
    para = import_docx(tmp_path / "a.docx", tmp_path / "img").children[0]
    assert [(type(x).__name__, getattr(x, "text", getattr(x, "latex", ""))) for x in para.children] == [
        ("Text", "12 Harbour Road"), ("InlineRaw", "\\\\"), ("Text", "Bristol")]


def test_project_figures_stay_out_of_synced_folders(tmp_path: Path):
    synced = Path("/Users/x/Library/CloudStorage/OneDrive-Example/Thesis")
    assert project_store.is_synced_folder(synced)
    assert project_store.is_synced_folder(Path("/Users/x/Dropbox/Thesis"))
    assert not project_store.is_synced_folder(Path("/Users/x/Documents/Thesis"))
    assert ".kherve" not in str(project_store.files_dir(synced, "01 Intro"))
    assert project_store.files_dir(tmp_path, "01 Intro") == tmp_path / ".kherve" / "files" / "01 Intro"


def test_a_file_read_that_timed_out_is_not_offline():
    log = ("warning: error closing out input /a/b c/figure_021.png\n"
           "caused by: Operation timed out (os error 60)\n")
    assert compiler._slow_file_from_log(log) == "/a/b c/figure_021.png"
    assert compiler._slow_file_from_log("error sending request") is None
