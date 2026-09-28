"""The Visual tab and the LaTeX must describe the same document.

Each test types real keystrokes into the visual editor, then checks,
line by line, that the style the Visual tab shows (block state + fonts)
is the style the serializer writes, and that reloading the saved model
gives back the same LaTeX.
"""
from __future__ import annotations

import os
import random

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QTextCursor  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc.editor import (  # noqa: E402
    DocumentEditor, _HEADING_SCALE, _STATE_PARAGRAPH, _style_code,
)
from khervedoc.model import (  # noqa: E402
    Document, Paragraph, Section, Text, Title,
)
from khervedoc.serializer import serialize_document  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


def _make(qapp, children):
    e = DocumentEditor()
    e.set_document(Document(children=children))
    e.show()
    e._edit.setFocus()
    return e


@pytest.fixture
def ed(qapp):
    e = _make(qapp, [
        Section(level=1, children=[Text(text="Intro")]),
        Paragraph(children=[Text(text="First para")]),
        Section(level=2, children=[Text(text="Details")]),
        Paragraph(children=[Text(text="Second para")]),
    ])
    yield e
    e.close()


# ------------------------------------------------------------ helpers

def _blocks(ed):
    b = ed._edit.document().begin()
    while b.isValid():
        yield b
        b = b.next()


def _body_pt(ed):
    zoom = ed._zoom_percent / 100 if ed._zoom_percent else 1.0
    return ed._body_font_pt * zoom


def _expected_pt(ed, code):
    if code == 0:
        return _body_pt(ed)
    if code >= 1:
        return ed._heading_fmt(code).fontPointSize()
    return None                          # title etc.: own sizes, not checked


def _text_frags(block):
    it = block.begin()
    while not it.atEnd():
        f = it.fragment()
        if f.isValid() and not f.charFormat().isImageFormat() and f.text().strip():
            yield f
        it += 1


def _node_code(node):
    if isinstance(node, Section):
        return node.level
    if isinstance(node, Paragraph):
        return 0
    if isinstance(node, Title):
        return -1
    return None


def assert_parity(ed):
    """Every text line: styled, fonts match its style, and the model
    (hence the LaTeX) carries that same style, in the same order."""
    visual = []
    for b in _blocks(ed):
        if not b.text().strip():
            continue
        state = b.userState()
        code = _style_code(state)
        assert code is not None, f"line {b.text()!r} has no style ({state})"
        want = _expected_pt(ed, code)
        if want is not None:
            for f in _text_frags(b):
                got = f.charFormat().fontPointSize()
                assert abs(got - want) < 0.01, (
                    f"{b.text()!r}: style {code} but {f.text()!r} is {got}pt, "
                    f"not {want}pt")
        visual.append((code, b.text()))

    doc = ed.get_document()
    model = [(_node_code(n), "".join(getattr(k, "text", "") for k in n.children))
             for n in doc.children if _node_code(n) is not None
             and "".join(getattr(k, "text", "") for k in n.children).strip()]
    assert [c for c, _ in model] == [c for c, _ in visual], (visual, model)
    assert [t for _, t in model] == [t for _, t in visual]

    latex = serialize_document(doc)
    ed2 = DocumentEditor()
    ed2.set_document(doc)
    assert serialize_document(ed2.get_document()) == latex
    ed2.close()


def _caret_style_matches_block(ed):
    c = ed._edit.textCursor()
    code = _style_code(c.block().userState())
    want = _expected_pt(ed, code)
    if want is not None:
        assert abs(ed._edit.currentCharFormat().fontPointSize() - want) < 0.01


def _goto(ed, text, where="end"):
    for b in _blocks(ed):
        if b.text() == text:
            c = QTextCursor(b)
            if where == "end":
                c.movePosition(QTextCursor.EndOfBlock)
            elif isinstance(where, int):
                c.setPosition(b.position() + where)
            ed._edit.setTextCursor(c)
            return b
    raise AssertionError(f"no line {text!r}")


def _state_of(ed, text):
    for b in _blocks(ed):
        if b.text() == text:
            return b.userState()
    raise AssertionError(f"no line {text!r}")


def key(ed, k, mod=Qt.NoModifier, n=1):
    for _ in range(n):
        QTest.keyClick(ed._edit, k, mod)


def type_(ed, text):
    QTest.keyClicks(ed._edit, text)


def _latex_body(ed):
    s = serialize_document(ed.get_document())
    return s[s.index("\\begin{document}"):]


# ------------------------------------------------------------ Enter

def test_starting_document_is_consistent(ed):
    assert_parity(ed)


def test_enter_at_end_of_heading_starts_body_text(ed):
    _goto(ed, "Intro")
    key(ed, Qt.Key_Return)
    _caret_style_matches_block(ed)
    type_(ed, "new body")
    assert _state_of(ed, "new body") == _STATE_PARAGRAPH
    assert "\\section{new body}" not in _latex_body(ed)
    assert_parity(ed)


def test_enter_at_end_of_heading_caret_is_not_bold(ed):
    _goto(ed, "Intro")
    key(ed, Qt.Key_Return)
    assert not ed._edit.currentCharFormat().font().bold()


def test_enter_inside_heading_splits_into_two_headings(ed):
    _goto(ed, "Intro", 2)
    key(ed, Qt.Key_Return)
    assert _state_of(ed, "In") == 1 and _state_of(ed, "tro") == 1
    assert_parity(ed)


def test_enter_at_start_of_heading_keeps_the_heading(ed):
    _goto(ed, "Details", 0)
    key(ed, Qt.Key_Return)
    assert _state_of(ed, "Details") == 2
    assert_parity(ed)


def test_enter_in_paragraph_keeps_paragraphs(ed):
    _goto(ed, "First para", 5)
    key(ed, Qt.Key_Return)
    assert _state_of(ed, "First") == _STATE_PARAGRAPH
    assert _state_of(ed, " para") == _STATE_PARAGRAPH
    assert_parity(ed)


def test_two_enters_after_heading_then_type(ed):
    _goto(ed, "Details")
    key(ed, Qt.Key_Return, n=2)
    type_(ed, "after blank")
    assert _state_of(ed, "after blank") == _STATE_PARAGRAPH
    assert_parity(ed)


def test_shift_enter_is_a_line_break_not_a_new_line_style(ed):
    _goto(ed, "Intro")
    key(ed, Qt.Key_Return, Qt.ShiftModifier)
    type_(ed, "more")
    assert_parity(ed)


def test_enter_after_starred_heading_is_body(ed):
    _goto(ed, "Intro")
    ed.toggle_heading_numbered(False)
    key(ed, Qt.Key_Return)
    type_(ed, "plain")
    assert _state_of(ed, "plain") == _STATE_PARAGRAPH
    assert "\\section*{Intro}" in _latex_body(ed)
    assert_parity(ed)


def test_enter_inside_starred_heading_keeps_it_starred(ed):
    _goto(ed, "Intro")
    ed.toggle_heading_numbered(False)
    _goto(ed, "Intro", 2)
    key(ed, Qt.Key_Return)
    assert _state_of(ed, "tro") == _state_of(ed, "In")
    assert "\\section*{tro}" in _latex_body(ed)


def test_bold_word_in_paragraph_survives_enter(qapp):
    from khervedoc.model import Paragraph as P
    e = _make(qapp, [P(children=[Text(text="plain "),
                                  Text(text="bold", marks=["bold"]),
                                  Text(text=" end")])])
    try:
        _goto(e, "plain bold end")
        key(e, Qt.Key_Return)
        type_(e, "next")
        assert "\\textbf{bold}" in _latex_body(e)
        assert_parity(e)
    finally:
        e.close()


# ------------------------------------------------------------ Backspace / Delete

def test_backspace_on_empty_line_after_heading_keeps_heading(ed):
    _goto(ed, "Intro")
    key(ed, Qt.Key_Return)
    key(ed, Qt.Key_Backspace)
    assert _state_of(ed, "Intro") == 1
    _caret_style_matches_block(ed)
    type_(ed, "X")
    assert _state_of(ed, "IntroX") == 1
    assert "\\section{IntroX}" in _latex_body(ed)
    assert_parity(ed)


def test_deleting_a_paragraph_back_into_the_heading_keeps_heading(ed):
    b = _goto(ed, "First para")
    key(ed, Qt.Key_Backspace, n=len("First para") + 1)
    assert _state_of(ed, "Intro") == 1
    assert "\\section{Intro}" in _latex_body(ed)
    assert_parity(ed)


def test_backspace_joining_body_into_heading_makes_it_heading_text(ed):
    _goto(ed, "First para", 0)
    key(ed, Qt.Key_Backspace)
    assert _state_of(ed, "IntroFirst para") == 1
    assert_parity(ed)


def test_backspace_joining_heading_into_body_makes_it_body_text(ed):
    _goto(ed, "Details", 0)
    key(ed, Qt.Key_Backspace)
    assert _state_of(ed, "First paraDetails") == _STATE_PARAGRAPH
    assert "\\subsection" not in _latex_body(ed)
    assert_parity(ed)


def test_delete_at_end_of_heading_keeps_heading(ed):
    _goto(ed, "Intro")
    key(ed, Qt.Key_Delete)
    assert _state_of(ed, "IntroFirst para") == 1
    assert_parity(ed)


def test_backspace_inside_a_heading_keeps_heading(ed):
    _goto(ed, "Intro")
    key(ed, Qt.Key_Backspace, n=3)
    assert _state_of(ed, "In") == 1
    assert_parity(ed)


def test_selection_across_heading_and_body_deleted(ed):
    b = _goto(ed, "Intro", 2)
    c = ed._edit.textCursor()
    target = next(x for x in _blocks(ed) if x.text() == "First para")
    c.setPosition(target.position() + 5, QTextCursor.KeepAnchor)
    ed._edit.setTextCursor(c)
    key(ed, Qt.Key_Backspace)
    assert _state_of(ed, "In para") == 1
    assert_parity(ed)


def test_merging_two_paragraphs_keeps_bold(qapp):
    e = _make(qapp, [Paragraph(children=[Text(text="a "),
                                          Text(text="B", marks=["bold"])]),
                     Paragraph(children=[Text(text="c")])])
    try:
        _goto(e, "c", 0)
        key(e, Qt.Key_Backspace)
        assert "\\textbf{B}" in _latex_body(e)
        assert_parity(e)
    finally:
        e.close()


def test_heading_deleted_to_empty_then_retyped(ed):
    _goto(ed, "Details")
    key(ed, Qt.Key_Backspace, n=len("Details"))
    type_(ed, "Redone")
    assert _state_of(ed, "Redone") == 2
    assert "\\subsection{Redone}" in _latex_body(ed)
    assert_parity(ed)


# ------------------------------------------------------------ style changes

@pytest.mark.parametrize("level", [1, 2, 3])
def test_heading_on_empty_line_then_type(ed, level):
    _goto(ed, "Second para")
    key(ed, Qt.Key_Return)
    ed.apply_heading(level)
    _caret_style_matches_block(ed)
    type_(ed, "Fresh")
    assert _state_of(ed, "Fresh") == level
    assert_parity(ed)


def test_heading_back_to_body(ed):
    _goto(ed, "Intro")
    ed.apply_heading(0)
    assert "\\section{Intro}" not in _latex_body(ed)
    assert_parity(ed)


def test_body_to_heading_and_enter(ed):
    _goto(ed, "Second para")
    ed.apply_heading(1)
    key(ed, Qt.Key_Return)
    type_(ed, "tail")
    assert _state_of(ed, "tail") == _STATE_PARAGRAPH
    assert "\\section{Second para}" in _latex_body(ed)
    assert_parity(ed)


def test_title_enter_gives_body(qapp):
    e = _make(qapp, [Title(children=[Text(text="My title")]),
                     Paragraph(children=[Text(text="p")])])
    try:
        _goto(e, "My title")
        key(e, Qt.Key_Return)
        type_(e, "after")
        assert _state_of(e, "after") == _STATE_PARAGRAPH
        assert_parity(e)
    finally:
        e.close()


# ------------------------------------------------------------ fuzz

_ACTIONS = ["type", "enter", "backspace", "delete", "h0", "h1", "h2",
            "left", "right", "up", "down", "home", "end", "undo", "redo"]


@pytest.mark.parametrize("seed", range(20))
def test_random_editing_never_desyncs(qapp, seed):
    rng = random.Random(seed)
    e = _make(qapp, [
        Section(level=1, children=[Text(text="Alpha")]),
        Paragraph(children=[Text(text="beta gamma")]),
        Section(level=2, children=[Text(text="Delta")]),
        Paragraph(children=[Text(text="epsilon")]),
    ])
    try:
        for step in range(40):
            a = rng.choice(_ACTIONS)
            if a == "type":
                type_(e, rng.choice(["x", "yz", "w "]))
            elif a == "enter":
                key(e, Qt.Key_Return)
            elif a == "backspace":
                key(e, Qt.Key_Backspace)
            elif a == "delete":
                key(e, Qt.Key_Delete)
            elif a == "undo":
                e._edit.undo()
            elif a == "redo":
                e._edit.redo()
            elif a in ("h0", "h1", "h2"):
                e.apply_heading(int(a[1]))
            else:
                key(e, {"left": Qt.Key_Left, "right": Qt.Key_Right,
                        "up": Qt.Key_Up, "down": Qt.Key_Down,
                        "home": Qt.Key_Home, "end": Qt.Key_End}[a])
            try:
                assert_parity(e)
            except AssertionError as ex:
                raise AssertionError(f"seed {seed} step {step} ({a}): {ex}")
    finally:
        e.close()


# ------------------------------------------------------------ hover guard

def test_mouse_past_end_of_text_does_not_warn(ed, capfd):
    from PySide6.QtCore import QPointF
    edit = ed._edit
    for y in (5000, 10000):
        assert edit._image_under(QPointF(10, y)) is None
    assert "out of range" not in capfd.readouterr().err


# ------------------------------------------------------------ undo

@pytest.mark.parametrize("keys", [
    [Qt.Key_Return],
    [Qt.Key_Backspace],
])
def test_undo_restores_a_consistent_document(ed, keys):
    before = _latex_body(ed)
    _goto(ed, "First para", 0)
    for k in keys:
        key(ed, k)
    ed._edit.undo()
    assert_parity(ed)
    assert _latex_body(ed) == before
