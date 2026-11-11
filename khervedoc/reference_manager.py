"""References ▸ Manage references: the document's own list of references.

A small KherveRef dedicated to one document: its .bib, kept inside the
.ktex (doc_references.py). A search bar and a filter find any reference,
and what is missing: keys the document cites that the list does not have,
listed in red at the end. Selecting one fills the form; New, Delete,
Import .bib… and From KherveRef… change the list; Cite inserts the
selected references at the caret. Nothing is saved until Done; Cancel
leaves the list as it was.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from . import doc_references as dr
from . import kherveref_link as kr
from .references import short_author

# The list's filter.
FILTERS = [("all", "All references"), ("cited", "Cited in the document"),
           ("not cited", "Not cited"), ("missing", "Missing (cited, not in the list)")]

# The form's fields and their labels.
_LABELS = {"author": "Authors", "title": "Title", "journal": "Journal",
           "booktitle": "Book / proceedings", "year": "Year", "volume": "Volume",
           "number": "Number", "pages": "Pages", "publisher": "Publisher",
           "school": "School", "institution": "Institution", "doi": "DOI",
           "url": "URL", "note": "Note"}

_RED = "#d8000c"


def summary(rows: list[dict]) -> str:
    n = sum(1 for r in rows if r["status"] != dr.MISSING)
    cited = sum(1 for r in rows if r["status"] == dr.CITED)
    missing = sum(1 for r in rows if r["status"] == dr.MISSING)
    text = f"{n} reference{'s' if n != 1 else ''} · {cited} cited"
    if missing:
        text += f" · {missing} missing"
    return text


class ReferenceManager(QDialog):
    def __init__(self, bib_text: str, cited: list[str], library: str = "",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("References of this document")
        self.resize(1000, 600)
        self._text = bib_text
        self._original = bib_text
        self._cited = list(cited)
        self._library = library
        self._rows: list[dict] = []
        # The entry in the form: its key in the list (None for a new one
        # or a missing key) and whether the form was changed.
        self._editing: str | None = None
        self._form_dirty = False
        self._cite: list[str] = []

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search key, author, year, title")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._fill)
        self._filter = QComboBox()
        for code, label in FILTERS:
            self._filter.addItem(label, code)
        self._filter.currentIndexChanged.connect(self._fill)
        top = QHBoxLayout()
        top.addWidget(self._search, 1)
        top.addWidget(self._filter)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Key", "Authors", "Year", "Title", "Cited"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        for col, w in ((0, 130), (1, 110), (2, 50), (4, 60)):
            self._table.setColumnWidth(col, w)
        self._table.itemSelectionChanged.connect(self._selection_changed)

        # The form.
        self._type = QComboBox()
        self._type.addItems(dr.ENTRY_TYPES)
        self._type.setEditable(True)
        self._type.currentTextChanged.connect(self._dirty)
        self._key = QLineEdit()
        self._key.setPlaceholderText("Made from the author, year and title")
        self._key.textEdited.connect(self._dirty)
        self._fields: dict[str, QLineEdit] = {}
        form = QFormLayout()
        form.addRow("Type", self._type)
        form.addRow("Key", self._key)
        for f in dr.FIELDS:
            w = QLineEdit()
            if f == "author":
                w.setPlaceholderText("Surname, First and Surname, First")
            w.textEdited.connect(self._dirty)
            self._fields[f] = w
            form.addRow(_LABELS[f], w)
        self._save_entry = QPushButton("Save entry")
        self._save_entry.setToolTip("Keep the changes made in the form")
        self._save_entry.clicked.connect(self.save_entry)
        form.addRow("", self._save_entry)
        right = QWidget()
        right.setLayout(form)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self._table)
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        self._new = QPushButton("New")
        self._new.setToolTip("Add a reference to the list")
        self._new.clicked.connect(self.new_entry)
        self._delete = QPushButton("Delete")
        self._delete.setToolTip("Take the selected references out of the list")
        self._delete.clicked.connect(self.delete_selected)
        self._import = QPushButton("Import .bib…")
        self._import.setToolTip("Add the references of a .bib file (from Zotero, "
                                "Mendeley, Google Scholar...)")
        self._import.clicked.connect(self._import_bib)
        self._from_kr = QPushButton("From KherveRef…")
        self._from_kr.setToolTip("Add references from a KherveRef library")
        self._from_kr.clicked.connect(self._import_kherveref)
        tools = QHBoxLayout()
        for b in (self._new, self._delete, self._import, self._from_kr):
            tools.addWidget(b)
        tools.addStretch(1)
        self._summary = QLabel()
        tools.addWidget(self._summary)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Done")
        self._cite_btn = buttons.addButton("Cite", QDialogButtonBox.ActionRole)
        self._cite_btn.setToolTip("Cite the selected references at the cursor")
        self._cite_btn.clicked.connect(self.cite_selected)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        note = ""
        if library and library != dr.DOCUMENT_LIBRARY:
            note = (f"This document cites from the KherveRef library "
                    f"“{kr.library_name(library)}”. Changing the list here gives "
                    "it a list of its own, its cited references included.")
        self._note = QLabel(note)
        self._note.setWordWrap(True)
        self._note.setStyleSheet("color: gray;")
        self._note.setVisible(bool(note))
        lay.addWidget(self._note)
        lay.addLayout(top)
        lay.addWidget(split, 1)
        lay.addLayout(tools)
        lay.addWidget(buttons)
        self._fill()
        self._clear_form()

    # ---- the list ----

    def text(self) -> str:
        """The list as it is now (.bib source)."""
        return self._text

    def changed(self) -> bool:
        return self._text != self._original

    def cite_keys(self) -> list[str]:
        return list(self._cite)

    def rows(self) -> list[dict]:
        """The rows shown (search and filter applied)."""
        return list(self._rows)

    def _fill(self, *_) -> None:
        keep = self.selected_keys()
        code = self._filter.currentData()
        all_rows = dr.rows(self._text, self._cited)
        self._rows = [r for r in all_rows
                      if (code == "all" or r["status"] == code)
                      and dr.matches(r, self._search.text())]
        self._table.blockSignals(True)
        self._table.setRowCount(len(self._rows))
        for i, r in enumerate(self._rows):
            missing = r["status"] == dr.MISSING
            vals = (r["key"], short_author(r["author"]), r["year"],
                    "(not in the list: select it to add it)" if missing
                    else r["title"].replace("{", "").replace("}", ""),
                    "✓" if r["status"] == dr.CITED else ("missing" if missing else ""))
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if missing:
                    item.setForeground(QColor(_RED))
                if col == 3:
                    item.setToolTip(val)
                self._table.setItem(i, col, item)
            if r["key"] in keep:
                self._table.selectRow(i)
        self._table.blockSignals(False)
        self._summary.setText(summary(all_rows))

    def selected_keys(self) -> list[str]:
        if not hasattr(self, "_table"):
            return []
        rows = sorted({ix.row() for ix in self._table.selectionModel().selectedRows()})
        return [self._table.item(r, 0).text() for r in rows if self._table.item(r, 0)]

    def select(self, key: str) -> None:
        for i, r in enumerate(self._rows):
            if r["key"] == key:
                self._table.selectRow(i)
                return

    def _selection_changed(self) -> None:
        keys = self.selected_keys()
        if self._form_dirty:
            # Keep the entry left in the form; the rows clicked stay
            # selected.
            self.save_entry(refill=False)
            self._fill()
        if len(keys) != 1:
            self._clear_form()
            return
        key = keys[0]
        src = dr.entries(self._text).get(key)
        if src is None:
            # A missing key: a new entry with that key.
            self._clear_form()
            self._key.setText(key)
            return
        etype, _k, fields = dr.parse_entry(src)
        self._editing = key
        self._type.blockSignals(True)
        self._type.setCurrentText(etype)
        self._type.blockSignals(False)
        self._key.setText(key)
        for f, w in self._fields.items():
            w.setText(fields.get(f, ""))
        self._extra = {f: v for f, v in fields.items() if f not in self._fields}
        self._form_dirty = False

    def _clear_form(self) -> None:
        self._editing = None
        self._extra: dict[str, str] = {}
        self._type.blockSignals(True)
        self._type.setCurrentText("article")
        self._type.blockSignals(False)
        self._key.clear()
        for w in self._fields.values():
            w.clear()
        self._form_dirty = False

    def _dirty(self, *_):
        self._form_dirty = True

    # ---- form and buttons ----

    def set_field(self, name: str, value: str) -> None:
        """Type into a field of the form (as the user does)."""
        if name == "key":
            self._key.setText(value)
        elif name == "type":
            self._type.setCurrentText(value)
        else:
            self._fields[name].setText(value)
        self._form_dirty = True

    def new_entry(self) -> None:
        if self._form_dirty:
            self.save_entry(refill=False)
        self._table.clearSelection()
        self._clear_form()
        self._fields["author"].setFocus()

    def save_entry(self, refill: bool = True) -> str | None:
        """Put the form's entry in the list; its key (made from the
        author, year and title when left empty), None when the form is
        empty."""
        fields = {f: w.text().strip() for f, w in self._fields.items()}
        if not any(fields.values()) and not self._key.text().strip():
            self._form_dirty = False
            return None
        fields.update(getattr(self, "_extra", {}))
        taken = set(dr.entries(self._text)) - {self._editing}
        key = self._key.text().strip().replace(" ", "")
        if not key:
            key = dr.suggest_key(fields["author"], fields["year"], fields["title"], taken)
        etype = self._type.currentText().strip().lower() or "misc"
        self._text = dr.set_entry(self._text, self._editing,
                                  dr.format_entry(etype, key, fields))
        self._editing = key
        self._key.setText(key)
        self._form_dirty = False
        if refill:
            self._fill()
            self.select(key)
        return key

    def delete_selected(self) -> None:
        keys = [k for k in self.selected_keys() if k in dr.entries(self._text)]
        for k in keys:
            self._text = dr.remove_entry(self._text, k)
        self._clear_form()
        self._fill()

    def add_bib(self, other: str) -> list[str]:
        """Add the entries of a .bib the list lacks; the keys added."""
        self._text, added = dr.merge(self._text, other)
        self._fill()
        return added

    def _import_bib(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import a .bib file", "",
                                              "BibTeX (*.bib);;All files (*)")
        if not path:
            return
        try:
            other = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            QMessageBox.warning(self, "Import .bib", str(exc))
            return
        added = self.add_bib(other)
        QMessageBox.information(self, "Import .bib",
                                f"{len(added)} reference{'s' if len(added) != 1 else ''} added.")

    def _import_kherveref(self) -> None:
        from .citation_picker import CitationPicker
        lib = self._library if kr.is_library(self._library) else ""
        dlg = CitationPicker(lib, "", parent=self)
        dlg.setWindowTitle("Add references from KherveRef")
        if dlg.exec() != QDialog.Accepted or not dlg.library:
            return
        source = kr.load_library(dlg.library)
        picked = {k: source[k] for k in dlg.keys() if k in source}
        if picked:
            self.add_bib("\n\n".join(picked.values()))

    def cite_selected(self) -> None:
        if self._form_dirty:
            self.save_entry()
        keys = self.selected_keys()
        if not keys:
            return
        # A missing key is cited already; citing it again is harmless.
        self._cite = keys
        self.accept()

    def accept(self) -> None:
        if self._form_dirty:
            self.save_entry(refill=False)
        super().accept()
