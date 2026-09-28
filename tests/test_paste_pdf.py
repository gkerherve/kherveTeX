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
