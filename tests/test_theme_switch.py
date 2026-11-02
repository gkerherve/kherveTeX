"""Only Light and Dark exist, and a switch at the bottom flips between them."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc import themes  # noqa: E402


def _window():
    QApplication.instance() or QApplication([])
    from khervedoc.mainwindow import MainWindow
    return MainWindow(theme_name="Light")


def test_only_light_and_dark():
    assert themes.THEME_NAMES == ["Light", "Dark"]
    assert themes.DEFAULT_THEME == "Light"


@pytest.mark.parametrize("name,dark,want", [
    ("Light", False, "Light"), ("Dark", True, "Dark"),
    ("Word Blue", False, "Light"), ("Nord", True, "Dark"),
    ("", False, "Light"),
])
def test_saved_presets_become_light_or_dark(name, dark, want):
    s = QSettings("kherveDOC", "kherve-theme-test")
    s.setValue("theme_name", name)
    s.setValue("theme_dark", dark)
    assert themes.saved_theme(s) == want


def test_switch_sits_in_the_status_bar_and_changes_the_theme():
    w = _window()
    w.show()
    sw = w._theme_switch
    assert sw.parent() is w._status or sw.window() is w
    assert sw.isVisible() and not sw.isChecked()
    sw.click()
    assert w._theme_name == "Dark" and w._is_dark
    assert w._theme_actions["Dark"].isChecked()
    assert "light" in sw.toolTip()
    sw.click()
    assert w._theme_name == "Light" and not w._is_dark
    w.grab()                    # paints in both states without raising


def test_menu_choice_moves_the_switch():
    w = _window()
    w._theme_actions["Dark"].trigger()
    assert w._theme_switch.isChecked()
    w._theme_actions["Light"].trigger()
    assert not w._theme_switch.isChecked()
