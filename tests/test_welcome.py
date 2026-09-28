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


def test_page_only_also_hides_the_documents_list(window):
    window.show()
    window.apply_layout_mode("page")
    assert window._project_dock.isHidden()
    assert window._side_tabs.isHidden() and window._auto_compile is False
    window.apply_layout_mode("visual")
    assert not window._project_dock.isHidden()
    assert window._side_tabs.isHidden()


def test_welcome_offers_three_ways_to_work(qapp):
    from khervedoc.welcome import WelcomeDialog
    d = WelcomeDialog([], [])
    labels = [b.text() for b in d._group.buttons()]
    assert len(labels) == 4 and any("Page only" in t for t in labels)
    assert any("own window" in t for t in labels)


def test_pdf_can_live_in_its_own_window(window):
    window.show()
    window.apply_layout_mode("window")
    win = window._pdf_window
    assert win is not None and win.isVisible()
    assert window._side_tabs.window() is win        # panel moved over
    assert window._auto_compile is True
    win.close()                                      # its X docks it back
    assert window._pdf_window is None
    assert window._side_tabs.window() is window
    assert not window._side_tabs.isHidden()
    window.apply_layout_mode("window")
    window.apply_layout_mode("visual")               # other modes re-dock
    assert window._pdf_window is None and window._side_tabs.isHidden()


def _checked_layout(window):
    return [a.text() for a in (window.act_visual_only, window.act_side_by_side,
                               window.act_pdf_window) if a.isChecked()]


def test_view_menu_layouts_are_one_choice(window):
    window.show()
    for mode, want in (("side", "PDF &side panel"),
                       ("window", "PDF in its own &window"),
                       ("visual", "&Visual only (like Word)"),
                       ("page", "&Visual only (like Word)")):
        window.apply_layout_mode(mode)
        assert _checked_layout(window) == [want], mode
    window.apply_layout_mode("window")
    window._pdf_window.close()                 # docking back = side panel
    assert _checked_layout(window) == ["PDF &side panel"]


def test_ctrl4_toggles_between_side_panel_and_visual(window):
    window.apply_layout_mode("side")
    window.act_side_by_side.trigger()
    assert window._side_tabs.isHidden() and window._auto_compile is False
    window.act_side_by_side.trigger()
    assert not window._side_tabs.isHidden() and window._auto_compile is True


def test_examples_open_in_the_chosen_layout(window):
    from khervedoc import examples
    window.apply_layout_mode("window")
    made = []
    orig = window._new_window
    window._new_window = lambda: made.append(orig()) or made[-1]
    window._open_example(examples.EXAMPLES[0][1])
    new = made[0]
    try:
        assert new._pdf_window is not None
        assert new.act_pdf_window.isChecked()
    finally:
        new.close()
        window.apply_layout_mode("side")
