"""Keep the test suite away from the user's real app settings, and keep one
test's windows from slowing down or crashing the rest of the run.

MainWindow persists preferences (layout mode, fit-to-width, side panel,
theme...) through QSettings("kherveDOC", "kherveDOC"). Without this,
running the tests on a developer's machine rewrote their actual
KherveTeX preferences. That constructor uses QSettings' default format,
so switching it to an INI file in a throwaway directory isolates every
test at once.
"""
import sys
import tempfile

import pytest

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QSettings, QThread
    from PySide6.QtWidgets import QApplication
except ImportError:          # pure-model tests still run without Qt
    QSettings = None

if QSettings is not None:
    _dir = tempfile.mkdtemp(prefix="khervedoc-test-settings-")
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, _dir)


def _delete_closed_main_windows() -> None:
    """close() only hides a MainWindow, and each one brings dozens of menus
    that QApplication counts as top-level widgets. apply_theme walks them all
    for every new window, so left alive they make the run crawl to a halt."""
    mainwindow = sys.modules.get("khervedoc.mainwindow")
    if mainwindow is None or QApplication.instance() is None:
        return
    for w in QApplication.topLevelWidgets():
        if isinstance(w, mainwindow.MainWindow) and w._closed:
            w.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


@pytest.fixture(autouse=True)
def _clean_up_after_each_test():
    yield
    if QSettings is not None:
        _delete_closed_main_windows()


@pytest.fixture(autouse=True, scope="module")
def _close_everything_after_each_module():
    """Close what a test file left open and wait for its threads: Qt aborts
    the process if a QThread is still running when it is destroyed."""
    yield
    if QSettings is None or QApplication.instance() is None:
        return
    for w in QApplication.topLevelWidgets():
        w.close()
    for w in QApplication.topLevelWidgets():
        for thread in w.findChildren(QThread):
            thread.wait()
    _delete_closed_main_windows()
