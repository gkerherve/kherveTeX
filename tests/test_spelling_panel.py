"""The Spelling panel: every spelling mistake of the document in a list,
to go to each one and fix it, ignore it or add it to the dictionary.
Nothing is corrected until the user says so."""

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc import spellcheck  # noqa: E402
from khervedoc.model import (  # noqa: E402
    Document, MathBlock, Paragraph, Section, Text,
)

pytestmark = pytest.mark.skipif(not spellcheck.is_available(),
                                reason="pyspellchecker not installed")


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


def _doc():
    return Document(children=[
        Section(level=1, children=[Text("Introduction")]),
        Paragraph(children=[Text("The quick brwon fox jumps over the lazy dog.")]),
        MathBlock(latex=r"\alpha + \betaa = \gammma"),
        Paragraph(children=[Text("Another brwon dog, and a mistkae here.")]),
    ])


@pytest.fixture
def panel(qapp):
    from khervedoc.editor import DocumentEditor
    from khervedoc.spelling_panel import SpellingPanel
    ed = DocumentEditor()
    ed.set_document(_doc())
    p = SpellingPanel(ed)
    p.refresh()
    yield p
    p.deleteLater()
    ed.deleteLater()


def _texts(panel):
    doc = panel._editor.get_document()
    return ["".join(c.text for c in b.children) for b in doc.children
            if isinstance(b, Paragraph)]


def test_context_around_cuts_at_a_word():
    text = "one two three four five six seven eight nine ten eleven twelve"
    a = text.index("seven")
    before, after = spellcheck.context_around(text, a, a + 5, width=12)
    assert before == "…five six "
    assert after == " eight nine…"
    assert spellcheck.context_around("a brwon b", 2, 7) == ("a ", " b")


def test_every_mistake_is_listed_in_order(panel):
    assert [m["word"] for m in panel.items()] == ["brwon", "brwon", "mistkae"]
    m = panel.items()[0]
    assert m["before"] == "The quick " and m["after"].startswith(" fox jumps")
    assert panel._summary.text() == "3 spelling mistakes"
    # Equations are not prose.
    assert all("gamm" not in m["word"] for m in panel.items())


def test_listed_with_the_underline_off(panel):
    panel._editor.set_spell_check_enabled(False)
    panel.refresh()
    assert len(panel.items()) == 3


def test_click_goes_to_the_mistake(panel):
    panel.select(2)
    cur = panel._editor.text_edit.textCursor()
    assert cur.selectedText() == "mistkae"


def test_nothing_changes_until_the_user_confirms(panel):
    panel.select(0)
    assert _texts(panel)[0] == "The quick brwon fox jumps over the lazy dog."


def test_change_fixes_one_and_shows_the_next(panel):
    panel.select(0, "brown")
    panel.change()
    assert _texts(panel)[0] == "The quick brown fox jumps over the lazy dog."
    assert _texts(panel)[1] == "Another brwon dog, and a mistkae here."
    assert [m["word"] for m in panel.items()] == ["brwon", "mistkae"]
    assert panel.current_index() == 0
    assert panel._editor.text_edit.textCursor().selectedText() == "brwon"


def test_change_all(panel):
    panel.select(1, "brown")
    panel.change_all()
    assert "brwon" not in " ".join(_texts(panel))
    assert [m["word"] for m in panel.items()] == ["mistkae"]


def test_ignore_one_and_ignore_all(panel):
    panel.select(0)
    panel.ignore()
    assert [m["word"] for m in panel.items()] == ["brwon", "mistkae"]
    assert panel.items()[0]["before"] == "Another "
    panel.select(1)
    panel.ignore_all()
    assert [m["word"] for m in panel.items()] == ["brwon"]
    assert _texts(panel)[1] == "Another brwon dog, and a mistkae here."


def test_add_to_dictionary_is_kept(panel):
    kept = []
    panel._editor.spell_highlighter.on_word_added = kept.append
    panel.select(2)
    panel.add_to_dictionary()
    assert kept == ["mistkae"]
    assert panel._editor.spell_highlighter.added_words() == ["mistkae"]
    assert [m["word"] for m in panel.items()] == ["brwon", "brwon"]


def test_no_mistakes(qapp):
    from khervedoc.editor import DocumentEditor
    from khervedoc.spelling_panel import SpellingPanel
    ed = DocumentEditor()
    ed.set_document(Document(children=[Paragraph(children=[Text("All good here.")])]))
    p = SpellingPanel(ed)
    p.refresh()
    assert p.items() == []
    assert p._summary.text() == "No spelling mistakes found."
    assert not p._change_btn.isEnabled()


def test_keeps_the_word_format(qapp):
    from khervedoc.editor import DocumentEditor
    from khervedoc.spelling_panel import SpellingPanel
    ed = DocumentEditor()
    ed.set_document(Document(children=[Paragraph(children=[
        Text("A "), Text("brwon", ["bold"]), Text(" fox.")])]))
    p = SpellingPanel(ed)
    p.refresh()
    p.select(0, "brown")
    p.change()
    para = ed.get_document().children[0]
    assert [(c.text, c.marks) for c in para.children] == [
        ("A ", []), ("brown", ["bold"]), (" fox.", [])]


def test_window_has_the_panel(qapp, monkeypatch):
    from khervedoc.mainwindow import MainWindow
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)
    w = MainWindow()
    try:
        # Not saved in the user's settings from a test.
        w._editor.spell_highlighter.on_word_added = None
        assert w._spelling_dock.isHidden()
        assert w.act_spelling_list.shortcut().toString() == "F7"
        w._editor.set_document(_doc())
        w.act_spelling_list.trigger()
        assert not w._spelling_dock.isHidden()
        assert [m["word"] for m in w._spelling_panel.items()] == ["brwon", "brwon", "mistkae"]
    finally:
        w.close()
