"""Welcome page shown at start: what to open, and how to work.

The layout choice is asked every time (unless switched off) because it
depends on the task: side by side with the live PDF when the LaTeX
output matters, or the visual editor alone — like Word — with the PDF,
console and background compiles off.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QRadioButton, QVBoxLayout,
    QWidget,
)

LAYOUT_SIDE = "side"
LAYOUT_VISUAL = "visual"
LAYOUT_PAGE = "page"


class WelcomeDialog(QDialog):
    """Returns, via `choice` and `layout`, what the user picked.

    choice is one of ("continue",), ("new",), ("open",), ("project",),
    ("example", index) or ("recent", Path)."""

    def __init__(self, recent: list[Path], examples: list[tuple[str, object]],
                 layout: str = LAYOUT_SIDE, show_at_start: bool = True,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to KherveTeX")
        self.setMinimumSize(QSize(860, 560))
        self.choice: tuple = ("continue",)
        self.layout_mode = layout

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(14)

        # ── header ────────────────────────────────────────────
        from . import __version__, icons
        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(icons.app_icon().pixmap(64, 64))
        head.addWidget(logo)
        titles = QVBoxLayout()
        t = QLabel("KherveTeX")
        f = QFont()
        f.setPointSizeF(22)
        f.setBold(True)
        t.setFont(f)
        titles.addWidget(t)
        titles.addWidget(QLabel(
            f"Write like in Word, publish in LaTeX — version {__version__}"))
        head.addLayout(titles, 1)
        root.addLayout(head)

        # ── start / examples / recent ─────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(16)

        start = QVBoxLayout()
        start.addWidget(self._heading("Start"))
        for label, tip, choice in (
                ("\U0001F4C4  New document", "A blank page", ("new",)),
                ("\U0001F4C2  Open…", "Open or import a document "
                 "(.ktexz, .tex, .docx, .md, .pdf)", ("open",)),
                ("\U0001F4DA  New project (thesis, book)…",
                 "Several documents compiled into one PDF", ("project",)),
                ("→  Continue with the tour",
                 "The guided tour already open behind this page",
                 ("continue",))):
            b = QPushButton(label)
            b.setToolTip(tip)
            b.setMinimumHeight(34)
            b.setStyleSheet("text-align: left; padding-left: 12px;")
            b.clicked.connect(lambda _=False, c=choice: self._finish(c))
            start.addWidget(b)
        start.addStretch(1)
        cols.addLayout(start, 3)

        ex_col = QVBoxLayout()
        ex_col.addWidget(self._heading("Examples & templates"))
        self._examples = QListWidget()
        for i, (label, _factory) in enumerate(examples):
            # Menu labels carry "&" accelerators; "&&" is a literal "&".
            text = label.replace("&&", "\0").replace("&", "").replace("\0", "&")
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, i)
            self._examples.addItem(item)
        self._examples.itemActivated.connect(
            lambda it: self._finish(("example", it.data(Qt.UserRole))))
        ex_col.addWidget(self._examples, 1)
        cols.addLayout(ex_col, 3)

        rec_col = QVBoxLayout()
        rec_col.addWidget(self._heading("Recent"))
        self._recent = QListWidget()
        for p in recent:
            p = Path(p)
            item = QListWidgetItem(f"{p.name}\n   {p.parent}")
            item.setToolTip(str(p))
            item.setData(Qt.UserRole, str(p))
            if not p.exists():
                item.setFlags(Qt.NoItemFlags)
            self._recent.addItem(item)
        if not recent:
            empty = QListWidgetItem("No recent documents yet")
            empty.setFlags(Qt.NoItemFlags)
            self._recent.addItem(empty)
        self._recent.itemActivated.connect(
            lambda it: it.data(Qt.UserRole) and self._finish(
                ("recent", Path(it.data(Qt.UserRole)))))
        rec_col.addWidget(self._recent, 1)
        cols.addLayout(rec_col, 4)
        root.addLayout(cols, 1)

        # ── how to work ───────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        root.addWidget(line)
        root.addWidget(self._heading("How do you want to work?"))
        modes = QHBoxLayout()
        self._group = QButtonGroup(self)
        for mode, title, text in (
                (LAYOUT_SIDE, "Visual + PDF side by side",
                 "Edit on the left and watch the compiled LaTeX PDF on "
                 "the right, updated as you type."),
                (LAYOUT_VISUAL, "Visual only",
                 "The page with the Documents list beside it. The PDF "
                 "and console are hidden and nothing compiles while you "
                 "write."),
                (LAYOUT_PAGE, "Page only — like Word",
                 "Just the page: the Documents list is hidden too. "
                 "Bring anything back from the View menu.")):
            box = QVBoxLayout()
            rb = QRadioButton(title)
            f = rb.font()
            f.setBold(True)
            rb.setFont(f)
            rb.setChecked(mode == layout)
            rb.toggled.connect(
                lambda on, m=mode: on and setattr(self, "layout_mode", m))
            self._group.addButton(rb)
            box.addWidget(rb)
            desc = QLabel(text)
            desc.setWordWrap(True)
            desc.setContentsMargins(24, 0, 0, 0)
            box.addWidget(desc)
            holder = QWidget()
            holder.setLayout(box)
            modes.addWidget(holder, 1)
        root.addLayout(modes)

        bottom = QHBoxLayout()
        self._show_again = QCheckBox("Show this page when KherveTeX starts")
        self._show_again.setChecked(show_at_start)
        bottom.addWidget(self._show_again)
        bottom.addStretch(1)
        go = QPushButton("Start writing")
        go.setDefault(True)
        go.setMinimumWidth(140)
        go.clicked.connect(lambda: self._finish(("continue",)))
        bottom.addWidget(go)
        root.addLayout(bottom)

    @staticmethod
    def _heading(text: str) -> QLabel:
        lab = QLabel(text)
        f = lab.font()
        f.setBold(True)
        f.setPointSizeF(f.pointSizeF() + 1.5)
        lab.setFont(f)
        return lab

    def show_at_start(self) -> bool:
        return self._show_again.isChecked()

    def _finish(self, choice: tuple) -> None:
        self.choice = choice
        self.accept()
