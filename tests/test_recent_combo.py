"""The status bar's recent-files combo lists the recent files by name and
opens the one picked."""
import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def _window(tmp_path):
    QApplication.instance() or QApplication([])
    from khervedoc.mainwindow import MainWindow
    w = MainWindow(theme_name="Light")
    # Keep the user's own recent list out of the test.
    w._settings = QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)
    w._recent = []
    w._refresh_recent_menu()
    return w


def test_combo_sits_left_of_the_path_and_starts_empty(tmp_path):
    w = _window(tmp_path)
    w.show()
    QApplication.processEvents()
    combo = w._recent_combo
    assert w._status.isAncestorOf(combo)
    assert combo.x() < w._path_label.x()
    assert not combo.isEnabled()
    assert combo.placeholderText() == "No recent files"


def test_combo_lists_recent_files_and_opens_the_pick(tmp_path):
    w = _window(tmp_path)
    a, b = tmp_path / "Paper draft.ktex", tmp_path / "Thesis.ktex"
    w._remember_recent(a)
    w._remember_recent(b)
    combo = w._recent_combo
    assert combo.isEnabled()
    assert [combo.itemText(i) for i in range(combo.count())] == [
        "Thesis.ktex", "Paper draft.ktex"]
    assert combo.itemData(1, Qt.ToolTipRole) == str(a)
    assert combo.currentIndex() == -1
    assert combo.placeholderText() == "Recent files"
    opened = []
    w.offer_save_before = lambda reason: True
    w._open_path = opened.append
    combo.activated.emit(1)
    assert opened == [a]
    assert combo.currentIndex() == -1
