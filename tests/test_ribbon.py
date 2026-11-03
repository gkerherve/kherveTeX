"""The Word ribbon is the window's one and only toolbar."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QToolBar  # noqa: E402


def _window():
    QApplication.instance() or QApplication([])
    from khervedoc.mainwindow import MainWindow
    return MainWindow()


def _bars(w):
    return [b for b in w.findChildren(QToolBar) if b.isVisible()]


def test_ribbon_is_the_only_toolbar():
    w = _window()
    w.show()
    tabs = [w._ribbon.tabText(i) for i in range(w._ribbon.count())]
    assert tabs[:3] == ["Home", "Insert", "Layout"]
    assert "Review" in tabs
    bars = _bars(w)
    assert len(bars) == 1
    assert w.toolBarArea(bars[0]) == Qt.TopToolBarArea
    assert w._fontsize_combo.isVisible()
    assert w._style_gallery.isVisible()


def test_saved_classic_preference_no_longer_brings_toolbars_back():
    QSettings("kherveDOC", "kherveDOC").setValue("toolbar_style", "classic")
    w = _window()
    w.show()
    assert len(_bars(w)) == 1


def test_view_tab_replaces_page_tabs_and_pdf_tab():
    w = _window()
    w.show()
    tabs = [w._ribbon.tabText(i) for i in range(w._ribbon.count())]
    assert "View" in tabs
    assert not w._tabs.tabBar().isVisible()
    assert not w._side_tabs.tabBar().isVisible()
    w.act_page_code.trigger()
    assert w._tabs.currentWidget() is w._latex_view
    w._tabs.setCurrentIndex(0)
    assert w.act_page_visual.isChecked()


def test_compile_tab_holds_what_left_the_corner():
    w = _window()
    w.show()
    names = [w._ribbon.tabText(i) for i in range(w._ribbon.count())]
    tab = w._ribbon.widget(names.index("Compile"))
    from PySide6.QtWidgets import QToolButton
    shown = {b.defaultAction() for b in tab.findChildren(QToolButton)}
    assert {w.act_compile_range, w.act_skip_images,
            w.act_export_pdf} <= shown


def test_big_button_keeps_its_two_line_label_after_a_toggle():
    from PySide6.QtWidgets import QToolButton
    w = _window()
    names = [w._ribbon.tabText(i) for i in range(w._ribbon.count())]
    tab = w._ribbon.widget(names.index("Compile"))
    btn = next(b for b in tab.findChildren(QToolButton)
               if b.defaultAction() is w.act_compile_range)
    assert btn.text() == "Compile\nrange"
    w.act_compile_range.setChecked(not w.act_compile_range.isChecked())
    assert btn.text() == "Compile\nrange"


def test_theme_switch_redraws_ribbon_icons():
    w = _window()
    before = w.act_cut.icon().cacheKey(), w._style_buttons[0].icon().cacheKey()
    w._refresh_icons()
    assert w.act_cut.icon().cacheKey() != before[0]
    assert w._style_buttons[0].icon().cacheKey() != before[1]


def test_tab_hover_is_word_blue_not_a_system_colour():
    from khervedoc.ribbon import HOVER_BLUE, Ribbon
    QApplication.instance() or QApplication([])
    qss = Ribbon().styleSheet()
    hover = qss.split("QTabBar::tab:hover")[1].split("}")[0]
    assert HOVER_BLUE in hover and "midlight" not in hover


@pytest.mark.parametrize("name", ["Light", "Dark"])
def test_theme_sets_every_shade_so_windows_cannot_darken_them(name):
    from PySide6.QtGui import QPalette
    from khervedoc import themes
    app = QApplication.instance() or QApplication([])
    t = themes.apply_theme(app, name)
    pal = app.palette()
    assert pal.color(QPalette.Midlight).name() == t["midlight"]
    text = pal.color(QPalette.WindowText).lightness()
    assert abs(pal.color(QPalette.Midlight).lightness() - text) > 100


def test_overleaf_is_on_the_review_tab_not_only_in_a_menu():
    from PySide6.QtWidgets import QToolButton
    w = _window()
    rb = w._ribbon
    review = rb.widget([rb.tabText(i) for i in range(rb.count())]
                       .index("Review"))
    shown = {b.defaultAction() for b in review.findChildren(QToolButton)}
    for act in (w.act_overleaf_send, w.act_overleaf_get, w.act_overleaf_zip):
        assert act in shown and not act.icon().isNull()
