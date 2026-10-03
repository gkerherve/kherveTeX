"""Console tab placement, Print / Print Preview, the auto-updater and
dropping several files at once."""
import os
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QMimeData, QRectF, QUrl  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, monkeypatch):
    from khervedoc.mainwindow import MainWindow
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)
    w = MainWindow()
    yield w
    w.close()


def _pdf(path: Path, sizes) -> Path:
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    for w, h in sizes:
        page = doc.new_page(width=w, height=h)
        page.insert_text((72, 72), "Hello")
    doc.save(str(path))
    doc.close()
    return path


def _menu(window, title):
    from PySide6.QtWidgets import QMenu
    return next(m for m in window.menuBar().findChildren(QMenu)
                if m.title() == title)


# ------------------------------------------------------------- console
def test_console_is_a_main_tab_after_code(window):
    tabs = window._tabs
    names = [tabs.tabText(i) for i in range(tabs.count())]
    assert names[:3] == ["Visual", "Code", "Console"]
    assert tabs.widget(2) is window._console
    side = [window._side_tabs.tabText(i)
            for i in range(window._side_tabs.count())]
    assert side == ["PDF"]


def test_console_shortcut_and_error_colour(window):
    from khervedoc.compiler import CompileResult
    window.act_view_console.trigger()
    assert window._tabs.currentWidget() is window._console
    bad = CompileResult(ok=False, pdf_path=None, log="! Undefined control",
                        error="boom")
    window._update_console(bad)
    assert "boom" in window._console.toPlainText()
    colour = window._tabs.tabBar().tabTextColor(2)
    assert colour.name() == "#c0392b"


# ------------------------------------------------------------- printing
def test_page_range_and_order(qapp):
    from PySide6.QtPrintSupport import QPrinter
    from khervedoc.printing import page_numbers
    pr = QPrinter()
    pr.setOutputFormat(QPrinter.PdfFormat)
    assert page_numbers(4, pr) == [0, 1, 2, 3]
    pr.setPrintRange(QPrinter.PageRange)
    pr.setFromTo(2, 3)
    assert page_numbers(4, pr) == [1, 2]
    pr.setPageOrder(QPrinter.LastPageFirst)
    assert page_numbers(4, pr) == [2, 1]


def test_fit_and_rotate():
    from khervedoc.printing import fit_rect, should_rotate
    sheet = QRectF(0, 0, 210, 297)
    assert not should_rotate(595, 842, sheet)
    assert should_rotate(842, 595, sheet)          # landscape on portrait
    box = fit_rect(842, 595, sheet, rotate=True)
    assert box.height() / box.width() == pytest.approx(842 / 595)
    assert box.width() <= 210 and box.height() == pytest.approx(297)
    assert box.center().x() == pytest.approx(105)


def test_render_pdf_prints_every_page(qapp, tmp_path):
    fitz = pytest.importorskip("fitz")
    from PySide6.QtPrintSupport import QPrinter
    from khervedoc.printing import match_printer_to_pdf, render_pdf
    src = _pdf(tmp_path / "doc.pdf", [(595, 842), (595, 842), (842, 595)])
    printer = QPrinter(QPrinter.HighResolution)
    match_printer_to_pdf(printer, src)
    out = tmp_path / "printed.pdf"
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(out))
    assert render_pdf(printer, src) == 3
    with fitz.open(str(out)) as printed:
        assert len(printed) == 3
        # A4 in, A4 out
        assert printed[0].rect.width == pytest.approx(595, abs=2)


def test_printer_follows_landscape_document(qapp, tmp_path):
    from PySide6.QtGui import QPageLayout
    from PySide6.QtPrintSupport import QPrinter
    from khervedoc.printing import match_printer_to_pdf
    src = _pdf(tmp_path / "deck.pdf", [(364, 273)])          # beamer 4:3
    printer = QPrinter(QPrinter.HighResolution)
    match_printer_to_pdf(printer, src)
    assert printer.pageLayout().orientation() == QPageLayout.Landscape
    assert printer.docName() == "deck"


def test_print_actions_in_file_menu(window):
    from PySide6.QtGui import QKeySequence
    assert window.act_print.shortcut().matches(
        QKeySequence(QKeySequence.Print)) == QKeySequence.ExactMatch
    file_menu = _menu(window, "&File")
    assert window.act_print in file_menu.actions()
    assert window.act_print_preview in file_menu.actions()


def test_preview_dialog_paints_pages(qapp, tmp_path):
    from khervedoc.printing import PdfPrintPreview
    src = _pdf(tmp_path / "doc.pdf", [(595, 842)] * 2)
    dlg = PdfPrintPreview(src)
    painted = []
    dlg.paintRequested.connect(lambda p: painted.append(p))
    dlg.show()
    qapp.processEvents()
    assert painted and "doc" in dlg.windowTitle()
    dlg.close()


# ------------------------------------------------------------- updater
def test_version_compare_and_changelog():
    from khervedoc import updater
    assert updater.parse_version("v0.12.3+abc") == (0, 12, 3)
    assert updater.newer_release("v9.0", "0.213")
    assert not updater.newer_release("v0.2", "0.213")
    md = updater.changelog_markdown(["v0.214: print preview", "plain"])
    assert "**v0.214** — print preview" in md and "- plain" in md


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t",
                            GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                            GIT_COMMITTER_EMAIL="t@t"))


def test_updater_fast_forwards_a_clean_checkout(tmp_path):
    from khervedoc import updater
    origin, clone = tmp_path / "origin", tmp_path / "clone"
    origin.mkdir()
    _git(origin, "init", "-q", "-b", "main")
    (origin / "a.txt").write_text("1")
    _git(origin, "add", "a.txt")
    _git(origin, "commit", "-q", "-m", "first")
    _git(tmp_path, "clone", "-q", str(origin), str(clone))
    (origin / "a.txt").write_text("2")
    _git(origin, "commit", "-q", "-am", "v0.300: something new")

    st = updater.check(clone)
    assert st.behind == 1 and st.can_fast_forward
    assert st.subjects == ["v0.300: something new"]
    updater.fast_forward(clone, st)
    assert (clone / "a.txt").read_text() == "2"

    (origin / "a.txt").write_text("3")
    _git(origin, "commit", "-q", "-am", "third")
    (clone / "a.txt").write_text("local edit")
    st = updater.check(clone)
    assert st.available and not st.can_fast_forward
    assert "uncommitted" in st.why_not()
    with pytest.raises(updater.UpdateError):
        updater.fast_forward(clone, st)


def test_help_menu_offers_updates(window):
    from khervedoc.mainwindow import MainWindow
    help_menu = _menu(window, "&Help")
    texts = [a.text() for a in help_menu.actions()]
    assert "Check for &updates…" in texts
    assert "Update &automatically" in texts
    # One updater for the whole app, whichever window asks.
    assert MainWindow.updater() is MainWindow.updater()


def test_offer_save_before_passes_unmodified(window):
    window._editor.text_edit.document().setModified(False)
    assert window.offer_save_before("restarting")


# ------------------------------------------------------------- drops
def _mime(paths):
    m = QMimeData()
    m.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
    return m


def test_droppable_paths_keep_every_supported_file(window, tmp_path):
    files = [tmp_path / n for n in ("a.png", "b.docx", "c.xyz", "d.md")]
    got = window._droppable_paths(_mime(files))
    assert [p.name for p in got] == ["a.png", "b.docx", "d.md"]


def test_open_dropped_handles_each_file(window, tmp_path, monkeypatch):
    from khervedoc.mainwindow import MainWindow
    images, opened, extra = [], [], []
    monkeypatch.setattr(window._editor, "drop_image_file", images.append)
    monkeypatch.setattr(window, "offer_save_before", lambda reason: True)
    monkeypatch.setattr(window, "_open_path", opened.append)

    class _Win:
        def _open_path(self, path):
            extra.append(path)
    monkeypatch.setattr(window, "_new_window", lambda: _Win())
    files = [tmp_path / "a.png", tmp_path / "one.tex", tmp_path / "b.jpg",
             tmp_path / "two.md"]
    window.open_dropped(files)
    assert [p.name for p in images] == ["a.png", "b.jpg"]
    assert [p.name for p in opened] == ["one.tex"]
    assert [p.name for p in extra] == ["two.md"]
    assert isinstance(window, MainWindow)


def test_open_dropped_respects_cancel(window, tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(window, "offer_save_before", lambda reason: False)
    monkeypatch.setattr(window, "_open_path", opened.append)
    window.open_dropped([tmp_path / "one.tex"])
    assert opened == []
