"""QTextEdit subclass that paints visible page-break lines.

The text content still flows as a single editable surface — properly
splitting the document into separate page widgets would require a custom
text-document layout, which is much larger work. The page-break overlay
draws horizontal dashed lines at each page boundary computed from the
QTextDocument's pagination, giving users immediate feedback about how
their content will be paginated in the PDF.
"""
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, QRectF, QSizeF, Qt, Signal
from PySide6.QtGui import (
    QColor, QImage, QLinearGradient, QPainter, QPen, QTextFormat,
)
from PySide6.QtWidgets import QTextEdit, QWidget


def anchor_offset(block_text: str, key_norm: str) -> int:
    """Where a PDF page's first line (normalised) starts in a block's
    text, or -1. A match at the block's start always counts; one inside
    the block (a page starting mid-paragraph) only when the key is long
    enough to be unambiguous — a short heading like "Lists" would
    otherwise match any paragraph that merely uses the word."""
    norm = _normalize_for_match(block_text)
    if not norm:
        return -1
    if len(key_norm) < 16:
        # A short first line is a whole line — usually a heading — so
        # the block must BE that line, not merely begin with its word.
        if norm == key_norm:
            return 0
    elif norm.startswith(key_norm) or (len(norm) >= 3
                                       and key_norm.startswith(norm)):
        return 0
    if len(key_norm) >= 12:
        idx = norm.find(key_norm)
        if idx > 0:
            # Map back to a raw-text offset (whitespace may differ).
            return min(len(block_text), idx)
    return -1


def _normalize_for_match(s: str) -> str:
    """Collapse whitespace, strip accents, and lowercase so PDF-extracted
    text (which may have ligatures, special Unicode, or different whitespace)
    can match the editor's QTextBlock content."""
    s = unicodedata.normalize("NFKD", s)
    # Drop combining marks (accents) — helps with ligature differences.
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


_IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".svg",
}
_DOCUMENT_SUFFIXES = {
    ".kdocz", ".ktexz", ".tex", ".md", ".markdown", ".docx",
}


def _is_document_file(p: Path) -> bool:
    name = p.name.lower()
    if name.endswith(".kdoc.json") or name.endswith(".ktex.json"):
        return True
    return p.suffix.lower() in _DOCUMENT_SUFFIXES


# Colour of the "desk" between sheets; matches the editor's backdrop.
DESK_COLOR = QColor("#d0d4d8")
_SHEET_EDGE = QColor("#b8bcc1")

# Block-format property carrying a heading's display number ("2.1").
# The number is painted, never stored as text, so it can't leak into the
# model or the LaTeX (which numbers headings itself).
HEADING_NUMBER_PROPERTY = QTextFormat.UserProperty + 40


class _PageBreakOverlay(QWidget):
    """Transparent child of the viewport that paints page-break lines."""

    def __init__(self, edit: "PagedTextEdit"):
        super().__init__(edit.viewport())
        self._edit = edit
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        # Without this the overlay would paint its own background on top of
        # the QTextEdit's content (covering the text).
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        edit.viewport().installEventFilter(self)
        self.resize(edit.viewport().size())
        self.raise_()

    def eventFilter(self, obj, event):
        if obj is self._edit.viewport():
            if event.type() == QEvent.Resize:
                self.resize(self._edit.viewport().size())
            elif event.type() == QEvent.Paint:
                # Schedule a repaint after the viewport finishes painting.
                self.update()
        return False

    def paintEvent(self, ev):
        # Preferred path: the compiler hands us a list of "first text
        # of each PDF page" anchors (page_no, y_doc_pixels). We
        # painted those by finding each snippet in the editor and
        # recording the Y position of its block. That maps the
        # editor's pagination 1:1 to the PDF's, even when LaTeX's
        # text density (title block, abstract, floats) means the
        # break is nowhere near halfway through the editor content.
        anchors = self._edit.page_anchor_positions()
        pdf_pages = self._edit.pdf_page_count()
        # Only trust the anchored path when most page breaks resolved
        # successfully — partial results produce confusing gaps and
        # out-of-order labels.
        expected_breaks = max(pdf_pages - 1, 1)
        if anchors and len(anchors) >= expected_breaks * 0.6:
            # Sort by Y so labels appear top-to-bottom even if snippet
            # matching resolved them in a different order.
            anchors.sort(key=lambda a: a[1])
            self._paint_anchored(anchors)
            return
        # Fallback: even spacing using doc_height / pdf_page_count.
        # Used between compile attempts or when the snippet match
        # fails. Less accurate than the anchored path but better
        # than the static page_height_px from before.
        pdf_pages = self._edit.pdf_page_count()
        doc_h = int(self._edit.document().size().height())
        if pdf_pages >= 2 and doc_h > 0:
            spacing = doc_h / pdf_pages
            total_pages = pdf_pages
            mode = "compiled"
        else:
            spacing = float(self._edit.page_height_px())
            total_pages = None
            mode = "estimate"
        if spacing <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        pen = QPen(QColor(140, 70, 50, 180), 1, Qt.DashLine)
        painter.setPen(pen)
        scroll_y = self._edit.verticalScrollBar().value()
        h = self.height()
        w = self.width()
        n = 1
        while True:
            y_doc = n * spacing
            y_vp = int(y_doc - scroll_y)
            if y_vp > h + spacing:
                break
            if total_pages is not None and n >= total_pages:
                break
            if 0 <= y_vp <= h:
                painter.drawLine(6, y_vp, w - 6, y_vp)
                label = (f"— page {n} / {n + 1} —" if mode == "compiled"
                         else f"— page {n} / {n + 1} (estimate) —")
                painter.drawText(8, y_vp - 4, label)
                self._draw_folio(painter, y_vp, n)
                painter.setPen(pen)
            n += 1
        self._draw_last_folio(painter, n)
        painter.end()

    def _draw_folio(self, painter: QPainter, y_vp: int, number: int) -> None:
        """The page number LaTeX prints centred in the footer (the
        default `plain` page style), just above the page's end."""
        font = painter.font()
        painter.save()
        f = self._edit.font()
        f.setPointSizeF(max(6.0, f.pointSizeF() * 0.9))
        painter.setFont(f)
        painter.setPen(QColor(90, 90, 90))
        fm = painter.fontMetrics()
        text = str(number)
        x = (self.width() - fm.horizontalAdvance(text)) // 2
        painter.drawText(x, y_vp - fm.descent() - 6, text)
        painter.restore()
        painter.setFont(font)

    def _draw_last_folio(self, painter: QPainter, number: int) -> None:
        doc_h = self._edit.document().size().height()
        y_vp = int(doc_h - self._edit.verticalScrollBar().value())
        if 0 <= y_vp <= self.height() + 20:
            self._draw_folio(painter, y_vp, number)

    def _paint_anchored(self,
                        anchors: list[tuple[int, float]]) -> None:
        """Draw one break line per anchor (page_no, y_doc). Each
        anchor is "page N starts at this Y pixel in the editor"."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        pen = QPen(QColor(140, 70, 50, 180), 1, Qt.DashLine)
        painter.setPen(pen)
        scroll_y = self._edit.verticalScrollBar().value()
        h = self.height()
        w = self.width()
        for seq, (_page_no, y_doc) in enumerate(anchors, start=1):
            y_vp = int(y_doc - scroll_y)
            if y_vp < -20 or y_vp > h + 20:
                continue
            painter.drawLine(6, y_vp, w - 6, y_vp)
            # Use sequential numbering based on Y-sorted position so
            # the labels always read 1/2, 2/3, 3/4 ... regardless of
            # which PDF page numbers the anchors originally came from.
            painter.drawText(8, y_vp - 4,
                             f"— page {seq} / {seq + 1} —")
            self._draw_folio(painter, y_vp, seq)
            painter.setPen(pen)
        self._draw_last_folio(painter, len(anchors) + 1)
        painter.end()


class PagedTextEdit(QTextEdit):
    """A QTextEdit that knows its page size, draws page-break lines and
    accepts pasted/dropped images.

    Image handling: when the user pastes from the clipboard or drops one
    or more image files onto the editor, each image is saved into the
    working images directory (set via `set_images_dir`) and an
    `imageReceived(str)` signal is emitted carrying the saved path. The
    DocumentEditor wires this up to insert a Figure block at the cursor.
    """

    imageReceived = Signal(str)
    documentDropped = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._page_height_px = 0
        self._page_width_px = 0
        # Number of pages in the most recent compiled PDF. The
        # overlay uses this (when >= 2) to position break lines
        # proportionally to the editor's actual content height —
        # much more accurate than the static page_height_px which
        # ignores LaTeX's text density. 0 = no compile yet → fall
        # back to the heuristic.
        self._pdf_page_count = 0
        # Raw [(page_no, snippet), ...] anchors handed in by the
        # compiler. Re-resolved into y-positions on every paint so
        # the lookup happens after the QTextDocument layout pass
        # has finished — resolving at set_page_anchors() time would
        # return y=0 for every anchor before the editor is shown.
        self._page_anchors: list[tuple[int, str]] = []
        self._images_dir: Path | None = None
        self._image_counter = 0
        self._overlay = _PageBreakOverlay(self)
        # Real pages replace the dashed "page N / N+1" break lines.
        self._overlay.hide()
        self.setAcceptDrops(True)

    def set_images_dir(self, path: Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self._images_dir = path

    def page_height_px(self) -> int:
        return self._page_height_px

    def pdf_page_count(self) -> int:
        return self._pdf_page_count

    def set_pdf_page_count(self, n: int) -> None:
        """Record the page count from the most recent successful PDF
        compile. The page-break overlay redraws using this to space
        its dashed indicator lines proportionally to the editor's
        content height. Called by MainWindow after each compile."""
        n = max(0, int(n))
        if n == self._pdf_page_count:
            return
        self._pdf_page_count = n
        self._overlay.update()

    def page_anchor_positions(self) -> list[tuple[int, float]]:
        """Lazily resolve the stored (page_no, snippet) anchors to
        (page_no, y_doc) on each request. Layout-dependent values
        like QTextLine geometry only become real after the editor
        has actually been painted, so we resolve at paint time
        rather than at set_page_anchors time.

        Returns the Y of the WRAPPED LINE the snippet sits on, not
        just the block top — that's the difference between "page
        break in the middle of this paragraph" (right) and "page
        break at the start of this paragraph" (wrong, what the
        previous version did)."""
        if not self._page_anchors:
            return []
        qdoc = self.document()
        layout = qdoc.documentLayout()
        resolved: list[tuple[int, float]] = []
        # Anchors are in page order, so each search resumes after the
        # previous hit: a phrase that also occurs earlier in the text
        # can't steal a later page's start.
        start = qdoc.firstBlock()
        for page_no, snippet in self._page_anchors:
            key = (snippet or "").strip()[:24]
            if not key:
                continue
            key_norm = _normalize_for_match(key)
            if len(key_norm) < 3:
                continue
            block = start
            while block.isValid():
                text = block.text().replace("\ufffc", "")
                idx = anchor_offset(text, key_norm)
                if idx >= 0:
                    block_rect = layout.blockBoundingRect(block)
                    if block_rect.height() > 0 or block_rect.top() > 0:
                        y_doc = block_rect.top()
                        # Refine with QTextLine: where inside this
                        # block is the matched substring drawn?
                        # A long paragraph that wraps over 5 lines
                        # in the editor needs the break line on the
                        # exact wrapped line that starts the PDF
                        # page, not the block's top.
                        blk_layout = block.layout()
                        if blk_layout is not None:
                            line = blk_layout.lineForTextPosition(idx)
                            if line.isValid():
                                y_doc = block_rect.top() + line.y()
                        resolved.append((int(page_no), float(y_doc)))
                        start = block
                    break
                block = block.next()
        return resolved

    def set_page_anchors(self,
                         anchors: list[tuple[int, str]]) -> None:
        """Receive [(page_no, first_text_snippet), ...] from the
        compiler. We store them as-is and resolve them to
        y-positions lazily on each paint (see
        `page_anchor_positions`)."""
        self._page_anchors = list(anchors or [])
        self._overlay.update()

    def set_page_size_px(self, width_px: int, height_px: int) -> None:
        """Lay the document out on real pages of this size, like Word:
        text that would cross a page's bottom margin moves to the next
        sheet, and each sheet is drawn separately with a gap between."""
        self._page_width_px = width_px
        self._page_height_px = height_px
        self._apply_pagination()
        self._overlay.update()

    def _apply_pagination(self) -> None:
        # QTextEdit resets the page height to "unlimited" whenever it
        # relays out (resize, wrap-mode change), which silently turns
        # pagination off; re-assert it afterwards.
        if self._page_height_px > 0:
            size = QSizeF(self.viewport().width() or self._page_width_px,
                          self._page_height_px)
            if self.document().pageSize() != size:
                self.document().setPageSize(size)

    def page_gap_px(self) -> int:
        """Grey gap drawn between sheets, scaled with the page."""
        return max(6, round(self._page_height_px * 0.011))

    def paintEvent(self, ev):
        super().paintEvent(ev)
        self._paint_sheets()
        self._paint_heading_numbers()

    def _sheet_labels(self, sheets: int) -> list[str]:
        """Footer label per sheet. After a compile each sheet is named
        for the PDF page it shows; a sheet that only exists because the
        editor's page overflowed (equation source, table notes...) reads
        "N (cont.)" so the numbering still matches the PDF."""
        H = self._page_height_px
        anchors = self.page_anchor_positions() if self._page_anchors else []
        if not anchors:
            return [str(k + 1) for k in range(sheets)]
        starts = {0: 1}
        for page_no, y in anchors:
            starts.setdefault(int(y // H), page_no)
        labels, current = [], 1
        for k in range(sheets):
            if k in starts:
                current = starts[k]
                labels.append(str(current))
            else:
                labels.append(f"{current} (cont.)")
        return labels

    def _paint_sheets(self) -> None:
        """Turn the paginated layout into separate sheets: desk-coloured
        gaps with a soft shadow between pages, an edge around each page,
        and the page number centred in each bottom margin (LaTeX's
        default plain page style)."""
        H = self._page_height_px
        doc = self.document()
        if H <= 0 or doc.pageSize().height() <= 0:
            return
        pages = max(1, doc.pageCount())
        dy = -self.verticalScrollBar().value()
        w = self.viewport().width()
        g = self.page_gap_px()
        bottom_margin = doc.rootFrame().frameFormat().bottomMargin()
        p = QPainter(self.viewport())
        font = self.font()
        font.setPointSizeF(max(6.0, font.pointSizeF() * 0.9))
        p.setFont(font)
        fm = p.fontMetrics()
        labels = self._sheet_labels(pages)
        for k in range(pages):
            top = k * H + dy + (g / 2 if k else 0)
            bottom = (k + 1) * H + dy - (g / 2 if k < pages - 1 else 1)
            if bottom < -H or top > self.viewport().height() + H:
                continue
            if k < pages - 1:
                gap = QRectF(0, bottom, w, g)
                p.fillRect(gap, DESK_COLOR)
                shade = QLinearGradient(0, bottom, 0, bottom + g * 0.6)
                shade.setColorAt(0, QColor(0, 0, 0, 55))
                shade.setColorAt(1, QColor(0, 0, 0, 0))
                p.fillRect(QRectF(0, bottom, w, g * 0.6), shade)
            p.setPen(QPen(_SHEET_EDGE, 1))
            p.drawRect(QRectF(0.5, top + 0.5, w - 1, bottom - top - 1))
            number = labels[k]
            p.setPen(QColor(90, 90, 90) if "cont" not in number
                     else QColor(170, 120, 60))
            y = (k + 1) * H + dy - bottom_margin / 2 + fm.ascent() / 2
            if k < pages - 1:
                y -= g / 2
            p.drawText(QPointF((w - fm.horizontalAdvance(number)) / 2, y),
                       number)
        p.end()

    def _paint_heading_numbers(self) -> None:
        doc = self.document()
        layout = doc.documentLayout()
        dx = -self.horizontalScrollBar().value()
        dy = -self.verticalScrollBar().value()
        visible = self.viewport().rect()
        painter = None
        block = doc.firstBlock()
        while block.isValid():
            number = block.blockFormat().property(HEADING_NUMBER_PROPERTY)
            if number:
                rect = layout.blockBoundingRect(block).translated(dx, dy)
                line = block.layout().lineAt(0) if block.layout() else None
                if line is not None and line.isValid() \
                        and rect.bottom() >= visible.top() \
                        and rect.top() <= visible.bottom():
                    if painter is None:
                        painter = QPainter(self.viewport())
                    it = block.begin()
                    if not it.atEnd():
                        cf = it.fragment().charFormat()
                        painter.setFont(cf.font())
                        painter.setPen(cf.foreground().color()
                                       if cf.hasProperty(QTextFormat.ForegroundBrush)
                                       else self.palette().text().color())
                    painter.drawText(
                        QPointF(rect.left(),
                                rect.top() + line.y() + line.ascent()),
                        str(number))
            block = block.next()
        if painter is not None:
            painter.end()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._apply_pagination()
        self._overlay.resize(self.viewport().size())

    # ----- paste / drop: route images through imageReceived signal -----

    def canInsertFromMimeData(self, source) -> bool:
        if source.hasImage():
            return True
        if source.hasUrls():
            for u in source.urls():
                local = u.toLocalFile()
                if local and Path(local).suffix.lower() in _IMAGE_SUFFIXES:
                    return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source) -> None:
        # Clipboard-image case: e.g. Snipping Tool, screenshots, Slack pastes.
        if source.hasImage():
            img = source.imageData()
            if isinstance(img, QImage) and not img.isNull():
                path = self._save_qimage(img)
                if path is not None:
                    self.imageReceived.emit(str(path))
                    return
        # File-URL case: Explorer drag-and-drop or copy from another app.
        if source.hasUrls():
            handled = False
            for u in source.urls():
                local = u.toLocalFile()
                if not local:
                    continue
                p = Path(local)
                if p.suffix.lower() in _IMAGE_SUFFIXES:
                    path = self._copy_local(p)
                    if path is not None:
                        self.imageReceived.emit(str(path))
                        handled = True
                elif _is_document_file(p):
                    self.documentDropped.emit(local)
                    handled = True
            if handled:
                return
        super().insertFromMimeData(source)

    def _next_image_filename(self, suffix: str) -> Path | None:
        if self._images_dir is None:
            return None
        suffix = suffix.lower() or ".png"
        while True:
            self._image_counter += 1
            candidate = self._images_dir / f"img_{self._image_counter:03d}{suffix}"
            if not candidate.exists():
                return candidate

    def _save_qimage(self, img: QImage) -> Path | None:
        path = self._next_image_filename(".png")
        if path is None:
            return None
        # PNG keeps clipboard quality without compression artefacts; tectonic
        # has no problem with it via \includegraphics.
        if img.save(str(path), "PNG"):
            return path
        return None

    def _copy_local(self, src: Path) -> Path | None:
        path = self._next_image_filename(src.suffix)
        if path is None:
            return None
        try:
            shutil.copy(src, path)
        except OSError:
            return None
        return path
