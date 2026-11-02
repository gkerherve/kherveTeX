"""The Light / Dark switch in the status bar: a sliding pill whose knob
shows a sun or a moon, drawn at runtime like the rest of the icons."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import QAbstractButton


class ThemeSwitch(QAbstractButton):
    """Checked means dark."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName("Dark theme")
        self.toggled.connect(self._describe)
        self._describe(False)

    def _describe(self, dark: bool) -> None:
        self.setToolTip("Switch to the light theme" if dark
                        else "Switch to the dark theme")

    def sizeHint(self) -> QSize:
        return QSize(40, 20)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = 18.0
        pill = QRectF(1, (self.height() - h) / 2, 38, h)
        dark = self.isChecked()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2b579a") if dark else QColor("#c8cdd3"))
        p.drawRoundedRect(pill, h / 2, h / 2)
        if self.hasFocus():
            p.setPen(QPen(self.palette().color(QPalette.Highlight), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(pill.adjusted(-0.5, -0.5, 0.5, 0.5), h / 2, h / 2)
        r = h / 2 - 2
        centre = QPointF(pill.right() - h / 2 if dark else pill.left() + h / 2,
                         pill.center().y())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(centre, r, r)
        if dark:
            # A crescent: the knob's colour with a bite taken out of it.
            moon = QPainterPath()
            moon.addEllipse(centre, r * 0.72, r * 0.72)
            bite = QPainterPath()
            bite.addEllipse(centre + QPointF(r * 0.38, -r * 0.3), r * 0.62,
                            r * 0.62)
            p.setBrush(QColor("#2b579a"))
            p.drawPath(moon.subtracted(bite))
        else:
            sun = QColor("#d98a00")
            p.setBrush(sun)
            p.drawEllipse(centre, r * 0.42, r * 0.42)
            p.setPen(QPen(sun, 1.1, Qt.SolidLine, Qt.RoundCap))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7),
                           (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
                p.drawLine(centre + QPointF(dx * r * 0.62, dy * r * 0.62),
                           centre + QPointF(dx * r * 0.88, dy * r * 0.88))
        p.end()
