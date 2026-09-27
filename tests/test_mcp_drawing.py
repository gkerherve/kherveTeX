"""MCP tools for equations, chemistry and drawings, and the KhervePaint
hand-off (locating the app, and regenerating a drawing when it saves)."""
import os
import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc import khervepaint_link as kpl  # noqa: E402
from khervedoc.mcp_bridge import tool_allowed  # noqa: E402
from khervedoc.mcp_tools import ToolExecutor  # noqa: E402
from khervedoc.model import Figure, MathBlock, MathInline, Paragraph  # noqa: E402

FLOW = [
    {"type": "rect", "x": 0, "y": 0, "w": 40, "h": 14, "label": "Start",
     "fill": "#eef2f6"},
    {"type": "rounded_rect", "x": 0, "y": 30, "w": 40, "h": 14,
     "label": "Measure"},
    {"type": "arrow", "points": [[20, 14], [20, 30]]},
    {"type": "text", "x": 60, "y": 7, "text": "note"},
    {"type": "symbol", "symbol": "electrical/resistor", "x": 70, "y": 37},
]


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, monkeypatch, tmp_path):
    from khervedoc.mainwindow import MainWindow
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)
    w = MainWindow()
    w._auto_compile = False
    w._editor._images_dir = tmp_path / "imgs"
    yield w
    w.close()


def _load(window, body: str):
    from khervedoc.importers import import_tex
    window._editor.set_document(import_tex(
        "\\documentclass{article}\\begin{document}\n" + body
        + "\n\\end{document}"))


def _blocks(window):
    return list(window._editor.get_document().children)


# ── equations & chemistry ──────────────────────────────────────────

def test_insert_display_and_inline_equation(window):
    _load(window, "Intro.")
    ex = ToolExecutor(window)
    r = ex.execute("insert_equation", {"latex": "$E = mc^2$",
                                       "label": "eq:e"})
    assert r["typesets_natively"] and r["numbered"]
    blk = _blocks(window)[r["at_index"]]
    assert isinstance(blk, MathBlock) and blk.latex == "E = mc^2"
    assert blk.label == "eq:e"
    r = ex.execute("insert_equation", {"latex": "\\alpha + 1",
                                       "display": False, "after": -1})
    first = _blocks(window)[0]
    assert isinstance(first, Paragraph)
    assert isinstance(first.children[0], MathInline)
    latex = ex.execute("get_latex", {})["latex"]
    assert "E = mc^2" in latex and "\\label{eq:e}" in latex


def test_equation_reports_untypeset_parts(window):
    _load(window, "x")
    r = ToolExecutor(window).execute(
        "insert_equation", {"latex": "\\frobnicate{x} + y"})
    assert r["typesets_natively"] is False
    assert r["not_typeset_in_editor"]


def test_insert_chemistry_adds_mhchem(window):
    _load(window, "x")
    ex = ToolExecutor(window)
    r = ex.execute("insert_chemistry", {"formula": "2H2 + O2 -> 2H2O"})
    assert r["mhchem_package_added"] and r["latex"] == "\\ce{2H2 + O2 -> 2H2O}"
    assert "mhchem" in window._editor.meta().packages
    latex = ex.execute("get_latex", {})["latex"]
    assert "\\usepackage{mhchem}" in latex
    assert "\\ce{2H2 + O2 -> 2H2O}" in latex
    r2 = ex.execute("insert_chemistry", {"formula": "SO4^2-",
                                         "display": True})
    assert r2["mhchem_package_added"] is False
    assert isinstance(_blocks(window)[r2["at_index"]], MathBlock)


# ── drawings ───────────────────────────────────────────────────────

def test_list_drawing_symbols(window):
    libs = ToolExecutor(window).execute("list_drawing_symbols",
                                        {})["libraries"]
    assert {"flowchart", "electrical", "optics"} <= set(libs)
    names = [s["name"] for cat in libs["optics"]["categories"].values()
             for s in cat]
    assert "laser" in names


def test_insert_drawing_writes_files_and_figure(window):
    _load(window, "Text.")
    ex = ToolExecutor(window)
    r = ex.execute("insert_drawing", {"shapes": FLOW, "caption": "Flow",
                                      "label": "fig:flow"})
    assert "error" not in r, r
    png = Path(r["files"]["png"])
    assert png.name == "drawing_001.png"
    for ext in (".png", ".svg", ".pdf"):
        assert png.with_suffix(ext).stat().st_size > 0
    fig = _blocks(window)[r["at_index"]]
    assert isinstance(fig, Figure) and fig.source == "drawing"
    assert fig.width == "0.7\\textwidth" and fig.label == "fig:flow"
    r2 = ex.execute("insert_drawing", {"shapes": FLOW[:1]})
    assert Path(r2["files"]["png"]).name == "drawing_002.png"


def test_get_drawing_round_trips(window):
    _load(window, "Text.")
    ex = ToolExecutor(window)
    at = ex.execute("insert_drawing", {"shapes": FLOW})["at_index"]
    got = ex.execute("get_drawing", {"index": at})
    types = [s["type"] for s in got["shapes"]]
    assert types == ["rect", "rounded_rect", "arrow", "text", "symbol"]
    rect = got["shapes"][0]
    assert (rect["x"], rect["y"], rect["w"], rect["h"]) == (0, 0, 40, 14)
    assert rect["label"] == "Start" and rect["fill"] == "#eef2f6"
    assert got["shapes"][4]["symbol"] == "electrical/resistor"
    assert ex.execute("get_drawing", {"index": 0})["error"]


def test_update_drawing_replace_and_append(window, monkeypatch):
    _load(window, "Text.")
    ex = ToolExecutor(window)
    at = ex.execute("insert_drawing", {"shapes": FLOW})["at_index"]
    refreshed = []
    monkeypatch.setattr(window._editor, "refresh_figure_image",
                        lambda p: refreshed.append(Path(p)) or 1)
    r = ex.execute("update_drawing", {"index": at, "shapes": FLOW[:2]})
    assert r["items_total"] == 2 and refreshed
    r = ex.execute("update_drawing", {"index": at, "mode": "append",
                                      "shapes": [{"type": "circle", "x": 80,
                                                  "y": 20, "r": 5}]})
    assert r["items_total"] == 3
    shapes = ex.execute("get_drawing", {"index": at})["shapes"]
    assert shapes[-1]["type"] == "circle" and shapes[-1]["r"] == 5


def test_bad_shape_is_reported(window):
    _load(window, "Text.")
    r = ToolExecutor(window).execute(
        "insert_drawing", {"shapes": [{"type": "rect", "x": 0}]})
    assert "shapes[0]" in r["error"]
    r = ToolExecutor(window).execute(
        "insert_drawing", {"shapes": [{"type": "symbol",
                                       "symbol": "optics/nope", "x": 0,
                                       "y": 0}]})
    assert "list_drawing_symbols" in r["error"]


def test_open_in_khervepaint_tool(window, monkeypatch):
    _load(window, "Text.")
    ex = ToolExecutor(window)
    at = ex.execute("insert_drawing", {"shapes": FLOW})["at_index"]
    launched = []
    link = window._editor.khervepaint_link()
    monkeypatch.setattr(link, "_launch", lambda cmd: launched.append(cmd)
                        or True)
    monkeypatch.setattr(kpl, "find_khervepaint", lambda: ["/kp"])
    r = ex.execute("open_in_khervepaint", {"index": at})
    assert r["opened"].endswith(".svg")
    assert launched == [["/kp", r["opened"]]]
    monkeypatch.setattr(kpl, "find_khervepaint", lambda: None)
    assert "Locate" in ex.execute("open_in_khervepaint",
                                  {"index": at})["error"]


def test_tool_categories():
    assert tool_allowed("get_drawing", "read")
    assert tool_allowed("list_drawing_symbols", "read")
    assert not tool_allowed("insert_drawing", "read")
    assert tool_allowed("open_in_khervepaint", "edit")


# ── KhervePaint locator ────────────────────────────────────────────

def test_locator_prefers_settings_override(qapp, tmp_path, monkeypatch):
    exe = tmp_path / "KhervePaint.exe"
    exe.write_text("")
    QSettings().setValue(kpl.SETTINGS_KEY, str(exe))
    try:
        assert kpl.find_khervepaint() == [str(exe)]
    finally:
        QSettings().remove(kpl.SETTINGS_KEY)


def test_locator_app_bundle_and_source_checkout(qapp, tmp_path,
                                                monkeypatch):
    app = tmp_path / "KhervePaint.app"
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "MacOS" / "KhervePaint").write_text("")
    assert kpl._command_for(app) == [
        str(app / "Contents" / "MacOS" / "KhervePaint")]

    src = tmp_path / "src" / "KhervePaint.py"
    (src.parent / ".venv" / "bin").mkdir(parents=True)
    src.write_text("")
    py = src.parent / ".venv" / "bin" / "python"
    py.write_text("")
    assert kpl._command_for(src) == [str(py), str(src)]

    monkeypatch.setattr(kpl, "candidate_paths",
                        lambda: [tmp_path / "missing.exe", src])
    assert kpl.find_khervepaint() == [str(py), str(src)]
    monkeypatch.setattr(kpl, "candidate_paths", lambda: [])
    assert kpl.find_khervepaint() is None


def test_source_checkout_without_pyqt5_is_skipped(qapp, tmp_path,
                                                  monkeypatch):
    src = tmp_path / "KhervePaint.py"
    src.write_text("")
    monkeypatch.setattr(kpl.importlib.util, "find_spec", lambda n: None)
    assert kpl._command_for(src) is None


def test_set_custom_path_rejects_missing(qapp, tmp_path):
    assert not kpl.set_custom_path(str(tmp_path / "nope"))


# ── watcher: KhervePaint saves flow back ───────────────────────────

def _wait(qapp, cond, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        qapp.processEvents()
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_saved_svg_regenerates_pdf_png_and_refreshes(window, qapp,
                                                     monkeypatch):
    from khervedoc.paint import export
    from khervedoc.paint.authoring import add_shapes, new_scene
    _load(window, "Text.")
    ex = ToolExecutor(window)
    r = ex.execute("insert_drawing", {"shapes": FLOW[:1]})
    png = Path(r["files"]["png"])
    svg, pdf = png.with_suffix(".svg"), png.with_suffix(".pdf")

    link = window._editor.khervepaint_link()
    monkeypatch.setattr(link, "_launch", lambda cmd: True)
    monkeypatch.setattr(kpl, "find_khervepaint", lambda: ["/kp"])
    link._timer.setInterval(50)
    refreshed = []
    real = window._editor.refresh_figure_image
    monkeypatch.setattr(window._editor, "refresh_figure_image",
                        lambda p: refreshed.append(p) or real(p))
    # the signal was connected to the bound method before the patch
    link.drawingUpdated.disconnect()
    link.drawingUpdated.connect(window._editor.refresh_figure_image)
    assert ex.execute("open_in_khervepaint",
                      {"index": r["at_index"]})["opened"]

    before = (png.stat().st_mtime_ns, pdf.stat().st_mtime_ns,
              png.stat().st_size)
    time.sleep(0.05)
    # What KhervePaint would do: rewrite the SVG with a bigger drawing.
    scene = new_scene()
    add_shapes(scene, FLOW[:1] + [{"type": "rect", "x": 0, "y": 40,
                                   "w": 80, "h": 30}])
    export.save_svg(scene, svg)

    assert _wait(qapp, lambda: refreshed), "no refresh after the save"
    assert png.stat().st_mtime_ns > before[0]
    assert pdf.stat().st_mtime_ns > before[1]
    assert png.stat().st_size != before[2]
    assert Path(refreshed[0]) == png
    assert str(svg.resolve()) in link.watched()


def test_regenerate_leaves_svg_alone(qapp, tmp_path):
    from khervedoc.paint import export
    from khervedoc.paint.authoring import add_shapes, new_scene
    scene = new_scene()
    add_shapes(scene, FLOW[:2])
    svg = tmp_path / "d.svg"
    export.save_svg(scene, svg)
    before = svg.read_bytes()
    png = kpl.regenerate_from_svg(svg)
    assert png == tmp_path / "d.png" and png.exists()
    assert (tmp_path / "d.pdf").exists() and svg.read_bytes() == before


def test_repeated_calls_do_not_pad_figures(window):
    _load(window, "Text.")
    ex = ToolExecutor(window)
    ex.execute("insert_drawing", {"shapes": FLOW[:1]})
    n = len(_blocks(window))
    ex.execute("insert_equation", {"latex": "x", "after": 0})
    ex.execute("insert_equation", {"latex": "y", "after": 0})
    assert len(_blocks(window)) == n + 2


def test_mhchem_is_drawn_as_typeset_chemistry():
    from khervedoc.editor import _ce_to_math
    from khervedoc import mathbox as mb
    from khervedoc.editor import _contains_raw
    cases = {
        r"\ce{2H2 + O2 -> 2H2O}":
            r"2\,\mathrm{H}_{2} + \mathrm{O}_{2} \rightarrow "
            r"2\,\mathrm{H}_{2}\mathrm{O}",
        r"\ce{Na+ + Cl- -> NaCl}":
            r"\mathrm{Na}^{+} + \mathrm{Cl}^{-} \rightarrow "
            r"\mathrm{Na}\mathrm{Cl}",
        r"\ce{CuSO4.5H2O}":
            r"\mathrm{Cu}\mathrm{S}\mathrm{O}_{4}\cdot 5\,"
            r"\mathrm{H}_{2}\mathrm{O}",
    }
    for src, want in cases.items():
        got = _ce_to_math(src)
        assert got == want
        assert not _contains_raw(mb.parse_latex(got))


def test_first_heading_is_left_aligned_after_a_rebuild(qapp):
    from PySide6.QtCore import Qt
    from khervedoc.editor import DocumentEditor
    from khervedoc.model import Document, Section, Text, Title
    ed = DocumentEditor()
    ed.set_document(Document(children=[Title(children=[Text("T")])]))
    ed.replace_body([Section(level=1, children=[Text("Setup")])])
    doc = ed._edit.document()
    b = doc.firstBlock()
    while b.isValid() and b.text() != "Setup":
        b = b.next()
    assert b.blockFormat().alignment() & Qt.AlignHorizontal_Mask == Qt.AlignLeft
