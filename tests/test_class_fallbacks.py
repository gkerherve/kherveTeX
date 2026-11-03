"""Every document class the toolbar offers must compile the editor's blocks."""
import re

import fitz
import pytest

from khervedoc.compiler import (
    compile_tex, tectonic_available, template_sample_document,
)
from khervedoc.editor import TEMPLATE_CHOICES
from khervedoc.model import (
    Affiliation, Author, Correspondence, DocMeta, Document, Paragraph,
    Project, Section, Text, Title,
)
from khervedoc.serializer import serialize_document, serialize_project_master


def _tex(cls: str) -> str:
    return serialize_document(template_sample_document(cls))


def test_keyword_and_abstract_fallbacks_everywhere():
    tex = _tex("article")
    assert r"\@ifundefined{keyword}{\newenvironment{keyword}" in tex
    assert r"\@ifundefined{abstract}" in tex


def test_tufte_gets_names_only_and_no_subsubsection():
    tex = _tex("tufte-book")
    assert r"\author{Jane Doe}" in tex
    assert r"\let\subsubsection\paragraph" in tex
    assert r"\renewcommand{\allcapsspacing}[1]{#1}" in tex


def test_revtex_front_matter_in_body_and_no_multicol():
    tex = _tex("revtex4-2")
    pre, body = tex.split(r"\begin{document}")
    assert "{multicol}" not in pre
    assert r"\affiliation{Imperial College London}" in body
    assert body.index(r"\begin{abstract}") < body.index(r"\maketitle")


def test_beamer_has_no_geometry():
    assert "{geometry}" not in _tex("beamer")


def test_moderncv_uses_name():
    tex = _tex("moderncv")
    assert r"\name{Jane}{Doe}" in tex
    assert r"\author{" not in tex


def test_tikzposter_body_in_block():
    assert r"\block{}{" in _tex("tikzposter")


def test_elegantbook_uses_bibtex_backend():
    assert r"\documentclass[bibtex]{elegantbook}" in _tex("elegantbook")


def _front_matter_doc(cls: str, **meta) -> Document:
    """A correspondence line and all five heading levels."""
    blocks = [
        Title(children=[Text("T")]),
        Author(children=[Text("Ann Lee")]),
        Affiliation(children=[Text("Imperial")]),
        Author(children=[Text("Bo Ng")]),
        Correspondence(children=[Text("ann@example.org")]),
    ]
    for level in range(1, 6):
        blocks += [Section(level=level, children=[Text(f"Head{level}")]),
                   Paragraph(children=[Text("Words.")])]
    return Document(meta=DocMeta(documentclass=cls, **meta), children=blocks)


def test_classes_without_a_redistributable_file_are_not_offered():
    assert not {"aa", "svjour3"} & set(TEMPLATE_CHOICES)


def test_acmart_gets_authornote_and_one_author_per_person():
    pre = serialize_document(_front_matter_doc("acmart")).split(
        r"\begin{document}")[0]
    assert r"\thanks" not in pre
    assert (r"\author{Ann Lee}" "\n" r"\authornote{ann@example.org}" "\n"
            r"\affiliation[obeypunctuation=true]{\institution{Imperial}\country{}}"
            "\n" r"\author{Bo Ng}") in pre


def test_acmart_moves_thanks_out_of_the_author_field():
    doc = Document(meta=DocMeta(documentclass="acmart",
                                author=r"Ann\thanks{Note}"),
                   children=[Title(children=[Text("T")])])
    assert (r"\author{Ann}" "\n" r"\authornote{Note}"
            in serialize_document(doc))


def test_llncs_has_institute_and_a_real_subparagraph():
    pre = serialize_document(_front_matter_doc("llncs")).split(
        r"\begin{document}")[0]
    assert r"\let\subparagraph\paragraph" in pre
    assert (r"\author{Ann Lee\thanks{ann@example.org} \and Bo Ng}" "\n"
            r"\institute{Imperial}") in pre


@pytest.mark.parametrize("cls, expected", [
    ("acmart", r"\authornote{ann@example.org}"),
    ("llncs", r"\let\subparagraph\paragraph"),
])
def test_project_master_shares_the_class_fixes(cls, expected):
    proj = Project(meta=DocMeta(documentclass=cls))
    tex = serialize_project_master(proj, [_front_matter_doc(cls)])
    assert expected in tex


@pytest.mark.skipif(not tectonic_available(), reason="tectonic missing")
@pytest.mark.parametrize("cls", ["acmart", "llncs"])
def test_correspondence_and_five_levels_compile(cls, tmp_path):
    tex = serialize_document(_front_matter_doc(cls))
    result = compile_tex(tex, tmp_path)
    assert result.ok, result.error
    assert not re.findall(r"^error:.*", result.log, re.M)
    text = "".join(p.get_text() for p in fitz.open(result.pdf_path))
    assert "ann@example.org" in text
    assert "Institute Given" not in text


@pytest.mark.skipif(not tectonic_available(), reason="tectonic missing")
def test_missing_class_is_a_failure_with_no_pdf(tmp_path):
    tex = (r"\documentclass{khervetexnosuchclass}"
           r"\begin{document}Hi\end{document}")
    result = compile_tex(tex, tmp_path)
    assert not result.ok
    assert result.pdf_path is None
    assert "khervetexnosuchclass" in result.error
    assert "Manage styles" in result.error


@pytest.mark.skipif(not tectonic_available(), reason="tectonic missing")
@pytest.mark.parametrize("cls", TEMPLATE_CHOICES)
def test_every_class_compiles_without_errors(cls, tmp_path):
    result = compile_tex(_tex(cls), tmp_path)
    assert result.ok, result.error
    errors = re.findall(r"^error:.*", result.log, re.M)
    assert not errors, errors[:5]
