"""Text-symbol commands (\\AA, \\ss, \\o, \\textdegree...) import as the
characters they print, not as raw LaTeX."""

from khervedoc.importers import import_body_fragment
from khervedoc.model import InlineRaw, Text


def _text(latex):
    para = import_body_fragment(latex)[0]
    assert not [c for c in para.children if isinstance(c, InlineRaw)]
    return "".join(c.text for c in para.children if isinstance(c, Text))


def test_angstrom_with_empty_group():
    assert _text("close to 5 \\AA{} thickness") == "close to 5 Å thickness"


def test_space_after_command_word_is_swallowed():
    assert _text("Stra\\ss e") == "Straße"
    assert _text("10 \\textdegree C") == "10 °C"


def test_symbol_before_punctuation():
    assert _text("Bj\\o rn, \\O re and \\ae{}ther\\ldots.") == "Bjørn, Øre and æther…."


def test_symbol_inside_bold_keeps_the_mark():
    para = import_body_fragment("\\textbf{1 \\AA{}}")[0]
    assert [(c.text, c.marks) for c in para.children] == [("1 Å", ["bold"])]


def test_unknown_command_still_raw():
    para = import_body_fragment("\\Kstroke{} here")[0]
    assert isinstance(para.children[0], InlineRaw)


def test_accent_on_dotless_i():
    assert _text('na\\"{\\i}ve') == "naïve"
