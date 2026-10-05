"""Insert ▸ Citation: pick references from a KherveRef library.

Lists the entries of a KherveRef library (read straight from its
library.bib), searchable by key, author, year and title. Keys that are
not in any library can still be typed by hand.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from . import kherveref_link as kr
from .references import parse_bibtex, short_author

STYLES = [("cite", "\\cite — numeric [1]"),
          ("citep", "\\citep — (Smith, 2020)"),
          ("citet", "\\citet — Smith (2020)")]

_BROWSE = "__browse__"
_BUNDLED = "__bundled__"


class CitationPicker(QDialog):
    def __init__(self, current_library: str = "", bundled_bib: str = "",
                 style: str = "cite", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert citation")
        self.resize(820, 520)
        self._bundled = bundled_bib
        self._entries: dict[str, dict[str, str]] = {}
        self.library: str = ""

        self._lib = QComboBox()
        libs = kr.known_libraries()
        if current_library and kr.is_library(current_library) and \
                Path(current_library) not in libs:
            libs.insert(0, Path(current_library))
        for p in libs:
            self._lib.addItem(f"{kr.library_name(p)} — {p}", str(p))
        if bundled_bib:
            self._lib.addItem("References carried in this document", _BUNDLED)
        self._lib.addItem("Other library folder…", _BROWSE)
        if current_library:
            i = self._lib.findData(str(Path(current_library)))
            if i >= 0:
                self._lib.setCurrentIndex(i)
            elif bundled_bib:
                self._lib.setCurrentIndex(self._lib.findData(_BUNDLED))
        self._lib.currentIndexChanged.connect(self._library_changed)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search key, author, year, title")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._fill)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Key", "Authors", "Year", "Title"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._table.doubleClicked.connect(lambda _ix: self.accept())

        self._manual = QLineEdit()
        self._manual.setPlaceholderText("Other keys, comma separated (optional)")
        self._style = QComboBox()
        for code, label in STYLES:
            self._style.addItem(label, code)
        self._style.setCurrentIndex(max(0, self._style.findData(style)))

        self._empty = QLabel()
        self._empty.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Library", self._lib)
        form.addRow("Find", self._search)

        bottom = QFormLayout()
        bottom.addRow("Also cite", self._manual)
        bottom.addRow("Style", self._style)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Insert")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(self._table)
        lay.addWidget(self._empty)
        lay.addLayout(bottom)
        row = QHBoxLayout()
        hint = QLabel("Ctrl/Shift-click to cite several. Add references in "
                      "KherveRef; they appear here after it saves.")
        hint.setStyleSheet("color: gray;")
        row.addWidget(hint, 1)
        row.addWidget(buttons)
        lay.addLayout(row)
        self._library_changed()

    # ----- data -----

    def _library_changed(self, *_):
        data = self._lib.currentData()
        if data == _BROWSE:
            d = QFileDialog.getExistingDirectory(self, "KherveRef library folder")
            if d and kr.is_library(d):
                self._lib.blockSignals(True)
                self._lib.insertItem(0, f"{kr.library_name(d)} — {d}", d)
                self._lib.setCurrentIndex(0)
                self._lib.blockSignals(False)
                data = d
            else:
                self._lib.blockSignals(True)
                self._lib.setCurrentIndex(0)
                self._lib.blockSignals(False)
                data = self._lib.currentData()
        text = ""
        if data == _BUNDLED:
            text = self._bundled
            self.library = ""
        elif data and data != _BROWSE:
            try:
                text = (Path(data) / kr.LIBRARY_BIB).read_text(
                    encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            self.library = data
        self._entries = parse_bibtex(text)
        self._fill()

    def _fill(self, *_):
        keys = kr.search(self._entries, self._search.text())
        self._table.setRowCount(len(keys))
        for row, key in enumerate(sorted(keys, key=str.lower)):
            e = self._entries[key]
            for col, val in enumerate((key, short_author(e.get("author", "")),
                                       e.get("year", ""), e.get("title", ""))):
                item = QTableWidgetItem(val.replace("{", "").replace("}", ""))
                if col == 3:
                    item.setToolTip(item.text())
                self._table.setItem(row, col, item)
        if not self._entries:
            self._empty.setText(
                "No KherveRef library found. Open or create one in KherveRef "
                "(it remembers the libraries it has opened), choose “Other "
                "library folder…”, or type keys below.")
        else:
            self._empty.setText("")
        self._empty.setVisible(not self._entries)

    # ----- result -----

    def keys(self) -> list[str]:
        rows = sorted({ix.row() for ix in self._table.selectionModel().selectedRows()})
        keys = [self._table.item(r, 0).text() for r in rows]
        for k in self._manual.text().split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
        return keys

    def style(self) -> str:
        return self._style.currentData()

    def accept(self):
        if not self.keys():
            self._empty.setText("Select at least one reference, or type a key.")
            self._empty.setVisible(True)
            return
        super().accept()
