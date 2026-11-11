"""The Spelling panel: every spelling mistake of the document in a list.

It is not an autocorrector. The underline shows mistakes where they
are; this panel lists them all, so none is missed in a long document.
Click a mistake to go to it on the page (it is selected there), pick the
right spelling among the suggestions and press Change; or Ignore it,
Ignore all of that word, or Add it to the dictionary. Nothing changes
until the user confirms it, one mistake (or one word, Change all) at a
time. After each fix the next mistake is selected and shown.

The list follows the document: it is checked again a moment after each
edit while the panel is open. It lists the document in the editor (in a
project, the open document).
"""
from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPalette
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QStyle, QStyledItemDelegate, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from . import spellcheck

# The underline's red (spellcheck.SpellHighlighter).
_RED = "#d8000c"


def _key(m: dict) -> tuple[str, str, str]:
    """One mistake, as Ignore remembers it: the word and the text around
    it, which an edit elsewhere in the document leaves as it is."""
    return (m["word"], m["before"], m["after"])


# Where a row keeps its mistake, for the context column's painter.
_ROLE = Qt.UserRole + 1


class _ContextDelegate(QStyledItemDelegate):
    """The text around a mistake on one line with the word itself in
    red, kept in view: the text before is cut on its left and the text
    after on its right, so a long paragraph never hides the word."""

    def paint(self, painter, option, index):
        m = index.data(_ROLE)
        if not m:
            return super().paint(painter, option, index)
        self.initStyleOption(option, index)
        option.text = ""
        style = option.widget.style() if option.widget else None
        if style is not None:
            style.drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)
        # A selected row of the list with the focus is drawn in the
        # highlight colour; without the focus (the user went to the page)
        # macOS draws it light, so the normal colours stay readable.
        selected = bool(option.state & QStyle.State_Selected) \
            and option.widget is not None and option.widget.hasFocus()
        grey = option.palette.color(
            QPalette.HighlightedText if selected else QPalette.PlaceholderText)
        red = grey if selected else QColor(_RED)
        r = option.rect.adjusted(4, 0, -4, 0)
        font = QFont(option.font)
        bold = QFont(font)
        bold.setBold(True)
        fm, bfm = QFontMetrics(font), QFontMetrics(bold)
        word_w = bfm.horizontalAdvance(m["word"])
        room = max(0, r.width() - word_w)
        before_w = min(fm.horizontalAdvance(m["before"]), room * 2 // 5)
        before = fm.elidedText(m["before"], Qt.ElideLeft, before_w) if before_w else ""
        after = fm.elidedText(m["after"], Qt.ElideRight, room - fm.horizontalAdvance(before))
        painter.save()
        x = r.left()
        for text, f, colour in ((before, font, grey), (m["word"], bold, red),
                                (after, font, grey)):
            painter.setFont(f)
            painter.setPen(colour)
            w = QFontMetrics(f).horizontalAdvance(text)
            painter.drawText(QRect(x, r.top(), w + 1, r.height()),
                             Qt.AlignVCenter | Qt.AlignLeft, text)
            x += w
        painter.restore()


def summary(n: int) -> str:
    if n == 0:
        return "No spelling mistakes found."
    return f"{n} spelling mistake{'s' if n != 1 else ''}"


class SpellingPanel(QWidget):
    """The list of mistakes, the suggestions for the one selected, and
    the buttons that fix or skip it."""

    def __init__(self, editor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self._items: list[dict] = []
        # Mistakes the user ignored one by one (_key), this session.
        self._ignored: set[tuple[str, str, str]] = set()
        # While the list is rebuilt, selecting a row must not move the
        # page (the user may be typing).
        self._filling = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        top = QHBoxLayout()
        self._summary = QLabel(self)
        top.addWidget(self._summary, 1)
        self._recheck = QToolButton(self)
        self._recheck.setText("Check again")
        self._recheck.setToolTip("Check the whole document again")
        self._recheck.setAutoRaise(True)
        self._recheck.clicked.connect(self.refresh)
        top.addWidget(self._recheck)
        lay.addLayout(top)

        self._list = QTreeWidget(self)
        self._list.setColumnCount(2)
        self._list.setHeaderLabels(["Word", "In the text"])
        self._list.setRootIsDecorated(False)
        self._list.setUniformRowHeights(True)
        self._list.setAlternatingRowColors(True)
        self._list.setColumnWidth(0, 100)
        self._list.setItemDelegateForColumn(1, _ContextDelegate(self._list))
        self._list.setToolTip("Click a mistake to go to it in the document")
        self._list.currentItemChanged.connect(self._on_current)
        self._list.itemClicked.connect(lambda *_: self._go_to_current())
        lay.addWidget(self._list, 3)

        lay.addWidget(QLabel("Suggestions:", self))
        self._suggestions = QListWidget(self)
        self._suggestions.setToolTip("Double-click a suggestion to change the word to it")
        self._suggestions.itemDoubleClicked.connect(lambda *_: self.change())
        lay.addWidget(self._suggestions, 2)

        grid = QGridLayout()
        grid.setSpacing(4)
        self._change_btn = QPushButton("Change", self)
        self._change_btn.setToolTip("Change this mistake to the selected suggestion")
        self._change_btn.clicked.connect(self.change)
        self._change_all_btn = QPushButton("Change all", self)
        self._change_all_btn.setToolTip(
            "Change every place this word is spelled so to the selected suggestion")
        self._change_all_btn.clicked.connect(self.change_all)
        self._ignore_btn = QPushButton("Ignore", self)
        self._ignore_btn.setToolTip("Leave this one as it is")
        self._ignore_btn.clicked.connect(self.ignore)
        self._ignore_all_btn = QPushButton("Ignore all", self)
        self._ignore_all_btn.setToolTip("Leave this word everywhere, until KherveTeX closes")
        self._ignore_all_btn.clicked.connect(self.ignore_all)
        self._add_btn = QPushButton("Add to dictionary", self)
        self._add_btn.setToolTip("Never flag this word again")
        self._add_btn.clicked.connect(self.add_to_dictionary)
        grid.addWidget(self._change_btn, 0, 0)
        grid.addWidget(self._change_all_btn, 0, 1)
        grid.addWidget(self._ignore_btn, 1, 0)
        grid.addWidget(self._ignore_all_btn, 1, 1)
        grid.addWidget(self._add_btn, 2, 0, 1, 2)
        lay.addLayout(grid)
        self._buttons = [self._change_btn, self._change_all_btn,
                         self._ignore_btn, self._ignore_all_btn, self._add_btn]
        self._update_buttons()

    # ---- the list ------------------------------------------------------

    def items(self) -> list[dict]:
        """The mistakes listed, in document order."""
        return list(self._items)

    def current_index(self) -> int:
        item = self._list.currentItem()
        return self._list.indexOfTopLevelItem(item) if item is not None else -1

    def refresh(self, select: int | None = None, go: bool = False) -> None:
        """Check the document again. The row selected stays selected
        (the same mistake, else the one now in its place), or `select`;
        `go` shows it on the page."""
        keep = None
        if select is None:
            i = self.current_index()
            if 0 <= i < len(self._items):
                keep = _key(self._items[i])
                select = i
        if not spellcheck.is_available():
            self._items = []
        else:
            self._items = [m for m in self._editor.misspellings()
                           if _key(m) not in self._ignored]
        self._filling = True
        try:
            self._list.clear()
            bold = QFont(self._list.font())
            bold.setBold(True)
            for m in self._items:
                it = QTreeWidgetItem([m["word"], f"{m['before']}{m['word']}{m['after']}"])
                it.setForeground(0, QColor(_RED))
                it.setFont(0, bold)
                it.setToolTip(1, f"{m['before']}{m['word']}{m['after']}")
                it.setData(1, _ROLE, m)
                self._list.addTopLevelItem(it)
            row = -1
            if keep is not None:
                row = next((k for k, m in enumerate(self._items) if _key(m) == keep), -1)
            if row < 0 and select is not None and self._items:
                row = min(max(select, 0), len(self._items) - 1)
            if row >= 0:
                self._list.setCurrentItem(self._list.topLevelItem(row))
            else:
                self._fill_suggestions()
        finally:
            self._filling = False
        if not spellcheck.is_available():
            self._summary.setText("Install pyspellchecker to check spelling.")
        else:
            self._summary.setText(summary(len(self._items)))
        self._update_buttons()
        if go:
            self._go_to_current()

    def _on_current(self, *_):
        self._fill_suggestions()
        self._update_buttons()
        if not self._filling:
            self._go_to_current()

    def _go_to_current(self) -> None:
        i = self.current_index()
        if 0 <= i < len(self._items):
            m = self._items[i]
            self._editor.select_range(m["start"], m["end"])

    def _fill_suggestions(self) -> None:
        self._suggestions.clear()
        i = self.current_index()
        if not 0 <= i < len(self._items):
            return
        sugg = self._editor.spell_highlighter.suggestions(self._items[i]["word"])
        if not sugg:
            it = QListWidgetItem("(no suggestions)")
            it.setFlags(Qt.NoItemFlags)
            self._suggestions.addItem(it)
            return
        for s in sugg:
            self._suggestions.addItem(s)
        self._suggestions.setCurrentRow(0)

    def _update_buttons(self) -> None:
        has = 0 <= self.current_index() < len(self._items)
        for b in self._buttons:
            b.setEnabled(has)
        if has and self.chosen() is None:
            self._change_btn.setEnabled(False)
            self._change_all_btn.setEnabled(False)

    def chosen(self) -> str | None:
        """The suggestion selected (None when there is none)."""
        it = self._suggestions.currentItem()
        if it is None or not (it.flags() & Qt.ItemIsEnabled):
            return None
        return it.text()

    def select(self, index: int, suggestion: str | None = None) -> None:
        """Select the index-th mistake (and one of its suggestions), as a
        click does."""
        self._list.setCurrentItem(self._list.topLevelItem(index))
        if suggestion is not None:
            hits = self._suggestions.findItems(suggestion, Qt.MatchExactly)
            if hits:
                self._suggestions.setCurrentItem(hits[0])

    # ---- the buttons -----------------------------------------------------

    def change(self) -> None:
        """Change the selected mistake to the selected suggestion, then
        show the next mistake."""
        i = self.current_index()
        new = self.chosen()
        if not 0 <= i < len(self._items) or new is None:
            return
        m = self._items[i]
        self._editor.replace_range(m["start"], m["end"], m["word"], new)
        self._after_fix(i)

    def change_all(self) -> None:
        """Change every mistake spelled as the selected one."""
        i = self.current_index()
        new = self.chosen()
        if not 0 <= i < len(self._items) or new is None:
            return
        word = self._items[i]["word"]
        # From the end, so the earlier positions stay right.
        for m in reversed(self._items):
            if m["word"] == word:
                self._editor.replace_range(m["start"], m["end"], word, new)
        self._after_fix(i)

    def ignore(self) -> None:
        i = self.current_index()
        if not 0 <= i < len(self._items):
            return
        self._ignored.add(_key(self._items[i]))
        self._after_fix(i)

    def ignore_all(self) -> None:
        i = self.current_index()
        if not 0 <= i < len(self._items):
            return
        self._editor.spell_highlighter.ignore_word(self._items[i]["word"])
        self._after_fix(i)

    def add_to_dictionary(self) -> None:
        i = self.current_index()
        if not 0 <= i < len(self._items):
            return
        word = self._items[i]["word"]
        self._editor.spell_highlighter.add_to_dictionary(word)
        self._after_fix(i)

    def _after_fix(self, i: int) -> None:
        # The mistake at i is gone: the next one takes its row.
        self._list.setCurrentItem(None)
        self.refresh(select=i, go=True)
