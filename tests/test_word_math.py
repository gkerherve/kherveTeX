"""Equations pasted from Word as Unicode text, converted back to LaTeX."""
import os

import pytest

from khervedoc.word_math import convert


def test_users_example_with_number():
    latex, number = convert("Ln = −⟨P⟩hi,     Rn = −⟨P⟩lo\t\t(2)")
    assert number == "2"
    assert latex == (r"L_{n} = -\langle P\rangle _{\text{hi}},\qquad "
                     r"R_{n} = -\langle P\rangle _{\text{lo}}")


@pytest.mark.parametrize("text,expected", [
    ("E = mc²", "E = mc^{2}"),
    ("ΔG = −nFE", r"\Delta G = -nFE"),
    ("sin θ ≤ 1", r"\sin \theta \le 1"),
    ("x₁ + x₂ = 3", "x_{1} + x_{2} = 3"),
    ("Emax = ħω/2", r"E_{\text{max}} = \hbar \omega /2"),
])
def test_symbols_scripts_and_functions(text, expected):
    assert convert(text) == (expected, None)


def test_selection_becomes_numbered_display_equation():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QTextCursor
    from khervedoc.editor import DocumentEditor
    from khervedoc.model import (
        DocMeta, Document, MathBlock, MathInline, Paragraph, Text)
    QApplication.instance() or QApplication([])

    e = DocumentEditor()
    e.set_document(Document(meta=DocMeta(), children=[
        Paragraph(children=[Text("Before")]),
        Paragraph(children=[Text("E = mc²")]),
        Paragraph(children=[Text("where c is light speed")])]))
    c = QTextCursor(e._edit.document().findBlockByNumber(1))
    c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
    e._edit.setTextCursor(c)
    e.replace_selection_with_math("E = mc^{2}", numbered=True)
    kids = e.get_document().children
    maths = [b for b in kids if isinstance(b, MathBlock)]
    assert len(maths) == 1 and maths[0].latex == "E = mc^{2}"
    assert maths[0].numbered

    # A few words inside a sentence become inline math instead.
    last = e._edit.document().lastBlock()
    while not last.text().startswith("where"):
        last = last.previous()
    c = QTextCursor(last)
    c.setPosition(last.position() + 6)
    c.setPosition(last.position() + 7, QTextCursor.KeepAnchor)
    e._edit.setTextCursor(c)
    e.replace_selection_with_math("c", numbered=False)
    para = [b for b in e.get_document().children
            if isinstance(b, Paragraph) and any(
                isinstance(i, MathInline) for i in b.children)]
    assert para
