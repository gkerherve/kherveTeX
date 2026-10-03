"""Print and Print Preview of the compiled PDF.

What goes to the printer is the typeset PDF, never the Visual tab, so the
paper matches File > Export > PDF page for page. Each PDF page is rendered
with PyMuPDF and scaled onto the whole sheet (the LaTeX margins are already
in the page); a landscape page on portrait paper is turned to fill it.

The preview renders at screen resolution and the real print at 300 dpi:
the preview keeps every page in memory, and full-resolution pages of a
long document would take gigabytes.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, QSizeF, Qt
from PySide6.QtGui import QImage, QPageLayout, QPageSize, QPainter, \
    QPaintEngine
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, \
    QPrintPreviewDialog
from PySide6.QtWidgets import QMessageBox

PRINT_DPI = 300
PREVIEW_DPI = 150


def page_sizes_pt(pdf_path: Path) -> list[tuple[float, float]]:
    """(width, height) in points of every page of the PDF."""
    import fitz
    with fitz.open(str(pdf_path)) as doc:
        return [(p.rect.width, p.rect.height) for p in doc]


def page_numbers(count: int, printer: QPrinter) -> list[int]:
    """0-based page indices the print dialog's range selects."""
    first, last = 1, count
    if printer.printRange() == QPrinter.PageRange and printer.fromPage():
        first = max(1, printer.fromPage())
        last = min(count, printer.toPage() or count)
    pages = list(range(first - 1, last))
    if printer.pageOrder() == QPrinter.LastPageFirst:
        pages.reverse()
    return pages


def fit_rect(page_w: float, page_h: float, target: QRectF,
             rotate: bool) -> QRectF:
    """The largest rect of the page's aspect (sides swapped when rotated)
    centred in ``target``."""
    if rotate:
        page_w, page_h = page_h, page_w
    scale = min(target.width() / page_w, target.height() / page_h)
    w, h = page_w * scale, page_h * scale
    return QRectF(target.x() + (target.width() - w) / 2,
                  target.y() + (target.height() - h) / 2, w, h)


def should_rotate(page_w: float, page_h: float, target: QRectF) -> bool:
    return (page_w > page_h) != (target.width() > target.height())


def match_printer_to_pdf(printer: QPrinter, pdf_path: Path) -> None:
    """Start the printer on the paper size and orientation of the
    document's first page (A4 stays A4, a beamer deck prints landscape)."""
    sizes = page_sizes_pt(pdf_path)
    if not sizes:
        return
    w, h = sizes[0]
    portrait = QPageSize(QSizeF(min(w, h), max(w, h)), QPageSize.Point,
                         "", QPageSize.FuzzyMatch)
    printer.setPageSize(portrait)
    printer.setPageOrientation(QPageLayout.Landscape if w > h
                               else QPageLayout.Portrait)
    printer.setFullPage(True)
    printer.setDocName(pdf_path.stem)


def render_pdf(printer: QPrinter, pdf_path: Path) -> int:
    """Paint the PDF's pages onto ``printer``; returns the pages printed."""
    import fitz
    painter = QPainter()
    if not painter.begin(printer):
        return 0
    preview = printer.paintEngine().type() == QPaintEngine.Picture
    dpi = PREVIEW_DPI if preview else PRINT_DPI
    printed = 0
    try:
        with fitz.open(str(pdf_path)) as doc:
            res = printer.resolution()
            sheet = printer.pageLayout().fullRectPixels(res) \
                if printer.fullPage() else printer.pageLayout().paintRectPixels(res)
            target = QRectF(0, 0, sheet.width(), sheet.height())
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            for i, pno in enumerate(page_numbers(len(doc), printer)):
                if i:
                    printer.newPage()
                page = doc[pno]
                pw, ph = page.rect.width, page.rect.height
                rotate = should_rotate(pw, ph, target)
                zoom = dpi / 72.0
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom),
                                      alpha=False)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                             QImage.Format_RGB888)
                box = fit_rect(pw, ph, target, rotate)
                painter.save()
                if rotate:
                    painter.translate(box.center())
                    painter.rotate(90)
                    painter.translate(-box.height() / 2, -box.width() / 2)
                    painter.drawImage(QRectF(0, 0, box.height(), box.width()),
                                      img)
                else:
                    painter.drawImage(box, img)
                painter.restore()
                printed += 1
    finally:
        painter.end()
    return printed


def print_pdf(parent, pdf_path: Path) -> bool:
    """File > Print: the system print dialog, then the printer."""
    printer = QPrinter(QPrinter.HighResolution)
    match_printer_to_pdf(printer, pdf_path)
    dlg = QPrintDialog(printer, parent)
    dlg.setWindowTitle("Print")
    dlg.setOption(QPrintDialog.PrintPageRange, True)
    dlg.setMinMax(1, max(1, len(page_sizes_pt(pdf_path))))
    if dlg.exec() != QPrintDialog.Accepted:
        return False
    if not render_pdf(printer, pdf_path):
        QMessageBox.warning(parent, "Print", "Nothing was printed.")
        return False
    return True


class PdfPrintPreview(QPrintPreviewDialog):
    """File > Print Preview: the pages exactly as they will print, opened
    large with the whole page in view; Print sends them on from here."""

    def __init__(self, pdf_path: Path, parent=None):
        self._printer = QPrinter(QPrinter.HighResolution)
        match_printer_to_pdf(self._printer, pdf_path)
        super().__init__(self._printer, parent, Qt.Window)
        self._pdf = pdf_path
        self.setWindowTitle(f"Print Preview — {pdf_path.stem}")
        if parent is not None:
            geo = parent.geometry()
            self.resize(max(900, int(geo.width() * 0.8)),
                        max(700, int(geo.height() * 0.9)))
        self.paintRequested.connect(lambda p: render_pdf(p, self._pdf))
