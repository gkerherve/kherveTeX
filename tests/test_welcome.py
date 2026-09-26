"""Start-up: splash picture, welcome page choices, and layout modes."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, monkeypatch):
    from PySide6.QtCore import QSettings
    from khervedoc.mainwindow import MainWindow
    settings = QSettings("kherveDOC", "kherveDOC")
    keys = ("layout_mode", "show_welcome", "side_by_side", "fit_page_width")
    saved = {k: settings.value(k) for k in keys}
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)
    w = MainWindow()
    yield w
    w.close()
    # The layout choice is persisted; don't leave the user's real app in
    # whatever mode the test ended on.
    for k, v in saved.items():
        if v is None:
            settings.remove(k)
        else:
            settings.setValue(k, v)


def test_splash_paints(qapp):
    from khervedoc.splash import splash_pixmap
    pm = splash_pixmap(1.0)
    assert not pm.isNull() and pm.width() == 640


def test_welcome_labels_have_no_menu_accelerators(qapp):
    from khervedoc import examples
    from khervedoc.welcome import WelcomeDialog
    d = WelcomeDialog([], list(examples.EXAMPLES))
    labels = [d._examples.item(i).text() for i in range(d._examples.count())]
    assert labels and not any("&" in t and "&&" not in t for t in labels
                              if t.count("&") == 1 and " & " not in t)
    assert "Blank document" in labels


def test_visual_only_hides_pdf_and_stops_compiling(window):
    window.apply_layout_mode("visual")
    assert window._side_tabs.isHidden()
    assert window._auto_compile is False
    assert window.act_visual_only.isChecked()
    window.apply_layout_mode("side")
    assert not window._side_tabs.isHidden()
    assert window._auto_compile is True


def test_welcome_example_choice_loads_it(window, monkeypatch):
    from khervedoc import welcome
    from PySide6.QtWidgets import QDialog

    def fake_exec(self):
        self.choice = ("example", 1)       # "Blank document"
        self.layout_mode = "visual"
        return QDialog.Accepted
    monkeypatch.setattr(welcome.WelcomeDialog, "exec", fake_exec)
    window.show_welcome()
    assert window._auto_compile is False
    assert "Welcome to KherveTeX" not in window._editor.text_edit.toPlainText()
