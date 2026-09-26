"""Structured math model: typing behaviour, editing operations and the
LaTeX parser/serializer round trip."""
import re

import pytest

from khervedoc import equations, mathbox as mb
from khervedoc.mathbox import (
    Atom, BigOp, Delim, Editor, Frac, Func, Matrix, PLACEHOLDER, Raw, Row,
    Scripts, Sqrt, Symbol, parse_latex, to_latex,
)


def typed(text: str) -> Editor:
    e = Editor()
    e.type_text(text)
    return e


def _norm(s: str) -> str:
    s = mb.normalize_template(s)
    s = s.replace(r"\{", "LBR").replace(r"\}", "RBR")
    s = re.sub(r"\\(left|right)(?![A-Za-z])", "", s)
    s = re.sub(r"\s+", "", s)
    return s.replace("{", "").replace("}", "")


def _raws(row):
    return [n for r in mb.walk_rows(row) for n in r.children
            if isinstance(n, Raw)]


# ------------------------------------------------------------- typing

def test_typing_script_then_fraction():
    e = typed("x^2")
    e.move_right()            # leave the superscript
    e.type_text("+1/y")
    assert e.latex() == r"x^2 + \frac{1}{y}"


def test_slash_wraps_preceding_operand():
    assert typed("2x/3").latex() == r"\frac{2x}{3}"
    # a bracketed numerator loses its now-redundant parentheses
    e = typed("(a+b")
    e.type_char(")")
    e.type_text("/c")
    assert e.latex() == r"\frac{a + b}{c}"


def test_slash_with_nothing_before_starts_empty_fraction():
    e = typed("/")
    f = e.root.children[0]
    assert isinstance(f, Frac) and e.row is f.num


def test_backslash_command_becomes_symbol_or_structure():
    e = typed("\\alpha ")
    assert isinstance(e.root.children[0], Symbol)
    e = typed("\\sqrt x")
    assert e.latex() == r"\sqrt{x}"
    e = typed("\\frac ")
    assert isinstance(e.root.children[0], Frac)


def test_command_completion_choice():
    e = typed("\\alp")
    assert mb.completions("alp")[0][0] == "alpha"
    e.commit_cmd("alpha")
    assert e.latex() == r"\alpha"


def test_function_names_are_recognised():
    e = typed("sinx")
    assert isinstance(e.root.children[0], Func)
    assert e.latex() == r"\sin x"
    e = typed("sinh")
    assert [type(n) for n in e.root.children] == [Func]
    assert e.root.children[0].name == "sinh"
    assert typed("arccos").latex() == r"\arccos"


def test_lim_becomes_limit_with_lower_slot():
    e = typed("lim")
    op = e.root.children[0]
    assert isinstance(op, BigOp) and e.row is op.lower
    e.type_text("x->0")
    e.move_right()
    e.type_text("f")
    assert e.latex() == r"\lim_{x \to 0} f"


def test_autocorrect_pairs():
    assert typed("a<=b").latex() == r"a \leq b"
    assert typed("a!=b").latex() == r"a \neq b"
    assert typed("x+-1").latex() == r"x \pm 1"


def test_brackets_and_closing():
    e = typed("f(x")
    e.type_char(")")
    e.type_text("=1")
    assert e.latex() == "f(x) = 1"
    assert isinstance(e.root.children[1], Delim)


def test_tall_brackets_use_left_right():
    e = typed("(")
    e.type_text("1/2")
    assert e.latex() == r"\left( \frac{1}{2} \right)"


def test_subscript_and_superscript_share_a_node():
    e = typed("x_i")
    e.move_right()
    e.type_char("^")
    e.type_char("2")
    assert e.latex() == "x_i^2"
    assert sum(isinstance(n, Scripts) for n in e.root.children) == 1


def test_text_inside_text_keeps_spaces():
    e = typed("\\text ")
    e.type_text("if x")
    assert e.latex() == r"\text{if x}"


# ------------------------------------------------------------ editing

def test_backspace_at_slot_start_unwraps_structure():
    e = typed("a/b")
    e.move_left()             # to start of denominator
    assert e.row is e.root.children[0].den and e.idx == 0
    e.backspace()
    assert e.latex() == "ab"
    assert e.row is e.root and e.idx == 1


def test_backspace_enters_structure_then_deletes():
    e = typed("\\sqrt x")
    e.move_right()            # out of the root
    e.backspace()             # steps inside
    assert e.row is e.root.children[0].body
    e.backspace()
    e.backspace()             # empty root dissolves
    assert e.latex() == ""


def test_undo_redo():
    e = typed("ab")
    e.undo()
    assert e.latex() == "a"
    e.redo()
    assert e.latex() == "ab"


def test_template_wraps_selection():
    e = typed("x+1")
    e.select_all()
    e.insert_latex(r"\sqrt{\square}")
    assert e.latex() == r"\sqrt{x + 1}"
    e = typed("y")
    e.select_all()
    e.insert_latex(r"\frac{\square}{\square}")
    assert e.latex() == r"\frac{y}{}"
    assert e.row is e.root.children[0].den


def test_template_caret_goes_to_first_slot_and_tab_cycles():
    e = Editor()
    e.insert_latex(r"\int_{\square}^{\square} \square \, d\square")
    op = e.root.children[0]
    assert e.row is op.lower
    e.type_char("0")
    e.next_slot()
    assert e.row is op.upper
    e.type_char("1")
    e.next_slot()
    e.type_char("f")
    e.next_slot()
    e.type_char("x")
    assert e.latex() == r"\int_0^1 f\, dx"
    assert mb.count_empty(e.root) == 0


def test_typing_replaces_placeholder():
    e = Editor()
    e.insert_latex(r"\square = \square")
    e.type_char("a")
    assert e.latex(PLACEHOLDER) == r"a = \square"


def test_selection_lifts_to_common_row():
    e = typed("a+b/c")
    frac = e.root.children[-1]
    e.set_selection(e.root, 0, frac.den, 1)
    assert e.row is e.root
    assert e.selection() == (e.root, 0, 3)
    assert e.selection_latex() == r"a + \frac{b}{c}"


def test_vertical_movement_in_fraction():
    e = typed("a/b")
    f = e.root.children[0]
    e.move_vertical(up=True)
    assert e.row is f.num
    e.move_vertical(up=False)
    assert e.row is f.den


def test_matrix_add_row():
    e = Editor()
    e.insert_latex(r"\begin{pmatrix}\square&\square\\\square&\square"
                   r"\end{pmatrix}")
    m = e.root.children[0]
    assert e.matrix_add_row()
    assert len(m.rows) == 3 and e.row is m.rows[1][0]


def test_paste_latex():
    e = typed("y=")
    e.paste_latex(r"\frac{1}{2}")
    assert e.latex() == r"y = \frac{1}{2}"


# ------------------------------------------------------- parse/serialise

def test_parse_structures():
    r = parse_latex(r"\frac{a}{b} + \sqrt[3]{x} + x_1^2")
    kinds = [type(n) for n in r.children]
    assert kinds == [Frac, Atom, Sqrt, Atom, Atom, Scripts]
    assert r.children[2].index is not None


def test_empty_slots_serialise_as_braces_for_the_document():
    r = parse_latex(r"\frac{\square}{\square}")
    assert to_latex(r) == r"\frac{}{}"
    assert to_latex(r, PLACEHOLDER) == r"\frac{\square}{\square}"


def test_bigop_limits_attach():
    r = parse_latex(r"\sum_{i=1}^{n} i")
    op = r.children[0]
    assert isinstance(op, BigOp)
    assert to_latex(op.lower) == "i = 1"
    assert to_latex(r) == r"\sum_{i=1}^n i"


def test_environments_parse_to_matrix():
    r = parse_latex(r"\begin{cases} x & y \\ z & w \end{cases}")
    m = r.children[0]
    assert isinstance(m, Matrix) and m.env == "cases"
    assert len(m.rows) == 2 and len(m.rows[0]) == 2


def test_unknown_constructs_are_kept_verbatim():
    src = r"\ce{2H2 + O2 -> 2H2O} + \foo[1]{a}{b}"
    r = parse_latex(src)
    assert [n.latex for n in _raws(r)] == [r"\ce{2H2 + O2 -> 2H2O}",
                                           r"\foo[1]{a}{b}"]
    assert to_latex(r) == src


def test_parser_never_raises_on_garbage():
    for s in ("}{", r"\frac{", r"\left(", "x^", r"\begin{pmatrix} a",
              r"\sqrt[", "&&", r"\\", "a_b_c", "(((", "]]"):
        to_latex(parse_latex(s))


@pytest.mark.parametrize("tpl", [t for _, items in equations.EQUATION_GROUPS
                                 for t, _ in items])
def test_every_template_round_trips(tpl):
    row = parse_latex(tpl)
    assert not _raws(row), tpl
    once = to_latex(row, PLACEHOLDER)
    assert to_latex(parse_latex(once), PLACEHOLDER) == once
    assert _norm(once) == _norm(tpl)


CORPUS = [
    r"E = mc^2",
    r"F = G\frac{m_1 m_2}{r^2}",
    r"\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}",
    r"\nabla \times \mathbf{B} = \mu_0 \mathbf{J} + \mu_0\varepsilon_0"
    r" \frac{\partial \mathbf{E}}{\partial t}",
    r"i\hbar\frac{\partial}{\partial t}\Psi = \hat{H}\Psi",
    r"\Delta G = \Delta H - T\Delta S",
    r"K_{eq} = \frac{[\mathrm{C}]^c[\mathrm{D}]^d}"
    r"{[\mathrm{A}]^a[\mathrm{B}]^b}",
    r"pH = -\log_{10}[\mathrm{H}^+]",
    r"k = A e^{-E_a/RT}",
    r"\langle x \rangle = \int_{-\infty}^{\infty} x |\psi(x)|^2 \, dx",
    r"e^{i\pi} + 1 = 0",
    r"\sum_{k=0}^{n} \binom{n}{k} x^k y^{n-k}",
    r"\lim_{x \to 0} \frac{\sin x}{x} = 1",
    r"\sqrt[n]{a} \cdot \overline{z}",
    r"\left\{ x \in \mathbb{R} : x > 0 \right\}",
    r"f'(x) = \lim_{h\to 0}\frac{f(x+h)-f(x)}{h}",
    r"\begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}",
    r"\begin{aligned} a &= b + c \\ &= d \end{aligned}",
    r"PV = nRT",
    r"\text{rate} = k[\mathrm{A}]^m[\mathrm{B}]^n",
    r"\frac{d[\mathrm{A}]}{dt} = -k[\mathrm{A}]",
    r"S = k_B \ln \Omega",
    r"\oint_C \mathbf{F} \cdot d\mathbf{r}",
    r"\hat{a}\,\vec{v}\,\dot{x}\,\ddot{y}\,\tilde{n}",
    r"\operatorname{Tr}(A) = \sum_i A_{ii}",
    r"x_{i,j}^{(n)}",
    r"\left| \frac{a}{b} \right| \leq 1",
    r"\frac{1}{2}mv^2 + \frac{1}{2}kx^2 = E",
    r"\sigma = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(x_i - \mu)^2}",
    r"\mathrm{d}U = T\,\mathrm{d}S - p\,\mathrm{d}V",
]


@pytest.mark.parametrize("src", CORPUS)
def test_corpus_round_trips(src):
    row = parse_latex(src)
    assert not _raws(row), src
    once = to_latex(row)
    assert to_latex(parse_latex(once)) == once
    assert _norm(once) == _norm(src)
