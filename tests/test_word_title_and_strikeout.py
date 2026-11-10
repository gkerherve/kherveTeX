"""Word files from the web: the Title style used more than once keeps one
title, and struck-out text loads ulem for \\sout."""
from pathlib import Path

import docx

from khervedoc.importers import import_docx
from khervedoc.model import Document, DocMeta, Paragraph, Section, Text, Title
from khervedoc.serializer import serialize_document


def test_title_style_used_twice_keeps_one_title(tmp_path: Path):
    d = docx.Document()
    d.add_paragraph("", style="Title")
    d.add_paragraph("User Guide", style="Title")
    d.add_paragraph("Some text.")
    d.add_paragraph("CONTENTS", style="Title")
    d.save(tmp_path / "t.docx")
    doc = import_docx(tmp_path / "t.docx", tmp_path / "img")
    titles = [b for b in doc.children if isinstance(b, Title)]
    assert [t.children[0].text for t in titles] == ["User Guide"]
    later = [b for b in doc.children if isinstance(b, Section)]
    assert [(s.children[0].text, s.numbered) for s in later] == [("CONTENTS", False)]
    assert serialize_document(doc).count("\\maketitle") == 1


def test_strikeout_loads_ulem():
    doc = Document(meta=DocMeta(), children=[
        Paragraph(children=[Text(text="gone", marks=["strikethrough"])])])
    tex = serialize_document(doc)
    assert "\\sout{gone}" in tex
    assert "\\usepackage[normalem]{ulem}" in tex.split("\\begin{document}")[0]
    plain = serialize_document(Document(meta=DocMeta(), children=[Paragraph(children=[Text(text="x")])]))
    assert "ulem" not in plain
