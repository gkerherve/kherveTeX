"""Live spell checking for the WYSIWYG editor.

Wraps `pyspellchecker` behind a small QSyntaxHighlighter so each
QTextBlock in the editor is scanned on change and unknown English
words get a red wavy underline (Qt's standard
QTextCharFormat.SpellCheckUnderline).

Pure no-op if pyspellchecker isn't installed — the editor still
boots, the toggle in the View menu just gets disabled.
"""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor, QSyntaxHighlighter, QTextCharFormat,
)


try:
    from spellchecker import SpellChecker
    _AVAILABLE = True
except Exception:  # pragma: no cover — environments without pyspellchecker
    SpellChecker = None  # type: ignore
    _AVAILABLE = False


def is_available() -> bool:
    return _AVAILABLE


# Block userState values that should NOT be spell-checked: math envs,
# raw LaTeX, figure/table stubs are not English prose. Keep this in
# sync with editor._STATE_* but don't import editor to avoid a cycle.
_SKIP_STATES = {99, 100, 101, 102}  # math, figure, table, raw


# Words to skip: pure digits, single letters, anything with a digit,
# or anything containing a backslash (stray LaTeX text). Bracketing
# punctuation and apostrophes are stripped before lookup so contractions
# like "don't" still hit the dictionary.
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*[A-Za-z]|[A-Za-z]")


def _is_checkable(word: str) -> bool:
    """Worth-looking-up: at least three letters and alphabetic."""
    if len(word) < 3:
        return False
    return all(c.isalpha() or c in "'’-" for c in word)


# Characters of the paragraph shown on each side of a mistake in the
# Spelling panel.
CONTEXT_CHARS = 30


def context_around(text: str, start: int, end: int,
                   width: int = CONTEXT_CHARS) -> tuple[str, str]:
    """The text before and after text[start:end] in its paragraph, for
    the Spelling panel's list: at most `width` characters each side, cut
    at a word, whitespace runs shown as one space, an ellipsis where the
    paragraph goes on. Inline objects (U+FFFC) read as a space."""
    def tidy(s: str) -> str:
        return re.sub(r"\s+", " ", s.replace("\ufffc", " "))
    before = text[:start]
    after = text[end:]
    if len(before) > width:
        cut = before[-width:]
        sp = cut.find(" ")
        before = "…" + (cut[sp + 1:] if 0 <= sp < width - 1 else cut)
    if len(after) > width:
        cut = after[:width]
        sp = cut.rfind(" ")
        after = (cut[:sp] if sp > 0 else cut) + "…"
    return tidy(before).lstrip(), tidy(after).rstrip()


class SpellHighlighter(QSyntaxHighlighter):
    """Underline unknown English words in red as the user types.

    The dictionary is loaded lazily on the first highlight pass so
    construction stays cheap (pyspellchecker reads a ~600 KB
    frequency table the first time it's used).
    """

    def __init__(self, document) -> None:
        super().__init__(document)
        self._checker: SpellChecker | None = None
        self._enabled = _AVAILABLE
        # Cache: word (lowercased) -> True if unknown. Avoids re-doing
        # the dictionary lookup on every keystroke for stable text.
        self._unknown_cache: dict[str, bool] = {}

        self._fmt = QTextCharFormat()
        self._fmt.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        self._fmt.setUnderlineColor(QColor("#d8000c"))

        # User additions ("ignore this word in future") and runtime
        # custom dictionary entries land here so they're treated as
        # known. Kept lowercase.
        self._ignored: set[str] = set()
        # The words added to the dictionary (not those only ignored),
        # and who keeps them: MainWindow saves them in its settings.
        self._added: list[str] = []
        self.on_word_added = None

    # ---- public API ---------------------------------------------------

    def is_enabled(self) -> bool:
        return self._enabled and _AVAILABLE

    def set_enabled(self, enabled: bool) -> None:
        if enabled == self._enabled:
            return
        self._enabled = bool(enabled) and _AVAILABLE
        # Rehighlight everything so any existing red squiggles get
        # cleared (when turning off) or applied (when turning on).
        self.rehighlight()

    def add_to_dictionary(self, word: str) -> None:
        """Mark `word` as known: "Add to dictionary" in the right-click
        menu and the Spelling panel. The window keeps the user's words
        (on_word_added) so they stay known in later sessions."""
        if not word:
            return
        self.ignore_word(word)
        key = word.lower()
        if key not in self._added:
            self._added.append(key)
            if self.on_word_added is not None:
                self.on_word_added(key)

    def ignore_word(self, word: str) -> None:
        """Stop flagging `word` for the rest of this session (the
        Spelling panel's Ignore all)."""
        if not word:
            return
        self._ignored.add(word.lower())
        # Invalidate the unknown-cache entry so it isn't re-flagged
        # by the very next highlight pass.
        self._unknown_cache.pop(word.lower(), None)
        self.rehighlight()

    def load_dictionary(self, words) -> None:
        """The user's own words, kept from earlier sessions."""
        for w in words:
            if w and w.lower() not in self._added:
                self._added.append(w.lower())
                self._ignored.add(w.lower())
        self._unknown_cache.clear()
        self.rehighlight()

    def added_words(self) -> list[str]:
        """The words the user added to the dictionary, in order."""
        return list(self._added)

    def is_misspelled(self, word: str) -> bool:
        """True if `word` looks like a checkable English word that the
        dictionary doesn't know. Used by the editor's context menu to
        decide whether to offer suggestion actions on right-click."""
        if not self._enabled or not _AVAILABLE or not word:
            return False
        if not _is_checkable(word):
            return False
        key = word.lower().strip("’'’")
        if not key or key in self._ignored:
            return False
        cached = self._unknown_cache.get(key)
        if cached is None:
            if self._checker is None:
                self._checker = SpellChecker()
            cached = bool(self._checker.unknown([key]))
            self._unknown_cache[key] = cached
        return cached

    def suggestions(self, word: str, limit: int = 7) -> list[str]:
        """Top correction suggestions for `word`, ordered by
        pyspellchecker's confidence. Empty list if the dictionary has
        nothing — happens for very long nonsense strings."""
        # Only the dictionary is needed: the Spelling panel lists
        # mistakes with the underline turned off too.
        if not _AVAILABLE or not word:
            return []
        if self._checker is None:
            self._checker = SpellChecker()
        key = word.lower().strip("’'’")
        try:
            candidates = self._checker.candidates(key)
        except Exception:
            return []
        if not candidates:
            return []
        # Best-first ordering by usage frequency from the bundled
        # corpus — more common candidates come first. Fall back to
        # alphabetical when frequencies tie.
        ranked = sorted(
            candidates,
            key=lambda w: (-self._checker.word_usage_frequency(w), w),
        )
        # Match the case of the input: ALL CAPS, Capitalised, lower.
        def _case_match(w: str) -> str:
            if word.isupper():
                return w.upper()
            if word[:1].isupper():
                return w.capitalize()
            return w
        return [_case_match(w) for w in ranked[:limit]]

    # ---- highlight implementation ------------------------------------

    def highlightBlock(self, text: str) -> None:
        if not self._enabled or not _AVAILABLE or not text:
            return
        block = self.currentBlock()
        if block.userState() in _SKIP_STATES:
            return
        for start, end in self.misspelled_ranges(text):
            self.setFormat(start, end - start, self._fmt)

    def misspelled_ranges(self, text: str) -> list[tuple[int, int]]:
        """[start, end) of each unknown word in a paragraph of prose:
        what the underline marks, and what the Spelling panel lists
        (with the underline turned off too)."""
        if not _AVAILABLE or not text:
            return []
        if self._checker is None:
            self._checker = SpellChecker()  # loads English by default
        out = []
        for m in _WORD_RE.finditer(text):
            raw = m.group(0)
            if not _is_checkable(raw):
                continue
            key = raw.lower().strip("’'’")
            if not key or key in self._ignored:
                continue
            cached = self._unknown_cache.get(key)
            if cached is None:
                cached = bool(self._checker.unknown([key]))
                self._unknown_cache[key] = cached
            if cached:
                out.append((m.start(), m.end()))
        return out
