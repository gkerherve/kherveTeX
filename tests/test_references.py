"""Citation / cross-reference display resolution for the visual editor."""
from khervedoc.model import (
    Citation, CrossRef, Document, Figure, MathBlock, Paragraph, RawLatex,
    Section, Table, Text,
)
from khervedoc.references import (
    ReferenceResolver, parse_bibtex, short_author,
)

BIB = r"""
@article{smith2020,
  author = {Smith, John and Doe, Anne and Roe, Bob},
  title = {A {Great} Paper},
  year = 2020,
}
@book{doe19, author = "Anne Doe", year = "2019", title = "Book"}
@comment{ignored}
"""


def test_parse_bibtex_fields():
    e = parse_bibtex(BIB)
    assert e["smith2020"]["year"] == "2020"
    assert "Great" in e["smith2020"]["title"]
    assert e["doe19"]["author"] == "Anne Doe"
    assert "ignored" not in e


def test_short_author():
    assert short_author("Smith, John and Doe, Anne and Roe, Bob") == "Smith et al."
    assert short_author("Anne Doe and Bo Li") == "Doe and Li"
    assert short_author("Anne Doe") == "Doe"


def _doc(*blocks):
    return Document(children=list(blocks))


def test_numeric_citations_follow_first_appearance(tmp_path):
    (tmp_path / "refs.bib").write_text(BIB, encoding="utf-8")
    doc = _doc(
        Paragraph(children=[Citation(keys=["doe19"]),
                            Citation(keys=["smith2020", "doe19"]),
                            Citation(keys=["nope"])]),
        RawLatex(text=r"\bibliography{refs}"),
    )
    r = ReferenceResolver(doc, tmp_path)
    assert r.cite_text(["doe19"]) == "[1]"
    assert r.cite_text(["smith2020", "doe19"]) == "[2, 1]"
    assert r.cite_text(["nope"]) == "[nope?]"


def test_author_year_styles(tmp_path):
    (tmp_path / "refs.bib").write_text(BIB, encoding="utf-8")
    doc = _doc(RawLatex(text=r"\addbibresource{refs.bib}"))
    r = ReferenceResolver(doc, tmp_path)
    assert r.cite_text(["smith2020"], "citet") == "Smith et al. (2020)"
    assert r.cite_text(["smith2020", "doe19"], "citep") == \
        "(Smith et al., 2020; Doe, 2019)"


def test_thebibliography_labels():
    doc = _doc(Paragraph(children=[Citation(keys=["a"])]),
               RawLatex(text="\\begin{thebibliography}{9}\n"
                             "\\bibitem[Ab99]{a} x\n\\end{thebibliography}"))
    assert ReferenceResolver(doc).cite_text(["a"]) == "[Ab99]"


def test_label_numbering():
    doc = _doc(
        Section(level=1, label="sec:a", children=[Text("A")]),
        Section(level=2, label="sec:a1", children=[Text("A1")]),
        Section(level=1, numbered=False, children=[Text("Unnumbered")]),
        Section(level=1, label="sec:b", children=[Text("B")]),
        MathBlock(latex="x", numbered=True, label="eq:x"),
        Figure(label="fig:1"), Table(label="tab:1"),
    )
    r = ReferenceResolver(doc)
    assert r.ref_text("sec:a") == "1"
    assert r.ref_text("sec:a1") == "1.1"
    assert r.ref_text("sec:b") == "2"
    assert r.ref_text("eq:x", "eqref") == "(1)"
    assert r.ref_text("fig:1") == "1" and r.ref_text("tab:1") == "1"
    assert r.ref_text("missing") == "??"


def test_chapter_prefixes():
    doc = _doc(Section(level=0, children=[Text("C1")]),
               Section(level=1, label="s", children=[Text("S")]),
               Figure(label="f"))
    r = ReferenceResolver(doc)
    assert r.ref_text("s") == "1.1" and r.ref_text("f") == "1.1"
