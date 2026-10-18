"""Every document class the toolbar offers must compile the editor's blocks."""
import re

import pytest

from khervedoc.compiler import (
    compile_tex, tectonic_available, template_sample_document,
)
from khervedoc.editor import TEMPLATE_CHOICES
from khervedoc.serializer import serialize_document

# Publisher classes that are neither in tectonic's bundle nor
# redistributable with KherveTeX: the user adds them via Manage styles.
_NOT_BUNDLED = {"aa", "svjour3"}


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


@pytest.mark.skipif(not tectonic_available(), reason="tectonic missing")
@pytest.mark.parametrize(
    "cls", [c for c in TEMPLATE_CHOICES if c not in _NOT_BUNDLED])
def test_every_class_compiles_without_errors(cls, tmp_path):
    result = compile_tex(_tex(cls), tmp_path)
    assert result.ok, result.error
    errors = re.findall(r"^error:.*", result.log, re.M)
    assert not errors, errors[:5]
