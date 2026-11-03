"""File > Share > Overleaf: the project link and a token, in plain words."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout,
)


class OverleafDialog(QDialog):
    def __init__(self, action: str, link: str = "", token: str = "",
                 parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{action} Overleaf")
        self.setMinimumWidth(520)
        lay = QVBoxLayout(self)
        intro = QLabel(
            "Collaborators edit the project on <b>overleaf.com</b>; "
            "KherveTeX sends your version there and gets theirs back as a "
            "document.<br><br>"
            "1. Open the project on Overleaf and copy the address from the "
            "browser.<br>"
            "2. In Overleaf, open <b>Account Settings › Git Integration</b> "
            "and create a token.<br><br>"
            "<span style='color: palette(placeholder-text)'>Git access needs "
            "an Overleaf plan that includes it. On a free plan, use "
            "<b>File › Share › Download for Overleaf</b> and upload the zip "
            "with Overleaf's <i>New Project › Upload Project</i>.</span>")
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.RichText)
        lay.addWidget(intro)
        form = QFormLayout()
        self._link = QLineEdit(link)
        self._link.setPlaceholderText("https://www.overleaf.com/project/…")
        form.addRow("Project link:", self._link)
        self._token = QLineEdit(token)
        self._token.setEchoMode(QLineEdit.Password)
        self._token.setPlaceholderText("olp_…")
        form.addRow("Git token:", self._token)
        lay.addLayout(form)
        note = QLabel("The token stays in memory until you quit; it is "
                      "never written to disk.")
        note.setStyleSheet("color: palette(placeholder-text);")
        lay.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok
                                   | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(action)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def link(self) -> str:
        return self._link.text().strip()

    def token(self) -> str:
        return self._token.text().strip()
