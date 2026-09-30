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
    QAbstractTextDocumentLayout, QColor, QImage, QLinearGradient,
    QMouseEvent, QPainter, QPen, QTextCharFormat, QTextCursor, QTextFormat,
)
from PySide6.QtCore import QTimer
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
    ".ktex", ".kdocz", ".ktexz", ".tex", ".md", ".markdown", ".docx",
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
EQUATION_NUMBER_PROPERTY = QTextFormat.UserProperty + 41



_PASTE_DPI = 300


def _clipboard_pdf(source) -> bytes | None:
    """The vector PDF flavour an Office app puts on the clipboard, if any."""
    for fmt in source.formats():
        if "pdf" in fmt.lower():
            data = bytes(source.data(fmt))
            if data.startswith(b"%PDF"):
                return data
    return None

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
    # A figure image was resized with the mouse: (doc position, w, h).
    imageResized = Signal(int, float, float)
    documentDropped = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._page_height_px = 0
        self._page_width_px = 0
        self._desk_color = QColor(DESK_COLOR)
        # Multi-column layout (1 = normal flow).
        self._columns = 1
        self._col_gap = 0.0
        self._col_left = 0.0
        self._col_width = 0.0
        self._caret_on = True
        # Mouse resizing of figure images. The editor decides which
        # images qualify (figures yes, typeset equations no).
        self.image_resizable = lambda fmt: False
        self._hover_img = None      # (doc pos, QRectF in view coords)
        self._img_drag = None       # (doc pos, start QPointF, w, h)
        self.viewport().setMouseTracking(True)
        # A hovered image's position goes stale as soon as text moves.
        self.textChanged.connect(self._forget_stale_hover)
        self._caret_timer = QTimer(self)
        self._caret_timer.timeout.connect(self._blink)
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
        # Printed number of the first sheet: a project document continues
        # from the pages of the documents before it.
        self._first_page = 1
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
            width = (self._col_width if self._columns > 1
                     else self.viewport().width() or self._page_width_px)
            size = QSizeF(width, self._page_height_px)
            if self.document().pageSize() != size:
                self.document().setPageSize(size)

    def set_desk_color(self, color: QColor) -> None:
        """Colour of the gaps between sheets — the theme's desk colour."""
        self._desk_color = QColor(color)
        self.viewport().update()

    # ----- multi-column layout -----
    #
    # QTextDocument has no columns, so the document is laid out on
    # "pages" one column wide and one sheet tall; page p is then drawn
    # as column p % n of sheet p // n. Mouse positions are mapped back
    # through the same arrangement, so editing works unchanged.

    def set_columns(self, n: int, gap_px: float, left_px: float,
                    right_px: float) -> None:
        n = max(1, int(n))
        width = self._page_width_px or self.viewport().width()
        col_w = (width - left_px - right_px - gap_px * (n - 1)) / n \
            if n > 1 else 0.0
        changed = (n, gap_px, left_px, col_w) != (
            self._columns, self._col_gap, self._col_left, self._col_width)
        self._columns, self._col_gap = n, gap_px
        self._col_left, self._col_width = left_px, col_w
        if n > 1:
            self._caret_timer.start(530)
        else:
            self._caret_timer.stop()
        if changed:
            self._apply_pagination()
            self.viewport().update()

    def columns(self) -> int:
        return self._columns

    def text_width_px(self) -> float:
        """Width available to a line of text (a column, when split)."""
        if self._columns > 1:
            return self._col_width
        fmt = self.document().rootFrame().frameFormat()
        # The page width, not the viewport's: before the widget is first
        # laid out the viewport is a stub ~100 px wide, and equations
        # capped to it at load time came out a fraction of their size.
        width = self._page_width_px or self.viewport().width()
        return width - fmt.leftMargin() - fmt.rightMargin()

    def sheet_count(self) -> int:
        pages = max(1, self.document().pageCount())
        return -(-pages // self._columns)

    def doc_to_view(self, x: float, y: float) -> QPointF:
        """Document-layout point -> viewport point."""
        dy = -self.verticalScrollBar().value()
        dx = -self.horizontalScrollBar().value()
        H = self._page_height_px
        if self._columns <= 1 or H <= 0:
            return QPointF(x + dx, y + dy)
        page = int(y // H)
        sheet, col = divmod(page, self._columns)
        vx = self._col_left + col * (self._col_width + self._col_gap) + x
        return QPointF(vx + dx, sheet * H + (y - page * H) + dy)

    def view_to_doc(self, pos) -> QPointF:
        """Viewport point -> document-layout point."""
        dy = self.verticalScrollBar().value()
        dx = self.horizontalScrollBar().value()
        H = self._page_height_px
        x, y = pos.x() + dx, pos.y() + dy
        if self._columns <= 1 or H <= 0:
            return QPointF(x, y)
        sheet = max(0, int(y // H))
        local = y - sheet * H
        step = self._col_width + self._col_gap
        col = int((x - self._col_left + self._col_gap / 2) // step) \
            if step > 0 else 0
        col = max(0, min(self._columns - 1, col))
        cx = x - self._col_left - col * step
        cx = max(0.0, min(self._col_width - 1, cx))
        page = sheet * self._columns + col
        return QPointF(cx, page * H + local)

    def _mapped(self, ev):
        if self._columns <= 1:
            return ev
        d = self.view_to_doc(ev.position())
        local = QPointF(d.x() - self.horizontalScrollBar().value(),
                        d.y() - self.verticalScrollBar().value())
        return QMouseEvent(ev.type(), local, ev.globalPosition(),
                           ev.button(), ev.buttons(), ev.modifiers())

    _HANDLE = 9.0

    def _image_under(self, view_pos):
        """(doc position, view rect) of a resizable image at view_pos."""
        doc = self.document()
        c = self.cursorForPosition(view_pos.toPoint())
        last = doc.characterCount() - 1
        for pos in (c.position(), c.position() - 1):
            if pos < 0 or pos + 1 > last:
                continue
            cc = QTextCursor(doc)
            cc.setPosition(pos)
            cc.setPosition(pos + 1, QTextCursor.KeepAnchor)
            fmt = cc.charFormat()
            if cc.selectedText() != "\ufffc" or not fmt.isImageFormat():
                continue
            if not self.image_resizable(fmt):
                return None
            rect = self._image_view_rect(pos, fmt.toImageFormat())
            if rect is not None and rect.adjusted(
                    -self._HANDLE, -self._HANDLE,
                    self._HANDLE, self._HANDLE).contains(view_pos):
                return pos, rect
        return None

    def _image_view_rect(self, pos: int, fmt):
        """Where an inline image is drawn, in viewport coordinates.

        Uses Qt's cursor rectangle, which accounts for table cells and
        frames: a block's own layout position is relative to its cell,
        so figures (which live in tables) were framed at the wrong place.
        An image sits on the line's top, so its box starts there."""
        c = QTextCursor(self.document())
        c.setPosition(pos)
        cr = QTextEdit.cursorRect(self, c)
        w, h = fmt.width(), fmt.height()
        if self._columns > 1:
            # cursorRect is in single-flow coordinates; re-map into columns.
            doc_pt = QPointF(cr.left() + self.horizontalScrollBar().value(),
                             cr.top() + self.verticalScrollBar().value())
            tl = self.doc_to_view(doc_pt.x(), doc_pt.y())
            return QRectF(tl.x(), tl.y(), w, h)
        return QRectF(cr.left(), cr.top(), w, h)

    def _handle_rect(self, rect: QRectF) -> QRectF:
        s = self._HANDLE
        return QRectF(rect.right() - s / 2, rect.bottom() - s / 2, s, s)

    def mousePressEvent(self, ev):
        hit = self._hover_img
        if (hit is not None and ev.button() == Qt.LeftButton
                and self._handle_rect(hit[1]).adjusted(-4, -4, 4, 4)
                .contains(ev.position())):
            pos, rect = hit
            self._img_drag = (pos, ev.position(), rect.width(), rect.height())
            ev.accept()
            return
        super().mousePressEvent(self._mapped(ev))

    def mouseMoveEvent(self, ev):
        if self._img_drag is not None:
            pos, start, w0, h0 = self._img_drag
            limit = max(40.0, self.text_width_px())
            w = max(24.0, min(limit, w0 + ev.position().x() - start.x()))
            self._set_image_size(pos, w, w * h0 / w0 if w0 else h0)
            ev.accept()
            return
        if not ev.buttons():
            hit = self._image_under(ev.position())
            if (hit is None) != (self._hover_img is None) or hit != self._hover_img:
                self._hover_img = hit
                self.viewport().update()
            on_handle = hit is not None and self._handle_rect(hit[1]) \
                .adjusted(-4, -4, 4, 4).contains(ev.position())
            if on_handle:
                self.viewport().setCursor(Qt.SizeFDiagCursor)
            else:
                self.viewport().unsetCursor()
        super().mouseMoveEvent(self._mapped(ev))

    def mouseReleaseEvent(self, ev):
        if self._img_drag is not None:
            pos = self._img_drag[0]
            self._img_drag = None
            cc = QTextCursor(self.document())
            cc.setPosition(pos)
            cc.setPosition(pos + 1, QTextCursor.KeepAnchor)
            f = cc.charFormat().toImageFormat()
            self.imageResized.emit(pos, f.width(), f.height())
            ev.accept()
            return
        super().mouseReleaseEvent(self._mapped(ev))

    def leaveEvent(self, ev):
        if self._hover_img is not None and self._img_drag is None:
            self._hover_img = None
            self.viewport().update()
        super().leaveEvent(ev)

    def _forget_stale_hover(self) -> None:
        if self._img_drag is None and self._hover_img is not None:
            self._hover_img = None
            self.viewport().update()

    def _set_image_size(self, pos: int, w: float, h: float) -> None:
        cc = QTextCursor(self.document())
        cc.setPosition(pos)
        cc.setPosition(pos + 1, QTextCursor.KeepAnchor)
        f = cc.charFormat().toImageFormat()
        f.setWidth(w)
        f.setHeight(h)
        cc.setCharFormat(f)
        rect = self._image_view_rect(pos, f)
        if rect is not None:
            self._hover_img = (pos, rect)
        self.viewport().update()

    def _paint_image_handles(self) -> None:
        if self._hover_img is None:
            return
        rect = self._hover_img[1]
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.Antialiasing)
        accent = self.palette().highlight().color()
        p.setPen(QPen(accent, 1, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        p.drawRect(rect.adjusted(-1, -1, 1, 1))
        p.setPen(QPen(QColor("white"), 1))
        p.setBrush(accent)
        p.drawRect(self._handle_rect(rect))
        p.end()

    def mouseDoubleClickEvent(self, ev):
        super().mouseDoubleClickEvent(self._mapped(ev))

    def cursorForPosition(self, pos):
        if self._columns <= 1:
            return super().cursorForPosition(pos)
        d = self.view_to_doc(pos)
        return super().cursorForPosition(QPointF(
            d.x() - self.horizontalScrollBar().value(),
            d.y() - self.verticalScrollBar().value()).toPoint())

    def _blink(self) -> None:
        self._caret_on = not self._caret_on
        self.viewport().update()

    def _paint_columns(self) -> None:
        """Draw each layout page as a column of its sheet (see above);
        QTextEdit's own painter only knows the single flow."""
        H = self._page_height_px
        doc = self.document()
        layout = doc.documentLayout()
        p = QPainter(self.viewport())
        p.fillRect(self.viewport().rect(), self.palette().base())
        ctx = QAbstractTextDocumentLayout.PaintContext()
        pal = self.palette()
        ctx.palette = pal
        cur = self.textCursor()
        if self.hasFocus() and self._caret_on and not self.isReadOnly():
            ctx.cursorPosition = cur.position()
        sels = []
        if cur.hasSelection():
            sel = QAbstractTextDocumentLayout.Selection()
            sel.cursor = cur
            fmt = QTextCharFormat()
            fmt.setBackground(pal.highlight())
            fmt.setForeground(pal.highlightedText())
            sel.format = fmt
            sels.append(sel)
        for extra in self.extraSelections():
            sel = QAbstractTextDocumentLayout.Selection()
            sel.cursor = extra.cursor
            sel.format = extra.format
            sels.append(sel)
        ctx.selections = sels
        vh = self.viewport().height()
        for page in range(max(1, doc.pageCount())):
            origin = self.doc_to_view(0, page * H)
            if origin.y() > vh or origin.y() + H < 0:
                continue
            p.save()
            p.setClipRect(QRectF(origin.x(), origin.y(),
                                 self._col_width, H))
            p.translate(origin.x(), origin.y() - page * H)
            ctx.clip = QRectF(0, page * H, self._col_width, H)
            layout.draw(p, ctx)
            p.restore()
        p.end()

    def page_gap_px(self) -> int:
        """Grey gap drawn between sheets, scaled with the page."""
        return max(6, round(self._page_height_px * 0.011))

    def paintEvent(self, ev):
        if self._columns > 1 and self._page_height_px > 0:
            self._paint_columns()
        else:
            super().paintEvent(ev)
        self._paint_sheets()
        self._paint_heading_numbers()
        self._paint_equation_numbers()
        self._paint_image_handles()

    def set_first_page_number(self, n: int) -> None:
        n = max(1, int(n or 1))
        if n != self._first_page:
            self._first_page = n
            self.viewport().update()

    def _sheet_labels(self, sheets: int) -> list[str]:
        """Footer label per sheet. After a compile each sheet is named
        for the PDF page it shows; a sheet that only exists because the
        editor's page overflowed (equation source, table notes...) reads
        "N (cont.)" so the numbering still matches the PDF."""
        H = self._page_height_px
        anchors = (self.page_anchor_positions()
                   if self._page_anchors and self._columns <= 1 else [])
        if not anchors:
            return [str(k + self._first_page) for k in range(sheets)]
        starts = {0: self._first_page}
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
        pages = self.sheet_count()
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
                p.fillRect(gap, self._desk_color)
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
                raw = layout.blockBoundingRect(block)
                line = block.layout().lineAt(0) if block.layout() else None
                at = self.doc_to_view(
                    raw.left(), raw.top() + (line.y() if line is not None
                                             and line.isValid() else 0))
                if line is not None and line.isValid() \
                        and at.y() + raw.height() >= visible.top() \
                        and at.y() <= visible.bottom():
                    if painter is None:
                        painter = QPainter(self.viewport())
                    it = block.begin()
                    if not it.atEnd():
                        cf = it.fragment().charFormat()
                        painter.setFont(cf.font())
                        painter.setPen(cf.foreground().color()
                                       if cf.hasProperty(QTextFormat.ForegroundBrush)
                                       else self.palette().text().color())
                    painter.drawText(QPointF(at.x(), at.y() + line.ascent()),
                                     str(number))
            block = block.next()
        if painter is not None:
            painter.end()

    def _paint_equation_numbers(self) -> None:
        """Right-align "(n)" against the text margin, vertically centred
        on the equation, as LaTeX places \\begin{equation} numbers."""
        doc = self.document()
        layout = doc.documentLayout()
        right = doc.textWidth() - doc.rootFrame().frameFormat().rightMargin()
        visible = self.viewport().rect()
        painter = None
        block = doc.firstBlock()
        while block.isValid():
            number = block.blockFormat().property(EQUATION_NUMBER_PROPERTY)
            if number:
                raw = layout.blockBoundingRect(block)
                bf = block.blockFormat()
                top = raw.top() + bf.topMargin()
                height = raw.height() - bf.topMargin() - bf.bottomMargin()
                at = self.doc_to_view(0, top)
                if at.y() + height >= visible.top() \
                        and at.y() <= visible.bottom():
                    if painter is None:
                        painter = QPainter(self.viewport())
                        painter.setFont(self.document().defaultFont())
                        painter.setPen(self.palette().text().color())
                    fm = painter.fontMetrics()
                    x = self.doc_to_view(
                        right - fm.horizontalAdvance(number), top).x()
                    y = at.y() + (height + fm.ascent() - fm.descent()) / 2
                    painter.drawText(QPointF(x, y), str(number))
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
        # Word / PowerPoint put a vector PDF beside a screen-resolution
        # bitmap; Qt's imageData() is that blurry bitmap, so render the
        # PDF ourselves when it's there.
        pdf = _clipboard_pdf(source)
        if pdf is not None:
            path = self._save_pdf_raster(pdf)
            if path is not None:
                self.imageReceived.emit(str(path))
                return
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

    def _save_pdf_raster(self, data: bytes) -> Path | None:
        path = self._next_image_filename(".png")
        if path is None:
            return None
        try:
            import fitz
            with fitz.open(stream=data, filetype="pdf") as pdf:
                pdf[0].get_pixmap(dpi=_PASTE_DPI, alpha=True).save(str(path))
        except Exception:
            return None
        return path

    def _copy_local(self, src: Path) -> Path | None:
        path = self._next_image_filename(src.suffix)
        if path is None:
            return None
        try:
            shutil.copy(src, path)
        except OSError:
            return None
        return path
