"""Startup splash screen, painted with QPainter at runtime (no image file,
crisp at any DPI, carries the live version) — the same approach as
KherveSheet's splash, in kherveDOC's blue."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
)
from PySide6.QtWidgets import QApplication, QSplashScreen

WIDTH, HEIGHT = 640, 380
_TOP = QColor("#1f63c6")
_BOTTOM = QColor("#0c2f66")
_INK = QColor("#ffffff")

#: The steps main() reports, in order; the bar advances through them.
STEPS = ("Loading the editor", "Building the window",
         "Opening the document", "Ready")


def _pages(p: QPainter, rect: QRectF) -> None:
    """Two stacked sheets of paper: text lines, a heading and a formula
    — the document the app produces."""
    for k, (dx, dy, alpha) in enumerate(((26, -18, 70), (0, 0, 235))):
        sheet = QRectF(rect.left() + dx, rect.top() + dy,
                       rect.width(), rect.height())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawRoundedRect(sheet.translated(3, 4), 4, 4)
        p.setBrush(QColor(255, 255, 255, alpha))
        p.drawRoundedRect(sheet, 4, 4)
        if k == 0:
            continue
        x0, x1 = sheet.left() + 22, sheet.right() - 22
        y = sheet.top() + 26
        p.setBrush(QColor("#1f63c6"))
        p.drawRoundedRect(QRectF(x0, y, 90, 7), 3, 3)          # heading
        y += 22
        p.setBrush(QColor(40, 60, 90, 90))
        for i in range(4):                                     # body text
            w = (x1 - x0) * (0.62 if i == 3 else 1.0)
            p.drawRoundedRect(QRectF(x0, y, w, 4), 2, 2)
            y += 11
        f = QFont("Times New Roman")
        f.setItalic(True)
        f.setPointSizeF(13)
        p.setFont(f)
        p.setPen(QColor("#0c2f66"))
        p.drawText(QRectF(x0, y + 4, x1 - x0, 30), Qt.AlignCenter,
                   "E = ℏω = ∫ ψ* Ĥ ψ dτ")
        y += 42
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(40, 60, 90, 90))
        for i in range(3):
            w = (x1 - x0) * (0.4 if i == 2 else 1.0)
            p.drawRoundedRect(QRectF(x0, y, w, 4), 2, 2)
            y += 11


def splash_pixmap(dpr: float = 1.0) -> QPixmap:
    from . import __version__, icons
    pm = QPixmap(int(WIDTH * dpr), int(HEIGHT * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    frame = QRectF(0, 0, WIDTH, HEIGHT)
    bg = QLinearGradient(frame.topLeft(), frame.bottomRight())
    bg.setColorAt(0.0, _TOP)
    bg.setColorAt(1.0, _BOTTOM)
    clip = QPainterPath()
    clip.addRoundedRect(frame, 14, 14)
    p.setClipPath(clip)
    p.fillRect(frame, bg)
    p.setPen(QPen(QColor(255, 255, 255, 18), 1))
    for i in range(0, WIDTH, 32):
        p.drawLine(QPointF(i, 0), QPointF(i - 120, HEIGHT))
    _pages(p, QRectF(372, 70, 210, 250))

    mark = icons.app_icon().pixmap(int(96 * dpr), int(96 * dpr))
    mark.setDevicePixelRatio(dpr)
    p.drawPixmap(QPointF(40, 52), mark)
    p.setPen(_INK)
    title = QFont()
    title.setPointSizeF(34)
    title.setBold(True)
    p.setFont(title)
    p.drawText(QRectF(40, 170, 330, 54), Qt.AlignLeft | Qt.AlignVCenter,
               "KherveTeX")
    sub = QFont()
    sub.setPointSizeF(12.5)
    p.setFont(sub)
    p.setPen(QColor(255, 255, 255, 215))
    p.drawText(QRectF(42, 222, 330, 44), Qt.AlignLeft | Qt.TextWordWrap,
               "Write like in Word, publish in LaTeX")
    small = QFont()
    small.setPointSizeF(9.5)
    p.setFont(small)
    p.setPen(QColor(255, 255, 255, 150))
    p.drawText(QRectF(42, HEIGHT - 34, 300, 20),
               Qt.AlignLeft | Qt.AlignVCenter, f"Version {__version__}")
    p.drawText(QRectF(WIDTH - 322, HEIGHT - 34, 300, 20),
               Qt.AlignRight | Qt.AlignVCenter,
               "© 2026 Gwilherm Kerherve · GPL-3.0")
    p.end()
    return pm


class Splash(QSplashScreen):
    """The start-up picture plus a status line and a progress bar."""

    def __init__(self):
        screen = QApplication.primaryScreen()
        ratio = screen.devicePixelRatio() if screen is not None else 1.0
        super().__init__(splash_pixmap(max(1.0, ratio)),
                         Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.step_text = STEPS[0]
        self.fraction = 0.0

    def step(self, text: str) -> None:
        self.step_text = text
        if text in STEPS:
            self.fraction = STEPS.index(text) / (len(STEPS) - 1)
        self.repaint()
        QApplication.processEvents()

    def drawContents(self, p: QPainter) -> None:
        p.setRenderHint(QPainter.Antialiasing)
        bar = QRectF(42, HEIGHT - 62, 290, 5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 35))
        p.drawRoundedRect(bar, 2.5, 2.5)
        if self.fraction > 0:
            p.setBrush(QColor("#9cc4ff"))
            p.drawRoundedRect(QRectF(bar.x(), bar.y(),
                                     bar.width() * self.fraction,
                                     bar.height()), 2.5, 2.5)
        p.setPen(QColor(255, 255, 255, 200))
        small = QFont()
        small.setPointSizeF(10.5)
        p.setFont(small)
        dots = "" if self.step_text == STEPS[-1] else "…"
        p.drawText(QRectF(42, HEIGHT - 86, 330, 20),
                   Qt.AlignLeft | Qt.AlignVCenter, self.step_text + dots)
