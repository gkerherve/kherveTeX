"""Programmatically-drawn toolbar icons.

QPainter draws each icon onto a transparent QPixmap so we never ship binary
image files. Every icon function returns a QIcon.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetricsF, QIcon, QPainter, QPainterPath,
    QPen, QPixmap, QPolygonF,
)

_SIZE = 24
_LINE_W = 2.0

# Mutable theme state — call set_dark() to switch.
_dark = False

def _fg() -> QColor:
    return QColor("#ddd") if _dark else QColor("#222")

def _accent() -> QColor:
    return QColor("#6cb4ff") if _dark else QColor("#1a6dd8")

def _accent2() -> QColor:
    return QColor("#f0a050") if _dark else QColor("#d96b00")

def set_dark(dark: bool) -> None:
    global _dark
    _dark = dark


def _new_canvas() -> tuple[QPixmap, QPainter]:
    px = QPixmap(_SIZE, _SIZE)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    return px, p


# The classic "LaTeX" logo drawn on the page: L, a raised small A, T, a
# lowered E, X. Each entry is (char, scale, baseline-shift, kern-after),
# all but the char in units of the cap size F, so the pieces kern like
# the real logo.
_LATEX_SERIF = "Times New Roman"
_LATEX_PIECES = (
    ("L", 1.00, 0.00, -0.28),
    ("A", 0.72, -0.32, -0.06),
    ("T", 1.00, 0.00, -0.13),
    ("E", 1.00, 0.24, -0.05),
    ("X", 1.00, 0.00, 0.00),
)


def _latex_advance(ch: str, px: float) -> float:
    f = QFont(_LATEX_SERIF)
    f.setPixelSize(max(1, int(px)))
    return QFontMetricsF(f).horizontalAdvance(ch)


def _latex_width(F: float) -> float:
    return sum(_latex_advance(ch, sc * F) + kern * F
               for ch, sc, _dy, kern in _LATEX_PIECES)


def _draw_latex(p: QPainter, cx: float, cy: float, avail: float,
                color: str) -> None:
    """Draw the classic LaTeX logo centred at (cx, cy), fit to *avail* wide."""
    F = 100.0
    F = avail / (_latex_width(F) / F)
    x = cx - _latex_width(F) / 2.0
    base = cy + 0.34 * F
    p.setPen(QColor(color))
    for ch, sc, dy, kern in _LATEX_PIECES:
        f = QFont(_LATEX_SERIF)
        f.setPixelSize(max(1, int(sc * F)))
        p.setFont(f)
        p.drawText(QPointF(x, base + dy * F), ch)
        x += _latex_advance(ch, sc * F) + kern * F


def _draw_ktex(p: QPainter, rect: QRectF, color: str) -> None:
    """Draw 'KTeX' centred in *rect* with a normal bold font, fit to width."""
    text = "KTeX"
    avail = rect.width() * 0.86
    font = QFont("Segoe UI")
    font.setBold(True)
    size = 4
    while size < rect.height():
        font.setPixelSize(size + 1)
        fm = QFontMetricsF(font)
        if fm.horizontalAdvance(text) > avail or fm.height() > rect.height():
            break
        size += 1
    font.setPixelSize(max(4, size))
    p.setFont(font)
    p.setPen(QColor(color))
    p.drawText(rect, Qt.AlignCenter, text)


def _draw_page(p: QPainter, box: QRectF) -> None:
    """A white document page with a folded corner, bearing the LaTeX logo."""
    x, y, w, h = box.x(), box.y(), box.width(), box.height()
    fold = w * 0.22
    page = QPainterPath()
    page.moveTo(x, y)
    page.lineTo(x + w - fold, y)
    page.lineTo(x + w, y + fold)
    page.lineTo(x + w, y + h)
    page.lineTo(x, y + h)
    page.closeSubpath()
    p.setPen(QPen(QColor("#cfd6e0"), max(1.0, w * 0.02)))
    p.setBrush(QColor("#ffffff"))
    p.drawPath(page)
    ear = QPainterPath()                       # the dog-ear fold
    ear.moveTo(x + w - fold, y)
    ear.lineTo(x + w - fold, y + fold)
    ear.lineTo(x + w, y + fold)
    p.setBrush(Qt.NoBrush)
    p.drawPath(ear)
    _draw_latex(p, x + w / 2, y + h * 0.58, w * 0.70, "#1a1a1a")


def app_pixmap(sz: int) -> QPixmap:
    """One size of the app icon: 'KTeX' above a page bearing the LaTeX
    logo, on a rounded blue tile."""
    px = QPixmap(sz, sz)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    m = sz * 0.06
    radius = sz * 0.22
    rect = QRectF(m, m, sz - 2 * m, sz - 2 * m)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#1a6dd8"))              # the blue tile
    p.drawRoundedRect(rect, radius, radius)
    pen = QPen(QColor("#155bb5"))
    pen.setWidthF(max(1.0, sz * 0.02))
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(rect, radius, radius)
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    _draw_ktex(p, QRectF(x, y + h * 0.05, w, h * 0.33), "#ffffff")
    pw, ph = w * 0.54, h * 0.48
    _draw_page(p, QRectF(x + (w - pw) / 2.0, y + h * 0.45, pw, ph))
    p.end()
    return px


def app_icon() -> QIcon:
    """Application icon: the 'KTeX' wordmark above a page bearing the
    LaTeX logo, on a rounded blue tile.

    Rendered at several sizes so the taskbar, title bar, and Alt-Tab all
    get a sharp copy.
    """
    icon = QIcon()
    for sz in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(app_pixmap(sz))
    return icon


# ----- text formatting -----


# ----- headings -----


# Word's Styles gallery: a sample in the style's own look over its name.
_STYLE_LOOK = {
    0: ("Georgia", 11, False, False, "fg"),       # Normal
    -1: ("Georgia", 14, False, False, "fg"),      # Title
    -2: ("Georgia", 10, False, True, "fg"),       # Author
    -7: ("Georgia", 9, False, True, "muted"),     # Affiliation
    -8: ("Georgia", 9, False, False, "muted"),    # Correspondence
    -3: ("Georgia", 10, True, False, "fg"),       # Abstract
    -4: ("Georgia", 9, False, True, "fg"),        # Keywords
    -6: ("Helvetica", 12, True, False, "accent"), # Frame
    -5: ("Georgia", 16, True, False, "accent"),   # Chapter
    1: ("Georgia", 15, True, False, "accent"),
    2: ("Georgia", 13, True, False, "accent"),
    3: ("Georgia", 12, True, False, "accent"),
    4: ("Georgia", 11, True, True, "accent"),
    5: ("Georgia", 10, False, True, "accent"),
}


def style_tile(level: int, name: str, w: int = 74, h: int = 46) -> QIcon:
    family, pt, bold_, italic_, tone = _STYLE_LOOK.get(
        level, _STYLE_LOOK[0])
    px = QPixmap(w * 2, h * 2)
    px.setDevicePixelRatio(2.0)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    color = {"fg": _fg(), "accent": _accent(),
             "muted": QColor("#999") if _dark else QColor("#666")}[tone]
    f = QFont(family); f.setPixelSize(pt + 2)
    f.setBold(bold_); f.setItalic(italic_)
    p.setFont(f); p.setPen(color)
    sample = QRect(0, 0, w, h - 15)
    p.drawText(sample, Qt.AlignCenter,
               QFontMetricsF(f).elidedText("AaBbCc", Qt.ElideRight, w - 4))
    if level in (1, -5):
        p.setPen(QPen(color, 1))
        p.drawLine(QPointF(8, h - 17.5), QPointF(w - 8, h - 17.5))
    lf = QFont(); lf.setPixelSize(10)
    p.setFont(lf); p.setPen(_fg())
    p.drawText(QRect(0, h - 14, w, 14), Qt.AlignCenter,
               QFontMetricsF(lf).elidedText(name, Qt.ElideRight, w - 2))
    p.end()
    return QIcon(px)


# ----- math -----


# ----- structure -----


# ----- file ops + history -----


# ----- alignment -----


# ---- equation builder category icons ----

def eq_fractions() -> QIcon:
    px, p = _new_canvas()
    p.setRenderHint(QPainter.Antialiasing, True)
    f = QFont("Cambria Math"); f.setPointSize(7); f.setItalic(True)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRect(4, 2, 16, 10), Qt.AlignCenter, "a+b")
    p.setPen(QPen(_fg(), 1.4)); p.drawLine(5, 12, 19, 12)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRect(4, 12, 16, 10), Qt.AlignCenter, "c")
    p.end()
    return QIcon(px)


def eq_sums() -> QIcon:
    px, p = _new_canvas()
    f = QFont("Cambria Math"); f.setPointSize(16)
    p.setFont(f); p.setPen(_accent())
    p.drawText(QRect(0, 0, _SIZE, _SIZE), Qt.AlignCenter, "\u03a3")
    p.end()
    return QIcon(px)


def eq_integrals() -> QIcon:
    px, p = _new_canvas()
    f = QFont("Cambria Math"); f.setPointSize(18)
    p.setFont(f); p.setPen(_accent())
    p.drawText(QRect(0, -1, _SIZE, _SIZE), Qt.AlignCenter, "\u222b")
    p.end()
    return QIcon(px)


def eq_scripts() -> QIcon:
    px, p = _new_canvas()
    f = QFont("Cambria Math"); f.setPointSize(12); f.setItalic(True)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRect(2, 4, 14, 16), Qt.AlignCenter, "x")
    f2 = QFont("Cambria Math"); f2.setPointSize(7); f2.setItalic(True)
    p.setFont(f2); p.setPen(_accent())
    p.drawText(QRect(13, 2, 10, 10), Qt.AlignLeft | Qt.AlignTop, "2")
    p.drawText(QRect(13, 12, 10, 10), Qt.AlignLeft | Qt.AlignTop, "i")
    p.end()
    return QIcon(px)


def eq_derivatives() -> QIcon:
    px, p = _new_canvas()
    f = QFont("Cambria Math"); f.setPointSize(8); f.setItalic(True)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRect(2, 2, 20, 10), Qt.AlignCenter, "dy")
    p.setPen(QPen(_fg(), 1.2)); p.drawLine(5, 12, 19, 12)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRect(2, 12, 20, 10), Qt.AlignCenter, "dx")
    p.end()
    return QIcon(px)


def eq_greek() -> QIcon:
    px, p = _new_canvas()
    f = QFont("Cambria Math"); f.setPointSize(11); f.setItalic(True)
    p.setFont(f); p.setPen(_accent())
    p.drawText(QRect(-2, 0, _SIZE, _SIZE), Qt.AlignCenter, "\u03b1\u03b2")
    p.end()
    return QIcon(px)


def eq_vectors() -> QIcon:
    px, p = _new_canvas()
    p.setRenderHint(QPainter.Antialiasing, True)
    # Arrow over x
    p.setPen(QPen(_accent(), 1.4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(6, 7, 18, 7)
    p.drawLine(15, 4, 18, 7); p.drawLine(15, 10, 18, 7)
    f = QFont("Cambria Math"); f.setPointSize(11); f.setItalic(True)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRect(0, 6, _SIZE, 16), Qt.AlignCenter, "x")
    p.end()
    return QIcon(px)


def eq_brackets() -> QIcon:
    px, p = _new_canvas()
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(_accent(), 1.6, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    # Left parenthesis arc
    p.drawArc(4, 3, 8, 18, 110 * 16, 140 * 16)
    # Right parenthesis arc
    p.drawArc(12, 3, 8, 18, -70 * 16, 140 * 16)
    p.end()
    return QIcon(px)


def eq_relations() -> QIcon:
    px, p = _new_canvas()
    f = QFont("Cambria Math"); f.setPointSize(12)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRect(0, 0, _SIZE, _SIZE), Qt.AlignCenter, "\u2264\u2265")
    p.end()
    return QIcon(px)


def eq_functions() -> QIcon:
    px, p = _new_canvas()
    f = QFont("Cambria Math"); f.setPointSize(10)
    p.setFont(f); p.setPen(_accent())
    p.drawText(QRect(0, 0, _SIZE, _SIZE), Qt.AlignCenter, "sin")
    p.end()
    return QIcon(px)


def eq_environments() -> QIcon:
    px, p = _new_canvas()
    p.setRenderHint(QPainter.Antialiasing, True)
    # Left brace
    p.setPen(QPen(_accent(), 1.6, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(8, 4, 6, 4); p.drawLine(6, 4, 6, 10)
    p.drawLine(6, 10, 4, 12); p.drawLine(4, 12, 6, 14)
    p.drawLine(6, 14, 6, 20); p.drawLine(6, 20, 8, 20)
    # Lines representing equation rows
    p.setPen(QPen(_fg(), 1.2, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(10, 8, 20, 8)
    p.drawLine(10, 12, 18, 12)
    p.drawLine(10, 16, 20, 16)
    p.end()
    return QIcon(px)


# ----- review -----


# ----- compile / auto-compile -----


# ----- drawing dialog (paint tools) -----
# Drawn on a 24-unit grid but rendered at 2x so the larger palette buttons
# stay crisp on hi-DPI screens.

def _paint_canvas() -> tuple[QPixmap, QPainter]:
    px = QPixmap(_SIZE * 2, _SIZE * 2)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    p.scale(2, 2)
    return px, p


def _pen(color, w=1.6) -> QPen:
    return QPen(color, w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)


def _fill_soft() -> QColor:
    c = QColor(_accent())
    c.setAlpha(60)
    return c


def _pt_pointer(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(_fg()))
    p.drawPolygon(QPolygonF([QPointF(6, 3), QPointF(6, 19), QPointF(10, 15),
                             QPointF(13, 21), QPointF(15.5, 20),
                             QPointF(12.5, 14), QPointF(18, 14)]))


def _pt_pencil(p):
    p.setPen(_pen(_fg(), 1.3)); p.setBrush(QBrush(_accent2()))
    p.drawPolygon(QPolygonF([QPointF(16, 3), QPointF(21, 8), QPointF(9, 20),
                             QPointF(4, 15)]))
    p.setBrush(QBrush(_fg()))
    p.drawPolygon(QPolygonF([QPointF(4, 15), QPointF(9, 20), QPointF(3, 21)]))
    p.setPen(_pen(_fg(), 1.1))
    p.drawLine(QPointF(14, 5), QPointF(19, 10))


def _pt_eraser(p):
    p.setPen(_pen(_fg(), 1.3))
    p.setBrush(QBrush(QColor("#f28b9b")))
    p.drawPolygon(QPolygonF([QPointF(13, 3), QPointF(21, 11), QPointF(14, 18),
                             QPointF(6, 10)]))
    p.setBrush(QBrush(QColor("#ffffff") if not _dark else QColor("#666")))
    p.drawPolygon(QPolygonF([QPointF(6, 10), QPointF(14, 18), QPointF(11, 21),
                             QPointF(7, 21), QPointF(3, 17), QPointF(3, 13)]))
    p.drawLine(QPointF(11, 21), QPointF(21, 21))


def _pt_bucket(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(_fill_soft()))
    p.drawPolygon(QPolygonF([QPointF(10, 3), QPointF(18, 11), QPointF(11, 18),
                             QPointF(3, 10)]))
    p.drawLine(QPointF(10, 3), QPointF(8, 1.5))
    p.setPen(Qt.NoPen); p.setBrush(QBrush(_accent()))
    path = QPainterPath(QPointF(19.5, 13))
    path.cubicTo(QPointF(22, 17), QPointF(22.5, 20), QPointF(19.5, 20.5))
    path.cubicTo(QPointF(16.5, 20), QPointF(17, 17), QPointF(19.5, 13))
    p.drawPath(path)


def _pt_picker(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(_fg()))
    p.drawEllipse(QPointF(18, 6), 3.2, 3.2)
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(15, 7), QPointF(17, 9))
    p.setPen(_pen(_fg(), 2.2))
    p.drawLine(QPointF(15.5, 8.5), QPointF(6, 18))
    p.setPen(_pen(_accent(), 2.2))
    p.drawLine(QPointF(6, 18), QPointF(4, 20))


def _pt_line(p):
    p.setPen(_pen(_fg(), 2.0))
    p.drawLine(QPointF(4, 20), QPointF(20, 4))
    p.setBrush(QBrush(_accent())); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(4, 20), 2, 2); p.drawEllipse(QPointF(20, 4), 2, 2)


def _pt_arrow(p):
    p.setPen(_pen(_fg(), 2.0))
    p.drawLine(QPointF(4, 20), QPointF(17, 7))
    p.setBrush(QBrush(_fg()))
    p.drawPolygon(QPolygonF([QPointF(21, 3), QPointF(19.5, 12),
                             QPointF(12, 4.5)]))


def _pt_dimension(p):
    p.setPen(_pen(_fg(), 1.3))
    p.drawLine(QPointF(3, 7), QPointF(3, 19)); p.drawLine(QPointF(21, 7), QPointF(21, 19))
    p.drawLine(QPointF(4, 13), QPointF(20, 13))
    p.setBrush(QBrush(_fg()))
    p.drawPolygon(QPolygonF([QPointF(4, 13), QPointF(8, 11), QPointF(8, 15)]))
    p.drawPolygon(QPolygonF([QPointF(20, 13), QPointF(16, 11), QPointF(16, 15)]))
    f = QFont(); f.setPixelSize(7); f.setBold(True); p.setFont(f)
    p.setPen(_accent())
    p.drawText(QRectF(4, 3, 16, 9), Qt.AlignCenter, "mm")


def _pt_protractor(p):
    p.setPen(_pen(_fg(), 1.5)); p.setBrush(QBrush(_fill_soft()))
    path = QPainterPath(QPointF(3, 19))
    path.arcTo(QRectF(3, 5, 18, 28), 180, -180)
    path.closeSubpath()
    p.drawPath(path)
    p.setPen(_pen(_accent(), 1.5))
    p.drawLine(QPointF(12, 19), QPointF(17, 9))


def _pt_shape(p, kind):
    p.setPen(_pen(_fg(), 1.7)); p.setBrush(QBrush(_fill_soft()))
    box = QRectF(3.5, 5.5, 17, 13)
    if kind == "rect":
        p.drawRect(box)
    elif kind == "roundrect":
        p.drawRoundedRect(box, 4, 4)
    elif kind == "circle":
        p.drawEllipse(QRectF(4, 4, 16, 16))
    elif kind == "ellipse":
        p.drawEllipse(QRectF(2.5, 6.5, 19, 11))
    else:
        from .paint import canvas
        r = QRectF(3.5, 3.5, 17, 17)
        if kind in canvas.ARC_KINDS:
            p.drawPath(canvas.arc_path(kind, r))
        else:
            p.drawPolygon(canvas.polygon_for_kind(kind, r))


def _pt_text(p):
    f = QFont("Georgia"); f.setPixelSize(19); f.setBold(True)
    p.setFont(f); p.setPen(_fg())
    p.drawText(QRectF(0, 0, 24, 24), Qt.AlignCenter, "T")
    p.setPen(_pen(_accent(), 1.2))
    p.drawLine(QPointF(19, 5), QPointF(19, 19))


def _pt_image(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(3, 4, 18, 16), 2, 2)
    p.setBrush(QBrush(_accent())); p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([QPointF(4.5, 18.5), QPointF(10, 11),
                             QPointF(14, 15.5), QPointF(16, 13.5),
                             QPointF(19.5, 18.5)]))
    p.setBrush(QBrush(_accent2()))
    p.drawEllipse(QPointF(16, 8.5), 2, 2)


def _pt_group(p, ungroup=False):
    p.setPen(QPen(_accent(), 1.2, Qt.DashLine)); p.setBrush(Qt.NoBrush)
    if not ungroup:
        p.drawRect(QRectF(2.5, 2.5, 19, 19))
    p.setPen(_pen(_fg(), 1.5)); p.setBrush(QBrush(_fill_soft()))
    d = 1.5 if ungroup else 0
    p.drawRect(QRectF(5 - d, 5 - d, 8, 8))
    p.drawEllipse(QRectF(11 + d, 11 + d, 8, 8))


def _pt_zorder(p, up: bool, full: bool):
    back = QColor("#b9c3cf") if not _dark else QColor("#666")
    front = _accent()
    p.setPen(_pen(_fg(), 1.2))
    lo, hi = (QRectF(3, 9, 11, 11), QRectF(10, 4, 11, 11))
    p.setBrush(QBrush(back if up else front)); p.drawRect(lo if up else hi)
    p.setBrush(QBrush(front if up else back)); p.drawRect(hi if up else lo)
    if full:
        p.setPen(_pen(_fg(), 1.6))
        y = 2 if up else 22
        p.drawLine(QPointF(3, y), QPointF(8, y))


def _pt_copy(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(4, 3, 11, 13), 1.5, 1.5)
    p.setBrush(QBrush(QColor("#ffffff") if not _dark else QColor("#333")))
    p.drawRoundedRect(QRectF(9, 8, 11, 13), 1.5, 1.5)


def _pt_paste(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(_fill_soft()))
    p.drawRoundedRect(QRectF(4, 4, 16, 18), 2, 2)
    p.setBrush(QBrush(_fg()))
    p.drawRoundedRect(QRectF(8.5, 2, 7, 4), 1, 1)


def _pt_duplicate(p):
    _pt_copy(p)
    p.setPen(_pen(_accent(), 1.6))
    p.drawLine(QPointF(14.5, 11.5), QPointF(14.5, 17.5))
    p.drawLine(QPointF(11.5, 14.5), QPointF(17.5, 14.5))


def _pt_delete(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(4, 6), QPointF(20, 6))
    p.drawRect(QRectF(9.5, 3, 5, 3))
    p.drawPolygon(QPolygonF([QPointF(6, 6), QPointF(18, 6), QPointF(17, 21),
                             QPointF(7, 21)]))
    p.drawLine(QPointF(10, 9.5), QPointF(10, 18))
    p.drawLine(QPointF(14, 9.5), QPointF(14, 18))


def _pt_grid(p):
    p.setPen(_pen(_fg(), 1.0))
    for v in (4, 10, 16, 22):
        p.drawLine(QPointF(v - 1, 3), QPointF(v - 1, 21))
        p.drawLine(QPointF(3, v - 1), QPointF(21, v - 1))


def _pt_snap(p):
    _pt_grid(p)
    p.setPen(Qt.NoPen); p.setBrush(QBrush(_accent()))
    p.drawEllipse(QPointF(9, 9), 3, 3)


def _pt_fit(p):
    p.setPen(QPen(_accent(), 1.2, Qt.DashLine)); p.setBrush(Qt.NoBrush)
    p.drawRect(QRectF(6, 6, 12, 12))
    p.setPen(_pen(_fg(), 1.6))
    for (x, y, dx, dy) in ((3, 3, 1, 1), (21, 3, -1, 1), (3, 21, 1, -1),
                           (21, 21, -1, -1)):
        p.drawLine(QPointF(x, y), QPointF(x + 4 * dx, y))
        p.drawLine(QPointF(x, y), QPointF(x, y + 4 * dy))


def _pt_flip(p, vertical=False):
    if vertical:
        p.translate(24, 0); p.rotate(90)
    p.setPen(QPen(_fg(), 1.1, Qt.DashLine))
    p.drawLine(QPointF(12, 2), QPointF(12, 22))
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(_fg()))
    p.drawPolygon(QPolygonF([QPointF(10, 5), QPointF(10, 19), QPointF(3, 19)]))
    p.setBrush(QBrush(_fill_soft()))
    p.drawPolygon(QPolygonF([QPointF(14, 5), QPointF(14, 19), QPointF(21, 19)]))


def _pt_rotate(p):
    p.setPen(_pen(_fg(), 1.8)); p.setBrush(Qt.NoBrush)
    path = QPainterPath(QPointF(19, 12))
    path.arcTo(QRectF(5, 5, 14, 14), 0, 270)
    p.drawPath(path)
    p.setBrush(QBrush(_fg())); p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([QPointF(15.5, 2), QPointF(15.5, 10),
                             QPointF(9.5, 5.5)]))


def _pt_explode(p):
    p.setPen(_pen(_fg(), 1.6))
    p.drawLine(QPointF(3, 8), QPointF(10, 3))
    p.drawLine(QPointF(14, 3), QPointF(21, 8))
    p.drawLine(QPointF(21, 13), QPointF(21, 21))
    p.drawLine(QPointF(3, 13), QPointF(3, 21))
    p.drawLine(QPointF(7, 21), QPointF(17, 21))


def _pt_flowchart(p):
    p.setPen(_pen(_fg(), 1.3)); p.setBrush(QBrush(_fill_soft()))
    p.drawRoundedRect(QRectF(7, 1.5, 10, 5), 2.5, 2.5)
    p.drawPolygon(QPolygonF([QPointF(12, 9), QPointF(17, 12.5),
                             QPointF(12, 16), QPointF(7, 12.5)]))
    p.drawRect(QRectF(7, 18.5, 10, 4.5))
    p.drawLine(QPointF(12, 6.5), QPointF(12, 9))
    p.drawLine(QPointF(12, 16), QPointF(12, 18.5))


def _pt_electrical(p):
    p.setPen(_pen(_fg(), 1.5)); p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(2, 12), QPointF(6, 12))
    p.drawPolyline(QPolygonF([QPointF(6, 12), QPointF(7.5, 8), QPointF(10, 16),
                              QPointF(12.5, 8), QPointF(15, 16),
                              QPointF(17.5, 8), QPointF(18.5, 12)]))
    p.drawLine(QPointF(18.5, 12), QPointF(22, 12))


def _pt_optics(p):
    p.setPen(_pen(QColor("#d8000c"), 1.4))
    p.drawLine(QPointF(2, 8), QPointF(12, 12)); p.drawLine(QPointF(2, 16), QPointF(12, 12))
    p.drawLine(QPointF(12, 12), QPointF(22, 12))
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(_fill_soft()))
    path = QPainterPath(QPointF(9, 3))
    path.quadTo(QPointF(14, 12), QPointF(9, 21))
    path.quadTo(QPointF(4, 12), QPointF(9, 3))
    p.drawPath(path)


def _pt_maths(p):
    p.setPen(_pen(_fg(), 1.3))
    p.drawLine(QPointF(3, 21), QPointF(21, 21)); p.drawLine(QPointF(3, 21), QPointF(3, 3))
    p.setPen(_pen(_accent(), 1.6)); p.setBrush(Qt.NoBrush)
    path = QPainterPath(QPointF(4, 19))
    path.cubicTo(QPointF(9, 19), QPointF(10, 4), QPointF(13, 4))
    path.cubicTo(QPointF(16, 4), QPointF(17, 17), QPointF(21, 17))
    p.drawPath(path)


def _pt_callout(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(_fill_soft()))
    path = QPainterPath()
    path.addRoundedRect(QRectF(2.5, 3, 19, 12), 3, 3)
    tail = QPainterPath()
    tail.addPolygon(QPolygonF([QPointF(7, 14), QPointF(6, 21), QPointF(12, 14)]))
    p.drawPath(path.united(tail))


def _pt_labware(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(Qt.NoBrush)
    outline = QPolygonF([QPointF(9, 2.5), QPointF(9, 9), QPointF(3.5, 20),
                         QPointF(4.5, 21.5), QPointF(19.5, 21.5),
                         QPointF(20.5, 20), QPointF(15, 9), QPointF(15, 2.5)])
    p.setBrush(QBrush(_fill_soft()))
    p.drawPolygon(outline)
    p.setPen(_pen(_accent(), 1.2))
    p.drawLine(QPointF(6.5, 15.5), QPointF(17.5, 15.5))


def _pt_chemistry(p):
    import math
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(Qt.NoBrush)
    pts = [QPointF(12 + 8.5 * math.cos(math.radians(90 + 60 * k)),
                   12 + 8.5 * math.sin(math.radians(90 + 60 * k)))
           for k in range(6)]
    p.drawPolygon(QPolygonF(pts))
    p.setPen(_pen(_accent(), 1.3))
    p.drawEllipse(QPointF(12, 12), 4.8, 4.8)


def _pt_canvas(p):
    p.setPen(_pen(_fg(), 1.4)); p.setBrush(QBrush(QColor("#ffffff")))
    p.drawRect(QRectF(5, 5, 14, 14))
    p.setPen(_pen(_accent(), 1.4))
    p.drawLine(QPointF(2, 5), QPointF(2, 19)); p.drawLine(QPointF(5, 22), QPointF(19, 22))


_PAINT_TOOLS = {
    "pointer": _pt_pointer, "pencil": _pt_pencil, "eraser": _pt_eraser,
    "bucket": _pt_bucket, "picker": _pt_picker, "line": _pt_line,
    "arrow": _pt_arrow, "dimension": _pt_dimension,
    "protractor": _pt_protractor, "text": _pt_text, "image": _pt_image,
    "group": _pt_group, "ungroup": lambda p: _pt_group(p, True),
    "front": lambda p: _pt_zorder(p, True, True),
    "forward": lambda p: _pt_zorder(p, True, False),
    "backward": lambda p: _pt_zorder(p, False, False),
    "back": lambda p: _pt_zorder(p, False, True),
    "copy": _pt_copy, "paste": _pt_paste, "duplicate": _pt_duplicate,
    "delete": _pt_delete, "grid": _pt_grid, "snap": _pt_snap, "fit": _pt_fit,
    "flip_h": _pt_flip, "flip_v": lambda p: _pt_flip(p, True),
    "rotate": _pt_rotate, "explode": _pt_explode,
    "flowchart": _pt_flowchart, "electrical": _pt_electrical,
    "optics": _pt_optics, "maths": _pt_maths, "arrows": _pt_callout,
    "labware": _pt_labware, "chemistry": _pt_chemistry, "canvas": _pt_canvas,
}


def paint_tool(name: str) -> QIcon:
    """Icon for a drawing-dialog tool or action. Shape tools (rect, circle,
    polygons, arcs…) are drawn from the shape's own geometry."""
    px, p = _paint_canvas()
    fn = _PAINT_TOOLS.get(name)
    if fn is not None:
        fn(p)
    else:
        _pt_shape(p, name)
    p.end()
    return QIcon(px)


def color_swatch(color: str, size: int = 16, *, none: bool = False) -> QIcon:
    """A rounded colour chip; *none* draws the "no colour" red slash."""
    px = QPixmap(size * 2, size * 2)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(2, 2)
    r = QRectF(1, 1, size - 2, size - 2)
    p.setPen(QPen(QColor("#777"), 1))
    p.setBrush(QBrush(QColor("#ffffff") if none else QColor(color)))
    p.drawRoundedRect(r, 3, 3)
    if none:
        p.setPen(QPen(QColor("#d8000c"), 1.6))
        p.drawLine(r.bottomLeft() + QPointF(2, -2), r.topRight() + QPointF(-2, 2))
    p.end()
    return QIcon(px)


def pen_preview(width: float = 2.0, dash: str = "solid", head: str = "",
                length: int = 44) -> QIcon:
    """A short stroke sample for the width / dash / arrowhead pickers."""
    h = 16
    px = QPixmap(length * 2, h * 2)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(2, 2)
    styles = {"solid": Qt.SolidLine, "dash": Qt.DashLine, "dot": Qt.DotLine,
              "dashdot": Qt.DashDotLine}
    pen = QPen(_fg(), min(width, h - 4), styles.get(dash, Qt.SolidLine),
               Qt.FlatCap if dash != "dot" else Qt.RoundCap)
    p.setPen(pen)
    x0, x1 = 3.0, length - 3.0
    if head:
        x1 -= 4
        if head == "double":
            x0 += 4
    p.drawLine(QPointF(x0, h / 2), QPointF(x1, h / 2))
    if head:
        p.setPen(_pen(_fg(), 1.3))

        def tip(x, sign):
            a, b = QPointF(x - sign * 8, h / 2 - 4.5), QPointF(x - sign * 8, h / 2 + 4.5)
            if head == "open":
                p.setBrush(Qt.NoBrush)
                p.drawPolyline(QPolygonF([a, QPointF(x, h / 2), b]))
            elif head == "stealth":
                p.setBrush(QBrush(_fg()))
                p.drawPolygon(QPolygonF([QPointF(x, h / 2), a,
                                         QPointF(x - sign * 5, h / 2), b]))
            else:
                p.setBrush(QBrush(_fg()))
                p.drawPolygon(QPolygonF([QPointF(x, h / 2), a, b]))
        tip(length - 2.0, 1)
        if head == "double":
            tip(2.0, -1)
    p.end()
    return QIcon(px)


# ----- document-class gallery -----

_TWO_COL = {"ieeetran", "revtex4-2", "acmart", "aa", "mnras", "svjour3",
            "sn-jnl", "elsarticle", "achemso"}
_BOOKISH = {"book", "report", "memoir", "scrbook", "scrreprt", "amsbook",
            "elegantbook", "mimosis", "hepthesis", "suftesi", "toptesi",
            "disser"}


def class_thumbnail(cls: str, w: int = 52, h: int = 66) -> QIcon:
    """A miniature first page showing the class's layout, like the page
    previews in Word's template picker."""
    c = (cls or "").lower()
    px = QPixmap(w * 2, h * 2)
    px.setDevicePixelRatio(2.0)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    ink = QColor("#8a8a8a") if not _dark else QColor("#9a9a9a")
    acc = _accent()
    page = QRectF(4, 2, w - 8, h - 4)
    if c == "beamer":
        page = QRectF(2, h / 2 - (w - 4) * 0.375, w - 4, (w - 4) * 0.75)
    elif c == "standalone":
        page = QRectF(10, h / 2 - 12, w - 20, 24)
    p.setPen(QPen(QColor("#999"), 0.8))
    p.setBrush(QColor("#fff") if not _dark else QColor("#2b2b2b"))
    p.drawRect(page)
    x0, y0, pw = page.left() + 4, page.top() + 4, page.width() - 8

    def lines(x, y, width, n, step=3.2, last=0.6):
        p.setPen(QPen(ink, 1))
        for k in range(n):
            ww = width * (last if k == n - 1 else 1)
            p.drawLine(QPointF(x, y + k * step), QPointF(x + ww, y + k * step))

    def bar(x, y, width, height, color):
        p.setPen(Qt.NoPen); p.setBrush(color)
        p.drawRect(QRectF(x, y, width, height))

    if c == "beamer":
        bar(page.left(), page.top(), page.width(), 7, acc)
        p.setPen(QPen(ink, 1))
        for k in range(3):
            yy = page.top() + 12 + k * 5
            p.drawEllipse(QPointF(x0 + 1, yy), 0.8, 0.8)
            p.drawLine(QPointF(x0 + 4, yy), QPointF(x0 + pw * 0.8, yy))
    elif c in ("letter", "scrlttr2"):
        lines(x0 + pw * 0.55, y0, pw * 0.45, 3, last=1)
        lines(x0, y0 + 13, pw * 0.4, 3, last=1)
        lines(x0, y0 + 26, pw, 8)
    elif c in ("moderncv", "europasscv"):
        bar(x0, y0, pw * 0.6, 4, acc)
        for k in range(4):
            yy = y0 + 10 + k * 12
            bar(x0, yy, pw * 0.25, 2, acc)
            lines(x0 + pw * 0.32, yy + 1, pw * 0.68, 3, last=0.8)
    elif c in ("tikzposter", "a0poster"):
        bar(page.left(), page.top(), page.width(), 9, acc)
        p.setPen(QPen(acc, 0.8)); p.setBrush(Qt.NoBrush)
        half = (pw - 2) / 2
        for col in range(2):
            for row in range(2):
                p.drawRect(QRectF(x0 + col * (half + 2), y0 + 9 + row * 24,
                                  half, 21))
    elif c == "standalone":
        p.setPen(QPen(acc, 1.2)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(page.center().x() - 4, page.center().y()), 5, 5)
        p.drawRect(QRectF(page.center().x() + 1, page.center().y() - 4, 8, 8))
    elif c.startswith("tufte"):
        bar(x0, y0, pw * 0.6, 3, ink)
        lines(x0, y0 + 9, pw * 0.65, 12)
        p.setPen(QPen(ink, 0.6))
        for k in (0, 1, 3):
            yy = y0 + 10 + k * 8
            p.drawLine(QPointF(x0 + pw * 0.75, yy), QPointF(x0 + pw, yy))
            p.drawLine(QPointF(x0 + pw * 0.75, yy + 2),
                       QPointF(x0 + pw * 0.92, yy + 2))
    elif c in _BOOKISH:
        f = QFont("Georgia"); f.setPixelSize(7); f.setBold(True)
        p.setFont(f); p.setPen(acc)
        p.drawText(QPointF(x0, y0 + 10), "Chapter 1")
        bar(x0, y0 + 14, pw, 0.8, acc)
        lines(x0, y0 + 21, pw, 10)
    elif c == "exam":
        f = QFont(); f.setPixelSize(5); f.setBold(True)
        p.setFont(f)
        for k in range(4):
            yy = y0 + 4 + k * 13
            p.setPen(acc); p.drawText(QPointF(x0, yy + 2), f"{k + 1}.")
            lines(x0 + 6, yy, pw - 6, 3, last=0.5)
    else:
        bar(x0 + pw * 0.15, y0, pw * 0.7, 3, ink)
        lines(x0 + pw * 0.3, y0 + 6, pw * 0.4, 1, last=1)
        if c in {x.lower() for x in _TWO_COL} or c == "ieeetran":
            col = (pw - 3) / 2
            lines(x0, y0 + 13, col, 12)
            lines(x0 + col + 3, y0 + 13, col, 12)
        else:
            lines(x0 + pw * 0.1, y0 + 12, pw * 0.8, 2, last=1)
            bar(x0, y0 + 21, pw * 0.4, 1.8, acc)
            lines(x0, y0 + 26, pw, 9)
    p.end()
    return QIcon(px)


def numbered_heading_tile(w: int = 70, h: int = 40) -> QIcon:
    """Toggle tile for numbered headings, drawn like the style tiles."""
    px = QPixmap(w * 2, h * 2)
    px.setDevicePixelRatio(2.0)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    f = QFont("Georgia"); f.setPixelSize(13); f.setBold(True)
    p.setFont(f); p.setPen(_accent())
    p.drawText(QRect(0, 0, w, h - 15), Qt.AlignCenter, "1.2 Aa")
    lf = QFont(); lf.setPixelSize(10)
    p.setFont(lf); p.setPen(_fg())
    p.drawText(QRect(0, h - 14, w, 14), Qt.AlignCenter, "Numbered")
    p.end()
    return QIcon(px)


# =====================================================================
# Word-style toolbar icons
# ---------------------------------------------------------------------
# Drawn in the look of Office's Fluent icons so Word users recognise
# them: thin grey outlines, Word blue for the meaningful part, a single
# light fill. Painted at 2x so they stay crisp on high-DPI screens.
# =====================================================================

_WORD_BLUE = "#2b579a"


def _ink() -> QColor:
    return QColor("#d6d6d6") if _dark else QColor("#424242")


def _blue() -> QColor:
    return QColor("#7aa7e8") if _dark else QColor(_WORD_BLUE)


def _paper() -> QColor:
    return QColor("#3a3a3a") if _dark else QColor("#ffffff")


def _tint() -> QColor:
    return QColor("#2f4a70") if _dark else QColor("#dce8f7")


class _W:
    """A 24-unit canvas drawn at 2x, with Fluent-style strokes."""

    def __init__(self) -> None:
        self.px = QPixmap(_SIZE * 2, _SIZE * 2)
        self.px.setDevicePixelRatio(2.0)
        self.px.fill(Qt.transparent)
        self.p = QPainter(self.px)
        self.p.setRenderHint(QPainter.Antialiasing, True)
        self.p.setRenderHint(QPainter.TextAntialiasing, True)

    def pen(self, color=None, w: float = 1.5) -> "_W":
        self.p.setPen(QPen(color or _ink(), w, Qt.SolidLine, Qt.RoundCap,
                           Qt.RoundJoin))
        return self

    def brush(self, color=None) -> "_W":
        self.p.setBrush(color if color is not None else Qt.NoBrush)
        return self

    def line(self, x1, y1, x2, y2, color=None, w: float = 1.5) -> None:
        self.pen(color, w)
        self.p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def rect(self, x, y, w, h, color=None, fill=None, r: float = 1.5,
             lw: float = 1.5) -> None:
        self.pen(color, lw).brush(fill)
        self.p.drawRoundedRect(QRectF(x, y, w, h), r, r)

    def fillrect(self, x, y, w, h, color) -> None:
        self.p.setPen(Qt.NoPen); self.p.setBrush(color)
        self.p.drawRect(QRectF(x, y, w, h))

    def poly(self, pts, color=None, fill=None, lw: float = 1.5,
             closed: bool = True) -> None:
        self.pen(color, lw).brush(fill)
        poly = QPolygonF([QPointF(x, y) for x, y in pts])
        if closed:
            self.p.drawPolygon(poly)
        else:
            self.p.drawPolyline(poly)

    def dot(self, x, y, r=1.4, color=None) -> None:
        self.p.setPen(Qt.NoPen); self.p.setBrush(color or _ink())
        self.p.drawEllipse(QPointF(x, y), r, r)

    def text(self, rect, s: str, *, size: float = 15, bold=False,
             italic=False, color=None, family="Segoe UI",
             align=Qt.AlignCenter) -> None:
        f = QFont(family)
        f.setStyleHint(QFont.SansSerif)
        f.setPixelSize(int(size)); f.setBold(bold); f.setItalic(italic)
        self.p.setFont(f); self.p.setPen(color or _ink())
        self.p.drawText(QRectF(*rect), align, s)

    def page(self, x=5, y=2.5, w=14, h=19, fold: float = 4) -> None:
        """Document sheet with a folded corner."""
        self.poly([(x, y), (x + w - fold, y), (x + w, y + fold),
                   (x + w, y + h), (x, y + h)], fill=_paper())
        self.poly([(x + w - fold, y), (x + w - fold, y + fold),
                   (x + w, y + fold)], closed=False)

    def done(self) -> QIcon:
        self.p.end()
        return QIcon(self.px)


# ----- file -----

def file_new() -> QIcon:
    c = _W(); c.page()
    c.line(16, 15, 16, 21, _blue(), 1.8); c.line(13, 18, 19, 18, _blue(), 1.8)
    return c.done()


def file_open() -> QIcon:
    c = _W()
    c.poly([(2.5, 6), (8.5, 6), (10.5, 8), (20, 8), (20, 19.5), (2.5, 19.5)],
           fill=QColor("#f6c85f") if not _dark else QColor("#a8862e"))
    c.poly([(2.5, 19.5), (5.5, 11.5), (22, 11.5), (19.5, 19.5)],
           fill=QColor("#ffdd80") if not _dark else QColor("#c9a040"))
    return c.done()


def file_save() -> QIcon:
    c = _W()
    c.poly([(3.5, 3.5), (17, 3.5), (20.5, 7), (20.5, 20.5), (3.5, 20.5)],
           fill=_blue(), color=_blue())
    c.fillrect(7, 4.5, 9, 5.5, _paper())
    c.fillrect(13, 5.3, 1.8, 3.6, _blue())
    c.rect(6.5, 13, 11, 7, color=_paper(), fill=_paper(), r=0.6, lw=0.8)
    return c.done()


def export_pdf() -> QIcon:
    c = _W(); c.page(4, 2.5, 14, 19)
    c.rect(9, 11, 13, 8, color=QColor("#c43e1c"), fill=QColor("#c43e1c"),
           r=1.2, lw=1)
    c.text((9, 11, 13, 8), "PDF", size=6.5, bold=True, color=QColor("white"))
    return c.done()


def _printer(c: _W) -> None:
    c.rect(6.5, 3, 11, 6, fill=_paper())
    c.rect(2.5, 8.5, 19, 9, fill=_tint())
    c.rect(6.5, 14, 11, 7, fill=_paper())
    c.line(8.5, 17, 15.5, 17, w=1); c.line(8.5, 19, 13.5, 19, w=1)
    c.dot(18.3, 11.3, 0.9, _blue())


def printer() -> QIcon:
    c = _W(); _printer(c)
    return c.done()


def print_preview() -> QIcon:
    c = _W(); c.page(3, 2.5, 13, 18)
    c.pen(_blue(), 1.6).brush(_paper())
    c.p.drawEllipse(QPointF(15, 15), 4, 4)
    c.line(18, 18, 21.5, 21.5, _blue(), 2)
    return c.done()


def project_open() -> QIcon:
    c = _W()
    c.page(8, 2.5, 12, 15, 3)
    c.page(4, 6, 12, 15.5, 3)
    for y in (12, 14.5, 17):
        c.line(6.5, y, 13, y, _blue(), 1)
    return c.done()


def undo() -> QIcon:
    c = _W(); c.pen(_blue(), 1.8)
    path = QPainterPath(); path.moveTo(5, 9)
    path.lineTo(14, 9); path.cubicTo(21, 9, 21, 19.5, 14, 19.5)
    path.lineTo(9, 19.5)
    c.p.drawPath(path)
    c.poly([(9, 4.5), (4.5, 9), (9, 13.5)], color=_blue(), closed=False,
           lw=1.8)
    return c.done()


def redo() -> QIcon:
    c = _W(); c.pen(_blue(), 1.8)
    path = QPainterPath(); path.moveTo(19, 9)
    path.lineTo(10, 9); path.cubicTo(3, 9, 3, 19.5, 10, 19.5)
    path.lineTo(15, 19.5)
    c.p.drawPath(path)
    c.poly([(15, 4.5), (19.5, 9), (15, 13.5)], color=_blue(), closed=False,
           lw=1.8)
    return c.done()


# ----- font group: Office draws letters in a plain sans -----

def _letter(s: str, **kw) -> QIcon:
    c = _W(); c.text((0, 0, 24, 23), s, size=kw.pop("size", 17), **kw)
    return c.done()


def bold() -> QIcon:
    return _letter("B", bold=True)


def italic() -> QIcon:
    return _letter("I", italic=True, family="Georgia")


def underline() -> QIcon:
    c = _W(); c.text((0, 0, 24, 20), "U", size=15)
    c.line(6, 20.5, 18, 20.5, w=1.6)
    return c.done()


def strike() -> QIcon:
    c = _W(); c.text((0, 0, 24, 23), "ab", size=14)
    c.line(3.5, 12.5, 20.5, 12.5, _blue(), 1.6)
    return c.done()


def subscript() -> QIcon:
    c = _W(); c.text((1, 1, 16, 20), "X", size=15)
    c.text((13, 10, 10, 13), "2", size=9, bold=True, color=_blue())
    return c.done()


def superscript() -> QIcon:
    c = _W(); c.text((1, 4, 16, 20), "X", size=15)
    c.text((13, 0, 10, 12), "2", size=9, bold=True, color=_blue())
    return c.done()


def smallcaps() -> QIcon:
    c = _W(); c.text((0, 0, 14, 23), "A", size=16)
    c.text((11, 3, 13, 20), "A", size=11, color=_blue())
    return c.done()


def code() -> QIcon:
    c = _W()
    c.poly([(8.5, 6), (3.5, 12), (8.5, 18)], closed=False, lw=1.7)
    c.poly([(15.5, 6), (20.5, 12), (15.5, 18)], closed=False, lw=1.7)
    c.line(13.3, 5, 10.7, 19, _blue(), 1.5)
    return c.done()


def highlight() -> QIcon:
    c = _W()
    c.poly([(13.5, 3), (19, 8.5), (11, 16.5), (5.5, 11)], fill=_paper())
    c.poly([(5.5, 11), (11, 16.5), (8, 17.5), (4.5, 14)], fill=_tint())
    c.fillrect(2.5, 19.5, 19, 3, QColor("#ffeb3b"))
    return c.done()


# ----- paragraph group -----

def bullet_list() -> QIcon:
    c = _W()
    for y in (6, 12, 18):
        c.dot(5, y, 1.6, _blue()); c.line(9.5, y, 20.5, y)
    return c.done()


def numbered_list() -> QIcon:
    c = _W()
    for k, y in enumerate((6, 12, 18), 1):
        c.text((1, y - 5, 7, 10), str(k), size=7.5, bold=True, color=_blue())
        c.line(9.5, y, 20.5, y)
    return c.done()


def _align(widths) -> QIcon:
    c = _W()
    for k, (x1, x2) in enumerate(widths):
        c.line(x1, 5 + k * 4.6, x2, 5 + k * 4.6)
    return c.done()


def align_left() -> QIcon:
    return _align([(3.5, 20.5), (3.5, 14), (3.5, 20.5), (3.5, 12)])


def align_center() -> QIcon:
    return _align([(3.5, 20.5), (7, 17), (3.5, 20.5), (8, 16)])


def align_right() -> QIcon:
    return _align([(3.5, 20.5), (10, 20.5), (3.5, 20.5), (12, 20.5)])


def align_justify() -> QIcon:
    return _align([(3.5, 20.5)] * 4)


def formatting_marks() -> QIcon:
    return _letter("¶", size=17, color=_blue())


def spell_check() -> QIcon:
    c = _W(); c.text((0, 0, 24, 15), "ABC", size=8.5, bold=True)
    c.poly([(5, 16.5), (9.5, 20.5), (19, 11.5)], color=_blue(), closed=False,
           lw=2)
    return c.done()


# ----- review -----

def comment() -> QIcon:
    c = _W()
    c.poly([(3, 4), (21, 4), (21, 16), (11, 16), (6.5, 20.5), (6.5, 16),
            (3, 16)], fill=_paper())
    c.line(6.5, 8.5, 17.5, 8.5, _blue(), 1.2)
    c.line(6.5, 11.8, 14, 11.8, _blue(), 1.2)
    return c.done()


def accept_change() -> QIcon:
    c = _W()
    c.poly([(4.5, 12.5), (9.5, 17.5), (19.5, 6.5)], closed=False,
           color=QColor("#107c10"), lw=2.4)
    return c.done()


def reject_change() -> QIcon:
    c = _W()
    c.line(6, 6, 18, 18, QColor("#c42b1c"), 2.4)
    c.line(18, 6, 6, 18, QColor("#c42b1c"), 2.4)
    return c.done()


def prev_comment() -> QIcon:
    c = _W()
    c.poly([(5, 4), (19, 4), (19, 13), (5, 13)], fill=_paper(), lw=1.2)
    c.poly([(7, 21), (12, 16), (17, 21)], color=_blue(), closed=False, lw=1.8)
    return c.done()


def next_comment() -> QIcon:
    c = _W()
    c.poly([(5, 11), (19, 11), (19, 20), (5, 20)], fill=_paper(), lw=1.2)
    c.poly([(7, 3), (12, 8), (17, 3)], color=_blue(), closed=False, lw=1.8)
    return c.done()


def history() -> QIcon:
    c = _W(); c.pen(_ink(), 1.5).brush(_paper())
    c.p.drawEllipse(QPointF(12.5, 12.5), 8.5, 8.5)
    c.line(12.5, 7.5, 12.5, 12.5, _blue(), 1.7)
    c.line(12.5, 12.5, 16, 14.5, _blue(), 1.7)
    return c.done()


def commit() -> QIcon:
    """Snapshot uploaded: a cloud with an up arrow."""
    c = _W(); c.pen(_ink(), 1.5).brush(_paper())
    path = QPainterPath(); path.moveTo(6.5, 18.5)
    path.cubicTo(1.5, 18.5, 1.5, 11, 6.5, 11)
    path.cubicTo(7.5, 5, 16.5, 5, 17.5, 10)
    path.cubicTo(22.5, 10, 22.5, 18.5, 17.5, 18.5)
    path.closeSubpath()
    c.p.drawPath(path)
    c.line(12, 20.5, 12, 11.5, _blue(), 1.8)
    c.poly([(9, 14.5), (12, 11.5), (15, 14.5)], color=_blue(), closed=False,
           lw=1.8)
    return c.done()


def branch() -> QIcon:
    c = _W()
    c.line(7, 5, 7, 19, w=1.5)
    c.pen(_ink(), 1.5)
    path = QPainterPath(); path.moveTo(17, 8); path.cubicTo(17, 14, 7, 12, 7, 17)
    c.p.drawPath(path)
    for x, y in ((7, 5), (7, 19), (17, 7)):
        c.pen(_blue(), 1.5).brush(_paper())
        c.p.drawEllipse(QPointF(x, y), 2.2, 2.2)
    return c.done()


# ----- compile -----

def compile_pdf() -> QIcon:
    c = _W(); c.page(3, 2.5, 13, 18)
    c.poly([(13, 11), (21.5, 16), (13, 21)], color=QColor("#107c10"),
           fill=QColor("#107c10"), lw=1)
    return c.done()


def auto_compile_on() -> QIcon:
    c = _W(); c.pen(QColor("#107c10"), 1.8)
    c.p.drawArc(QRectF(4, 4, 16, 16), 60 * 16, 290 * 16)
    c.poly([(16, 2.5), (19.5, 6), (15, 8)], color=QColor("#107c10"),
           fill=QColor("#107c10"), lw=1)
    c.dot(12, 12, 2, QColor("#107c10"))
    return c.done()


def auto_compile_off() -> QIcon:
    c = _W(); c.pen(_ink(), 1.8)
    c.p.drawArc(QRectF(4, 4, 16, 16), 60 * 16, 290 * 16)
    c.line(4, 20, 20, 4, QColor("#c42b1c"), 1.8)
    return c.done()


def compile_no_images() -> QIcon:
    c = _W(); _picture(c)
    c.line(3, 21, 21, 3, QColor("#c42b1c"), 1.8)
    return c.done()


def compile_range() -> QIcon:
    c = _W(); c.page(5, 2.5, 14, 19)
    c.fillrect(6, 8, 12, 7, _tint())
    c.line(3, 8, 21, 8, _blue(), 1.4); c.line(3, 15, 21, 15, _blue(), 1.4)
    return c.done()


# ----- insert -----

def _picture(c: _W) -> None:
    c.rect(3, 4.5, 18, 15, fill=_paper())
    c.poly([(4.5, 18), (10, 11), (14, 15.5), (16.5, 13), (19.5, 18)],
           color=_blue(), fill=_tint(), lw=1.2)
    c.dot(16, 8.5, 1.8, QColor("#f2b01e"))


def figure() -> QIcon:
    c = _W(); _picture(c)
    return c.done()


def table() -> QIcon:
    c = _W()
    c.rect(3, 4, 18, 16, fill=_paper(), r=1)
    c.fillrect(3.8, 4.8, 16.4, 4, _tint())
    c.line(3, 9, 21, 9, w=1); c.line(3, 14.5, 21, 14.5, w=1)
    c.line(9, 4, 9, 20, w=1); c.line(15, 4, 15, 20, w=1)
    return c.done()


def drawing() -> QIcon:
    c = _W()
    c.pen(_blue(), 1.5).brush(_tint())
    c.p.drawEllipse(QRectF(3, 3, 9, 9))
    c.rect(11, 11, 10, 9, color=_ink(), fill=_paper(), r=0.8)
    c.poly([(5, 21), (9, 14), (13, 21)], color=_ink(), fill=_paper())
    return c.done()


def flowchart_builder() -> QIcon:
    c = _W()
    c.rect(7, 2.5, 10, 5, fill=_tint(), color=_blue(), r=1)
    c.line(12, 7.5, 12, 10.5, w=1.2)
    c.poly([(12, 10.5), (16.5, 13.5), (12, 16.5), (7.5, 13.5)], fill=_paper())
    c.line(12, 16.5, 12, 18.5, w=1.2)
    c.rect(7, 18.5, 10, 3.5, fill=_tint(), color=_blue(), r=1)
    return c.done()


def link() -> QIcon:
    c = _W(); c.pen(_blue(), 1.8).brush(Qt.NoBrush)
    c.p.drawRoundedRect(QRectF(2.5, 8.5, 11, 7), 3.5, 3.5)
    c.pen(_ink(), 1.8)
    c.p.drawRoundedRect(QRectF(10.5, 8.5, 11, 7), 3.5, 3.5)
    return c.done()


def footnote() -> QIcon:
    c = _W(); c.text((0, 0, 17, 15), "ab", size=11)
    c.text((14, 0, 9, 9), "1", size=7.5, bold=True, color=_blue())
    c.line(3, 17, 11, 17, w=1)
    c.line(3, 20.5, 20, 20.5, _blue(), 1.2)
    return c.done()


def citation() -> QIcon:
    c = _W()
    c.rect(4, 3, 15, 18, fill=_tint(), color=_blue(), r=1)
    c.line(7, 3, 7, 21, _blue(), 1.2)
    c.text((7, 4, 12, 15), "“”", size=13, bold=True, color=_blue(),
           family="Georgia")
    return c.done()


def cross_ref() -> QIcon:
    c = _W()
    c.poly([(6, 3), (18, 3), (18, 21), (12, 16.5), (6, 21)], fill=_tint(),
           color=_blue())
    c.line(9, 8, 15, 8, w=1)
    return c.done()


def math_inline() -> QIcon:
    c = _W(); c.text((0, 0, 24, 22), "π", size=17, color=_blue(),
                     family="Georgia")
    return c.done()


def math_block() -> QIcon:
    c = _W()
    c.rect(2.5, 4.5, 19, 15, fill=_paper())
    c.text((2.5, 4.5, 19, 14), "π", size=13, color=_blue(),
           family="Georgia")
    return c.done()


def symbol() -> QIcon:
    return _letter("Ω", size=17, family="Georgia")


def equation_builder() -> QIcon:
    c = _W()
    c.text((1, 0, 22, 13), "x", size=10, italic=True, family="Georgia",
           color=_blue())
    c.line(5, 12, 19, 12, w=1.3)
    c.text((1, 12, 22, 12), "y", size=10, italic=True, family="Georgia",
           color=_blue())
    c.rect(2, 2, 20, 20, color=_ink(), r=2, lw=1)
    return c.done()


def chemistry() -> QIcon:
    c = _W()
    c.poly([(9, 3), (15, 3)], closed=False, lw=1.5)
    c.poly([(10, 3), (10, 9), (4.5, 19.5), (5.5, 21), (18.5, 21),
            (19.5, 19.5), (14, 9), (14, 3)], fill=_paper(), closed=False)
    c.poly([(7, 15), (17, 15), (19, 19.5), (5, 19.5)], color=_blue(),
           fill=_tint(), lw=0.8)
    return c.done()


def chemfig_structure() -> QIcon:
    import math
    c = _W()
    pts = [(12 + 8 * math.cos(math.radians(90 + 60 * k)),
            12 + 8 * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
    c.poly(pts, fill=_paper())
    inner = [(12 + 5 * math.cos(math.radians(90 + 60 * k)),
              12 + 5 * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
    for k in (0, 2, 4):
        c.line(*inner[k], *inner[k + 1], _blue(), 1.3)
    return c.done()


def _columns(n: int) -> QIcon:
    c = _W(); c.rect(3, 3, 18, 18, fill=_paper(), r=1, lw=1.2)
    gap = 1.8
    w = (14 - gap * (n - 1)) / n
    for k in range(n):
        x = 5 + k * (w + gap)
        for y in (6.5, 9.5, 12.5, 15.5, 18.5):
            c.line(x, y, x + w, y, _blue(), 1)
    return c.done()


def one_column() -> QIcon:
    return _columns(1)


def two_columns() -> QIcon:
    return _columns(2)


def three_columns() -> QIcon:
    return _columns(3)


def page_break() -> QIcon:
    c = _W()
    c.poly([(5, 2.5), (19, 2.5), (19, 9), (5, 9)], fill=_paper(), closed=False)
    c.poly([(5, 21.5), (5, 15), (19, 15), (19, 21.5)], fill=_paper(),
           closed=False)
    c.pen(_blue(), 1.3)
    c.p.setPen(QPen(_blue(), 1.3, Qt.DashLine))
    c.p.drawLine(QPointF(2, 12), QPointF(22, 12))
    return c.done()


def horizontal_rule() -> QIcon:
    c = _W()
    c.line(4, 6, 20, 6, w=1); c.line(4, 18, 20, 18, w=1)
    c.line(2.5, 12, 21.5, 12, _blue(), 2)
    return c.done()


# ----- view -----

def zoom_in() -> QIcon:
    c = _W(); c.pen(_ink(), 1.6).brush(_paper())
    c.p.drawEllipse(QPointF(10, 10), 6.5, 6.5)
    c.line(15, 15, 21, 21, w=2)
    c.line(7, 10, 13, 10, _blue(), 1.6); c.line(10, 7, 10, 13, _blue(), 1.6)
    return c.done()


def zoom_out() -> QIcon:
    c = _W(); c.pen(_ink(), 1.6).brush(_paper())
    c.p.drawEllipse(QPointF(10, 10), 6.5, 6.5)
    c.line(15, 15, 21, 21, w=2)
    c.line(7, 10, 13, 10, _blue(), 1.6)
    return c.done()


def fit_width() -> QIcon:
    c = _W(); c.rect(6, 3, 12, 18, fill=_paper(), r=1, lw=1.2)
    c.line(2, 12, 22, 12, _blue(), 1.5)
    c.poly([(5, 9.5), (2, 12), (5, 14.5)], color=_blue(), closed=False)
    c.poly([(19, 9.5), (22, 12), (19, 14.5)], color=_blue(), closed=False)
    return c.done()


def heading(level: int) -> QIcon:
    c = _W()
    c.text((0, 0, 24, 23), f"H{level}", size={1: 14, 2: 13, 3: 12}.get(level, 11),
           bold=True, color=_blue())
    return c.done()


# ----- clipboard -----

def paste() -> QIcon:
    c = _W()
    c.rect(4, 4.5, 14, 17, fill=QColor("#c8a76a") if not _dark else QColor("#8a7040"), r=1.5)
    c.rect(8, 2.5, 6, 4, fill=_paper(), r=1)
    c.page(10, 9, 11, 13, 3)
    c.line(12, 15, 18, 15, _blue(), 1); c.line(12, 17.5, 16.5, 17.5, _blue(), 1)
    return c.done()


def cut() -> QIcon:
    c = _W()
    c.line(8, 3, 15.5, 15, w=1.6); c.line(16, 3, 8.5, 15, w=1.6)
    c.pen(_blue(), 1.6).brush(_paper())
    c.p.drawEllipse(QPointF(7, 18), 3, 3)
    c.p.drawEllipse(QPointF(17, 18), 3, 3)
    return c.done()


def copy() -> QIcon:
    c = _W()
    c.page(8, 2.5, 12, 15, 3)
    c.page(4, 6.5, 12, 15, 3)
    return c.done()


# ----- contextual tabs: table, picture, equation, page setup -----

def _grid(c: _W, x=3, y=7, w=14, h=14) -> None:
    c.rect(x, y, w, h, fill=_paper(), r=0.8, lw=1.2)
    c.line(x, y + h / 2, x + w, y + h / 2, w=0.9)
    c.line(x + w / 2, y, x + w / 2, y + h, w=0.9)


def _plus(c: _W, x, y) -> None:
    c.line(x - 3, y, x + 3, y, _blue(), 1.8); c.line(x, y - 3, x, y + 3, _blue(), 1.8)


def _cross(c: _W, x, y) -> None:
    red = QColor("#c42b1c")
    c.line(x - 2.8, y - 2.8, x + 2.8, y + 2.8, red, 1.8)
    c.line(x + 2.8, y - 2.8, x - 2.8, y + 2.8, red, 1.8)


def table_row_above() -> QIcon:
    c = _W(); _grid(c, 3, 9, 18, 12)
    c.fillrect(3.8, 9.8, 16.4, 5, _tint()); _plus(c, 12, 4.5)
    return c.done()


def table_row_below() -> QIcon:
    c = _W(); _grid(c, 3, 3, 18, 12)
    c.fillrect(3.8, 9.5, 16.4, 4.8, _tint()); _plus(c, 12, 19.5)
    return c.done()


def table_col_left() -> QIcon:
    c = _W(); _grid(c, 9, 3, 12, 18)
    c.fillrect(9.8, 3.8, 5, 16.4, _tint()); _plus(c, 4.5, 12)
    return c.done()


def table_col_right() -> QIcon:
    c = _W(); _grid(c, 3, 3, 12, 18)
    c.fillrect(9.5, 3.8, 4.8, 16.4, _tint()); _plus(c, 19.5, 12)
    return c.done()


def table_delete_row() -> QIcon:
    c = _W(); _grid(c, 3, 3, 14, 14)
    c.fillrect(3.8, 3.8, 12.4, 6.4, QColor("#f6d5d1")); _cross(c, 19, 19)
    return c.done()


def table_delete_col() -> QIcon:
    c = _W(); _grid(c, 3, 3, 14, 14)
    c.fillrect(3.8, 3.8, 6.4, 12.4, QColor("#f6d5d1")); _cross(c, 19, 19)
    return c.done()


def table_delete() -> QIcon:
    c = _W(); _grid(c, 3, 3, 14, 14); _cross(c, 19, 19)
    return c.done()


def table_style_plain() -> QIcon:
    c = _W(); c.rect(3, 4, 18, 16, fill=_paper(), r=0.5, lw=1.2)
    for y in (9, 14.5):
        c.line(3, y, 21, y, w=1)
    c.line(9, 4, 9, 20, w=1); c.line(15, 4, 15, 20, w=1)
    return c.done()


def table_style_booktabs() -> QIcon:
    c = _W()
    c.line(3, 4.5, 21, 4.5, w=2); c.line(3, 9, 21, 9, w=1)
    c.line(3, 19.5, 21, 19.5, w=2)
    for y in (12, 15.5):
        c.line(5, y, 10, y, _blue(), 1); c.line(14, y, 19, y, _blue(), 1)
    return c.done()


def picture_delete() -> QIcon:
    c = _W()
    c.rect(2.5, 3.5, 15, 12.5, fill=_paper())
    c.poly([(4, 14.5), (8.5, 9), (12, 12.5), (16, 14.5)], color=_blue(),
           fill=_tint(), lw=1)
    _cross(c, 19, 19)
    return c.done()


def picture_edit() -> QIcon:
    c = _W()
    c.rect(2.5, 3.5, 15, 12.5, fill=_paper())
    c.poly([(19.5, 9.5), (22, 12), (13, 21), (10, 21.5), (10.5, 18.5)],
           color=_blue(), fill=_tint(), lw=1.3)
    return c.done()


def picture_width(frac: float) -> QIcon:
    c = _W()
    c.rect(2, 5, 20, 14, color=QColor("#999"), r=0.5, lw=0.8)
    w = 18 * frac
    c.rect(12 - w / 2, 8, w, 8, color=_blue(), fill=_tint(), r=0.5, lw=1)
    return c.done()


def equation_numbered() -> QIcon:
    c = _W(); c.text((0, 0, 15, 24), "π", size=13, color=_blue(),
                     family="Georgia")
    c.text((12, 0, 12, 24), "(1)", size=7.5)
    return c.done()


def equation_delete() -> QIcon:
    c = _W(); c.text((0, 0, 17, 22), "π", size=15, color=_blue(),
                     family="Georgia")
    _cross(c, 19, 19)
    return c.done()


def page_size() -> QIcon:
    c = _W(); c.page(6, 2.5, 12, 18, 3.5)
    c.line(3.5, 3, 3.5, 20.5, _blue(), 1); c.line(8, 22.5, 16, 22.5, _blue(), 1)
    return c.done()


def page_margins() -> QIcon:
    c = _W(); c.rect(4, 2.5, 16, 19.5, fill=_paper(), r=0.5, lw=1.2)
    c.p.setPen(QPen(_blue(), 1, Qt.DashLine)); c.p.setBrush(Qt.NoBrush)
    c.p.drawRect(QRectF(7, 5.5, 10, 13.5))
    return c.done()


def paper_thumb(w_in: float, h_in: float) -> QIcon:
    """A sheet drawn to the paper's real proportions."""
    c = _W()
    s = 19 / max(w_in, h_in)
    w, h = w_in * s, h_in * s
    c.page(12 - w / 2, 12 - h / 2, w, h, 3)
    return c.done()
