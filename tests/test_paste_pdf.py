"""Pasting from Office uses the clipboard's vector PDF, not its bitmap."""
import os

import pytest

pytest.importorskip("PySide6")
fitz = pytest.importorskip("fitz")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QMimeData  # noqa: E402
from PySide6.QtGui import QImage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc.paged_edit import _PASTE_DPI, _clipboard_pdf  # noqa: E402


def _pdf_bytes(w_pt=144, h_pt=72) -> bytes:
    doc = fitz.open()
    doc.new_page(width=w_pt, height=h_pt)
    return doc.tobytes()


def test_clipboard_pdf_found_and_rendered_at_high_dpi(tmp_path):
    QApplication.instance() or QApplication([])
    mime = QMimeData()
    mime.setData("com.adobe.pdf", _pdf_bytes())
    mime.setImageData(QImage(144, 72, QImage.Format_RGB32))
    data = _clipboard_pdf(mime)
    assert data is not None and data.startswith(b"%PDF")
    with fitz.open(stream=data, filetype="pdf") as pdf:
        pix = pdf[0].get_pixmap(dpi=_PASTE_DPI)
    assert pix.width == 2 * _PASTE_DPI  # 2 inches wide


def test_no_pdf_flavour_returns_none():
    QApplication.instance() or QApplication([])
    mime = QMimeData()
    mime.setImageData(QImage(10, 10, QImage.Format_RGB32))
    assert _clipboard_pdf(mime) is None


def test_enter_after_pasted_picture_makes_visible_lines(tmp_path):
    """Enter right after a pasted picture used to add zero-height lines,
    so the caret seemed stuck until you typed."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
    from PySide6.QtTest import QTest
    from khervedoc.editor import DocumentEditor
    from khervedoc.model import Document
    QApplication.instance() or QApplication([])
    ed = DocumentEditor()
    ed.set_document_dir(tmp_path)
    ed.set_document(Document())
    img = QImage(40, 30, QImage.Format_RGB32)
    img.fill(QColor("red"))
    mime = QMimeData()
    mime.setImageData(img)
    ed._edit.insertFromMimeData(mime)
    assert ed._edit.textCursor().block().userState() == 0
    y0 = ed._edit.cursorRect().y()
    QTest.keyClick(ed._edit, Qt.Key_Return)
    assert ed._edit.cursorRect().y() > y0


def test_paste_special_latex_text_and_picture(tmp_path):
    from khervedoc.editor import DocumentEditor
    from khervedoc.model import Document, Figure, Section
    app = QApplication.instance() or QApplication([])
    ed = DocumentEditor()
    ed.set_document_dir(tmp_path)
    ed.set_document(Document())
    app.clipboard().setText(r"\section{Results} Some $x^2$ text.")
    keys = [k for k, _ in ed.paste_options()]
    assert {"keep", "text", "picture", "latex"} <= set(keys)
    ed.paste_special("latex")
    ed.paste_special("picture")
    kinds = [type(b) for b in ed.get_document().children]
    assert Section in kinds and Figure in kinds
