"""A report/book .tex keeps its heading levels through import, and an
equation whose body opens with split/array keeps its equation."""

from khervedoc.importers import import_body_fragment, import_tex
from khervedoc.model import MathBlock, Section
from khervedoc.serializer import serialize_document

REPORT = r"""\documentclass{report}
\begin{document}
\chapter{Intro}
\section{Methods}
\subsection{Samples}
\subsubsection{Cleaning}
\paragraph{Annealing.} Text.
\end{document}
"""


def _levels(doc):
    return [(b.level, b.children[0].text) for b in doc.children
            if isinstance(b, Section)]


def test_report_sections_sit_one_level_below_chapter():
    doc = import_tex(REPORT)
    assert _levels(doc) == [(0, "Intro"), (2, "Methods"), (3, "Samples"),
                            (4, "Cleaning"), (5, "Annealing.")]


def test_report_headings_round_trip():
    out = serialize_document(import_tex(REPORT))
    for cmd in ("\\chapter{Intro}", "\\section{Methods}",
                "\\subsection{Samples}", "\\subsubsection{Cleaning}",
                "\\paragraph{Annealing.}"):
        assert cmd in out, cmd
    assert out.split("\\begin{document}")[1].count("\\chapter") == 1


def test_article_levels_unchanged():
    doc = import_tex(REPORT.replace("{report}", "{article}"))
    assert _levels(doc)[1:] == [(1, "Methods"), (2, "Samples"),
                                (3, "Cleaning"), (4, "Annealing.")]


def test_fragment_into_report_shifts_sections():
    blocks = import_body_fragment("\\section{A}\n\\subsection{B}",
                                  has_chapters=True)
    assert [b.level for b in blocks] == [2, 3]
    assert [b.level for b in import_body_fragment("\\section{A}")] == [1]


def _math(doc):
    return next(b for b in doc.children if isinstance(b, MathBlock))


def test_equation_with_split_keeps_its_equation():
    src = ("\\documentclass{article}\\begin{document}\n"
           "\\begin{equation}\\begin{split} a &= b \\\\ &= c \\end{split}"
           "\\label{eq:x}\\end{equation}\n\\end{document}")
    doc = import_tex(src)
    out = serialize_document(doc)
    body = out.split("\\begin{document}")[1]
    assert body.index("\\begin{equation}") < body.index("\\begin{split}")
    assert "\\label{eq:x}" in body


def test_display_array_keeps_its_math_delimiters():
    src = ("\\documentclass{article}\\begin{document}\n"
           "\\[ \\begin{array}{l} x \\\\ y \\end{array} \\]\n\\end{document}")
    out = serialize_document(import_tex(src))
    body = out.split("\\begin{document}")[1]
    assert "\\begin{equation*}" in body
    assert body.index("\\begin{equation*}") < body.index("\\begin{array}")


def test_align_still_emitted_verbatim():
    src = ("\\documentclass{article}\\begin{document}\n"
           "\\begin{align} a &= b \\end{align}\n\\end{document}")
    body = serialize_document(import_tex(src)).split("\\begin{document}")[1]
    assert "\\begin{align}" in body and "equation" not in body
