"""The menu bar is Word's, the app opens on an empty page, and the
examples have a ribbon tab of their own."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QToolButton  # noqa: E402


@pytest.fixture
def window():
    QApplication.instance() or QApplication([])
    from khervedoc.mainwindow import MainWindow
    w = MainWindow()
    yield w
    w.close()


def _titles(menu):
    return [a.text().replace("&", "") for a in menu.actions() if a.text()]


def test_menu_bar_is_words(window):
    assert _titles(window.menuBar()) == [
        "File", "Edit", "View", "Insert", "Format", "Tools", "Window", "Help"]


def test_nothing_was_lost_in_the_move(window):
    def every(menu, out):
        for a in menu.actions():
            out.add(a)
            if a.menu():
                every(a.menu(), out)
        return out
    found = every(window.menuBar(), set())
    for act in (window.act_commit_now, window.act_history, window.act_pull,
                window.act_branches, window.act_configure_remotes,
                window.act_highlight, window.act_comment,
                window.act_chemfig, window.act_raw, window.act_compile_start,
                window.act_overleaf_send, window.act_overleaf_get,
                window.act_overleaf_zip, window.act_save_as_template,
                window.act_tour):
        assert act in found, act.text()


def test_app_opens_on_an_empty_page(window):
    doc = window._editor.get_document()
    assert sum(1 for b in doc.children
               if "".join(getattr(c, "text", "") for c in
                          getattr(b, "children", [])).strip()) == 0


def test_every_example_is_in_the_template_menu(window):
    from khervedoc import examples
    labels = set()
    for cat in window._new_from_template_menu.actions():
        if cat.menu():
            labels |= {a.text() for a in cat.menu().actions()}
    assert {label for _c, label, _f, _d in examples.GALLERY} <= labels


def test_examples_ribbon_tab_offers_every_category(window):
    from khervedoc import examples
    rb = window._ribbon
    names = [rb.tabText(i) for i in range(rb.count())]
    tab = rb.widget(names.index("Examples"))
    texts = {b.text().replace("\n", " ").replace("&&", "&").strip()
             for b in tab.findChildren(QToolButton)}
    for cat in examples.GALLERY_CATEGORIES[1:]:
        assert cat in texts
    assert window.act_tour in {b.defaultAction()
                               for b in tab.findChildren(QToolButton)}


def test_tour_opens_the_welcome_document(window):
    before = len(type(window)._windows)
    window.act_tour.trigger()
    new = type(window)._windows[-1]
    assert len(type(window)._windows) == before + 1
    assert len(new._editor.get_document().children) >= 15
    new.close()
