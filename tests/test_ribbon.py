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


def test_view_tab_replaces_page_tabs_and_pdf_tab():
    w = _window()
    w.show()
    w._apply_toolbar_style("word")
    tabs = [w._ribbon.tabText(i) for i in range(w._ribbon.count())]
    assert "View" in tabs
    assert not w._tabs.tabBar().isVisible()
    assert not w._side_tabs.tabBar().isVisible()
    w.act_page_code.trigger()
    assert w._tabs.currentWidget() is w._latex_view
    w._tabs.setCurrentIndex(0)
    assert w.act_page_visual.isChecked()
    w._apply_toolbar_style("classic")
    QApplication.processEvents()
    assert w._tabs.tabBar().isVisible()
