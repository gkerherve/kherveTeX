"""The Word ribbon replaces the toolbars, including the vertical Insert
bar, and can be swapped with the classic layout at run time."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QToolBar  # noqa: E402


def _window():
    QApplication.instance() or QApplication([])
    from khervedoc.mainwindow import MainWindow
    return MainWindow()


def _left_bars(w):
    return [b for b in w.findChildren(QToolBar)
            if w.toolBarArea(b) == Qt.LeftToolBarArea and b.isVisible()]


def test_word_ribbon_has_tabs_and_no_vertical_bar():
    w = _window()
    w._apply_toolbar_style("word")
    w.show()
    tabs = [w._ribbon.tabText(i) for i in range(w._ribbon.count())]
    assert tabs[:3] == ["Home", "Insert", "Layout"]
    assert "Review" in tabs
    assert not _left_bars(w)
    assert w.act_style_word.isChecked()


def test_swapping_styles_keeps_shared_widgets_alive():
    w = _window()
    w.show()
    w._apply_toolbar_style("classic")
    QApplication.processEvents()
    assert _left_bars(w)
    w._apply_toolbar_style("word")
    QApplication.processEvents()
    assert w._fontsize_combo.isVisible()
    assert w._style_gallery.isVisible()
    assert not _left_bars(w)
