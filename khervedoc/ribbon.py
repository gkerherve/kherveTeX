"""Word-style ribbon, the window's only toolbar: tabs of labelled groups,
big buttons for the main command of a group and rows of small buttons
beside them.

The ribbon only arranges things the window already owns — QActions and
a few widgets (combos, galleries)."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QTabWidget,
    QToolButton, QVBoxLayout, QWidget,
)

_LARGE = QSize(32, 32)
_SMALL = QSize(18, 18)
# Word's grid: three small rows are as tall as one big button.
_ROW_H = 24
_BODY_H = 3 * _ROW_H + 2 * 2


def _short(action: QAction) -> str:
    """Menu text without the & accelerator or a trailing ellipsis."""
    return action.text().replace("&", "").rstrip(".…").strip()


def big_label(text: str) -> str:
    """Always two lines, as Word's big buttons: a long label breaks at the
    space nearest its middle, a short one gets a blank line (where a
    drop-down's chevron sits) so every icon stays at the same height."""
    if len(text) <= 9 or " " not in text:
        return text + "\n "
    mid = len(text) / 2
    at = min((i for i, ch in enumerate(text) if ch == " "),
             key=lambda i: abs(i - mid))
    return text[:at] + "\n" + text[at + 1:]


def _button(action: QAction, large: bool, text: bool) -> QToolButton:
    b = QToolButton()
    b.setDefaultAction(action)
    b.setAutoRaise(True)
    # A drop-down beside the button (Word's Paste ▾), kept off the action
    # itself so the action stays a plain item in the menu bar.
    menu = action.property("ribbon_menu")
    if menu is not None:
        b.setMenu(menu)
        b.setPopupMode(QToolButton.MenuButtonPopup)
    if large:
        b.setIconSize(_LARGE)
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        b.setMinimumWidth(52)
        b.setFixedHeight(_BODY_H)
        label = big_label(_short(action))
    else:
        b.setIconSize(_SMALL)
        b.setFixedHeight(_ROW_H)
        if text:
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            label = _short(action)
        else:
            b.setToolButtonStyle(Qt.ToolButtonIconOnly)
            b.setFixedWidth(_ROW_H + 2)
            return b
    b.setText(label)
    # The button resets its text to the action's whenever the action
    # changes (a toggle, say), which would undo the label above.
    action.changed.connect(lambda: b.setText(label))
    return b


class RibbonTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(4, 3, 4, 0)
        self._lay.setSpacing(0)
        self._lay.addStretch(1)

    def add_group(self, label: str, *, large=(), rows=(),
                  text: bool = False) -> None:
        """A group: `large` actions/widgets as big buttons, then `rows`
        (lists of actions/widgets) stacked as small buttons; `text`
        shows labels beside the small icons."""
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(5, 0, 5, 1)
        v.setSpacing(0)
        body = QHBoxLayout()
        body.setSpacing(1)
        for it in large:
            if isinstance(it, QAction):
                body.addWidget(_button(it, True, True))
            else:
                # Page buttons and the like fill the height as actions do.
                if (isinstance(it, QToolButton) and
                        it.toolButtonStyle() == Qt.ToolButtonTextUnderIcon):
                    it.setFixedHeight(_BODY_H)
                    it.setMinimumWidth(52)
                body.addWidget(it, 0, Qt.AlignVCenter)
        if rows:
            body.addLayout(self._text_rows(rows) if text
                           else self._icon_rows(rows))
        holder = QWidget()
        holder.setFixedHeight(_BODY_H)
        holder.setLayout(body)
        body.setContentsMargins(0, 0, 0, 0)
        v.addWidget(holder, 0, Qt.AlignLeft)
        v.addStretch(1)
        cap = QLabel(label)
        cap.setObjectName("RibbonCaption")
        cap.setAlignment(Qt.AlignHCenter)
        v.addWidget(cap)
        self._lay.insertWidget(self._lay.count() - 1, box)
        sep = QFrame()
        sep.setObjectName("RibbonSeparator")
        sep.setFixedWidth(1)
        self._lay.insertWidget(self._lay.count() - 1, sep)

    @staticmethod
    def _text_rows(rows) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(2)
        for r, row in enumerate(rows):
            for c, it in enumerate(row):
                w = _button(it, False, True) if isinstance(it, QAction) else it
                grid.addWidget(w, r, c, Qt.AlignLeft)
        return grid

    @staticmethod
    def _icon_rows(rows) -> QVBoxLayout:
        """Each row packs its own buttons: a wide combo in one row must not
        spread the buttons of the next, as a shared grid column would."""
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addStretch(1)
        for row in rows:
            h = QHBoxLayout()
            h.setSpacing(0)
            for it in row:
                h.addWidget(_button(it, False, False)
                            if isinstance(it, QAction) else it)
            h.addStretch(1)
            col.addLayout(h)
        col.addStretch(1)
        return col


class Ribbon(QTabWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(_BODY_H + 52)
        # Word: flat text tabs, no boxes; the open tab is bold with a short
        # coloured bar under it, the groups sit on a plain band, and buttons
        # show only a soft fill on hover or when on. Hairlines are translucent
        # grey so they stay faint on every light and dark theme.
        self.setStyleSheet("""
            QTabWidget::pane { border: none;
                border-top: 1px solid palette(midlight); top: -1px; }
            QTabBar { qproperty-drawBase: 0; }
            QTabBar::tab { background: transparent; border: none;
                padding: 7px 11px 5px 11px; margin: 0 1px;
                font-size: 13px; }
            QTabBar::tab:hover { background: palette(midlight);
                border-radius: 4px; }
            QTabBar::tab:selected { font-weight: 600;
                border-bottom: 3px solid #2b579a;
                padding-bottom: 2px; }
            QToolButton { font-size: 11px; padding: 1px 3px;
                border: 1px solid transparent; border-radius: 4px; }
            QToolButton:checked, QToolButton:pressed {
                border-color: transparent; }
            QToolButton::menu-indicator { subcontrol-origin: padding;
                subcontrol-position: bottom center; bottom: 1px; }
            QToolButton::menu-button { width: 11px; }
            QToolButton#GalleryMore { padding: 0; }
            QToolButton#GalleryMore::menu-indicator { image: none; }
            QComboBox { font-size: 12px; min-height: 18px; max-height: 20px;
                padding: 0 2px 0 4px; }
            QLabel#RibbonCaption { font-size: 10px;
                color: palette(placeholder-text); }
            QFrame#RibbonSeparator { background: rgba(128, 128, 128, 90);
                margin: 3px 0 6px 0; }
            QWidget#StyleGallery { background: palette(base);
                border: 1px solid rgba(128, 128, 128, 90);
                border-radius: 4px; }
        """)

    def add_tab(self, name: str) -> RibbonTab:
        tab = RibbonTab()
        self.addTab(tab, name)
        return tab

    def add_contextual_tab(self, name: str, kind: str) -> RibbonTab:
        """A tab that appears only while the caret is in that kind of
        object (Word's Table Design / Picture Format tabs)."""
        tab = self.add_tab(name)
        idx = self.indexOf(tab)
        self.tabBar().setTabTextColor(idx, QColor("#2b579a"))
        self.setTabVisible(idx, False)
        self._contextual = getattr(self, "_contextual", [])
        self._contextual.append((kind, tab))
        return tab

    def show_context(self, kind: str | None) -> None:
        for k, tab in getattr(self, "_contextual", []):
            idx = self.indexOf(tab)
            visible = k == kind
            if self.isTabVisible(idx) != visible:
                if not visible and self.currentIndex() == idx:
                    self.setCurrentIndex(0)
                self.setTabVisible(idx, visible)

    def set_corner(self, actions, corner: Qt.Corner, labelled=()) -> None:
        """Always-visible buttons beside the tabs (Word's Quick Access);
        those in `labelled` show their name, like Word's Share button."""
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(0)
        for a in actions:
            if a is None:
                line = QFrame()
                line.setObjectName("RibbonSeparator")
                line.setFixedSize(1, _ROW_H)
                h.addSpacing(4)
                h.addWidget(line)
                h.addSpacing(4)
            else:
                h.addWidget(_button(a, False, a in labelled))
        self.setCornerWidget(w, corner)
