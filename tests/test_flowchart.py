"""The flowchart builder: the Qt-free model and its TikZ (flowchart.py),
Figure.source == "flowchart" in the serializers and .kdocz bundles, the
offline warm-up, and the builder / editor round trip."""
import json
import os
import zipfile

import pytest

from khervedoc.flowchart import (
    DEFAULT_SCHEME, SCHEME_NAMES, TEMPLATES, TIKZ_LIBRARIES, Flowchart, Node,
    auto_layout, colours, standalone_doc, template_simple, to_tikz,
)
from khervedoc.kdocz import load_kdocz, save_kdocz
from khervedoc.model import Document, Figure, from_json, to_json
from khervedoc.serializer import serialize_block
from khervedoc.typst_serializer import serialize_block as typst_block


# --- the model -------------------------------------------------------------

def test_add_chains_and_connects():
    fc = Flowchart()
    a = fc.add("terminal", "Start")
    b = fc.add("process", after=a.id)
    c = fc.add("decision", "OK?", after=b.id, label="")
    assert (b.x, b.y) == (0, 1) and (c.x, c.y) == (0, 2)
    assert [(e.src, e.dst) for e in fc.edges] == [(a.id, b.id), (b.id, c.id)]
    assert b.text == "Process"                 # the shape's name by default
    d = fc.add("process", "side", after=b.id)  # spot taken: sidesteps
    assert (d.x, d.y) == (1, 2)
    assert fc.connect(a.id, a.id) is None      # no self-loops
    assert fc.connect(a.id, b.id) is fc.edges[0]   # no duplicates
    fc.remove(b.id)
    assert fc.node(b.id) is None
    assert all(b.id not in (e.src, e.dst) for e in fc.edges)


def test_left_to_right_and_json_round_trip():
    fc = Flowchart(direction="LR")
    a = fc.add("database", "Data")
    b = fc.add("process", "Clean", after=a.id)
    assert (b.x, b.y) == (1, 0)
    fc.edges[0].label = "raw"
    fc.nodes[0].fill = "#FF0000"
    back = Flowchart.from_json(fc.to_json())
    assert back == fc


def test_tikz_shapes_routes_and_colours():
    fc = TEMPLATES["Algorithm (sum to n)"]()
    assert len({n.id for n in fc.nodes}) == len(fc.nodes)   # unique ids
    tikz = to_tikz(fc)
    assert tikz.count("\\node[") == len(fc.nodes)
    assert tikz.count("\\draw[") == len(fc.edges)
    assert "diamond" in tikz and "trapezium" in tikz
    assert "rounded rectangle" in tikz
    assert "{HTML}{1F4E79}" in tikz            # the default (Blue) scheme
    assert "node[pos=0.25" in tikz and "{Yes}" in tikz
    # the loop back to the decision goes round the left side
    assert ".west) -- ++(-1.9,0)" in tikz
    doc = standalone_doc(fc)
    for lib in TIKZ_LIBRARIES:
        assert lib in doc
    assert doc.startswith("\\documentclass[border=4pt]{standalone}")
    for name, make in TEMPLATES.items():
        assert make().nodes, name


def test_default_scheme_and_kherveslide_charts():
    # No presentation in KherveTeX: the schemes are the fixed ones, and a
    # chart made in KherveSlide with "Presentation colours" still draws.
    assert "Presentation colours" not in SCHEME_NAMES
    assert Flowchart().scheme == DEFAULT_SCHEME == SCHEME_NAMES[0]
    slide = Flowchart(scheme="Presentation colours")
    assert colours(slide) == colours(Flowchart())
    green = Flowchart(scheme="Green")
    assert colours(green)["terminal"][0] == "#2E6B30"


def test_arrowheads_lines_and_chosen_sides():
    fc = Flowchart()
    a = fc.add("process", "A")
    b = fc.add("process", "B", after=a.id)
    e = fc.edges[0]
    assert (e.head, e.src_side, e.dst_side) == ("end", "auto", "auto")
    assert "\\draw[line, ->]" in to_tikz(fc)
    e.head = "both"
    assert "\\draw[line, <->]" in to_tikz(fc)
    e.head = "none"                            # a plain line
    e.dashed = True
    assert "\\draw[line, -, dashed]" in to_tikz(fc)
    e.head, e.dashed = "start", False
    assert "\\draw[line, <-]" in to_tikz(fc)
    # leave from the right, come back into the right: stub then |-
    e.src_side = e.dst_side = "east"
    assert (f"({a.id}.east) -- ++(0.35,0) |- ({b.id}.east);"
            in to_tikz(fc))
    e.dst_side = "north"                       # into the top: -|
    assert f"({a.id}.east) -- ++(0.35,0) -| ({b.id}.north);" in to_tikz(fc)
    e.route = "straight"
    assert f"({a.id}.east) -- ++(0.35,0) -- ({b.id}.north);" in to_tikz(fc)
    back = Flowchart.from_json(fc.to_json())
    assert back == fc and back.edges[0].head == "start"
    # charts saved before these options still load
    d = json.loads(fc.to_json())
    for k in ("head", "src_side", "dst_side"):
        d["edges"][0].pop(k)
    old = Flowchart.from_json(json.dumps(d))
    assert (old.edges[0].head, old.edges[0].src_side) == ("end", "auto")


def test_curved_links():
    fc = Flowchart()
    a = fc.add("process", "A")
    b = fc.add("process", "B", after=a.id)
    e = fc.edges[0]
    e.route = "curve"
    assert f"({a.id}) to[bend left=30] ({b.id});" in to_tikz(fc)
    e.bend = -45
    assert f"({a.id}) to[bend right=45] ({b.id});" in to_tikz(fc)
    e.bend = 0                                 # no bow: a straight line
    assert f"({a.id}) -- ({b.id});" in to_tikz(fc)
    e.src_side, e.dst_side = "east", "north"   # follows both sides
    assert (f"({a.id}.east) to[out=0, in=90] ({b.id}.north);"
            in to_tikz(fc))
    e.label = "loop"
    assert "to[out=0, in=90] node[pos=0.25" in to_tikz(fc)
    assert Flowchart.from_json(fc.to_json()).edges[0].bend == 0


def test_auto_layout_ranks_by_path():
    fc = Flowchart()
    for nid in ("a", "b", "c", "d"):
        fc.nodes.append(Node(nid, "process", nid, 5, 5))
    fc.connect("a", "b"); fc.connect("a", "c"); fc.connect("b", "d")
    fc.connect("c", "d"); fc.connect("d", "a")          # a loop back
    auto_layout(fc)
    y = {n.id: n.y for n in fc.nodes}
    assert y == {"a": 0, "b": 1, "c": 1, "d": 2}
    xs = sorted(n.x for n in fc.nodes if n.id in "bc")
    assert xs == [-0.5, 0.5]                           # spread around 0


# --- Figure.source == "flowchart" ------------------------------------------

def test_flowchart_figure_source_round_trips():
    doc = Document(children=[Figure(path="figures/flowchart_001.png",
                                    source="flowchart")])
    assert from_json(to_json(doc)).children[0].source == "flowchart"


def test_latex_uses_the_flowchart_pdf_and_typst_its_png():
    fig = Figure(path="figures\\flowchart_001.png", source="flowchart")
    assert "{figures/flowchart_001.pdf}" in serialize_block(fig)
    # there is no SVG of a flowchart: Typst keeps the preview
    assert 'image("figures/flowchart_001.png"' in typst_block(fig)


def test_kdocz_bundles_flowchart_siblings(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for ext in (".png", ".pdf", ".flow.json", ".tikz"):
        (src / f"flowchart_001{ext}").write_bytes(b"x" + ext.encode())
    doc = Document(children=[Figure(path=str(src / "flowchart_001.png"),
                                    source="flowchart")])
    out = tmp_path / "doc.kdocz"
    save_kdocz(doc, out)
    names = set(zipfile.ZipFile(out).namelist())
    assert {"figures/figure_001.png", "figures/figure_001.pdf",
            "figures/figure_001.flow.json",
            "figures/figure_001.tikz"} <= names

    loaded, extract = load_kdocz(out, tmp_path / "x")
    fig = loaded.children[0]
    assert fig.source == "flowchart" and fig.path.endswith("figure_001.png")
    assert (extract / "figures" / "figure_001.flow.json").exists()


# --- offline warm-up ---------------------------------------------------------

def test_offline_bundle_warms_the_flowchart_libraries(monkeypatch):
    from khervedoc import compiler
    seen: dict[str, str] = {}

    class FakeProc:
        returncode = 0
        stdout: list = []

        def __init__(self, cmd, **_kw):
            tex = cmd[-1]
            seen[os.path.basename(tex)] = open(tex, encoding="utf-8").read()

        def wait(self):
            return 0

    monkeypatch.setattr(compiler, "_find_tectonic", lambda: "tectonic")
    monkeypatch.setattr(compiler.subprocess, "Popen", FakeProc)
    ok, _log = compiler.download_tectonic_bundle()
    assert ok
    for lib in TIKZ_LIBRARIES:
        assert lib in seen["flowchart.tex"]


# --- the builder and the editor (Qt) -----------------------------------------

@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    yield QApplication.instance() or QApplication([])


def _pdf_bytes(w_pt: float = 283.0, h_pt: float = 200.0) -> bytes:
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=w_pt, height=h_pt)
    page.draw_rect(pymupdf.Rect(10, 10, w_pt - 10, h_pt - 10),
                   color=(0, 0, 0), fill=(0.8, 0.9, 1.0))
    data = doc.tobytes()
    doc.close()
    return data


def test_box_text_renders_maths_and_escapes():
    pytest.importorskip("PySide6")
    from khervedoc.flowchart_builder import _pretty_inline_html
    out = _pretty_inline_html("$i \\le n$? 50\\% -- <ok>")
    assert "≤" in out and "<i>" in out
    assert "50%" in out and "–" in out and "&lt;ok&gt;" in out
    assert "<sup>2</sup>" in _pretty_inline_html("$x^2$")
    assert "<sub>ij</sub>" in _pretty_inline_html("$a_{ij}$")


def test_flowchart_files_and_width(qapp, tmp_path):
    from khervedoc import flowchart_builder as FB
    path = FB.next_flowchart_path(tmp_path)
    assert path.name == "flowchart_001.png"
    pdf = _pdf_bytes()
    fc = template_simple()
    assert FB.save_flowchart(path, fc, pdf, to_tikz(fc))
    for ext in (".png", ".pdf", ".flow.json", ".tikz"):
        assert path.with_suffix(ext).exists(), ext
    assert FB.flowchart_source_for(path) == path.with_suffix(".flow.json")
    assert FB.flowchart_source_for(tmp_path / "photo.png") is None
    assert FB.next_flowchart_path(tmp_path).name == "flowchart_002.png"
    # 283 pt ≈ 10 cm of a 15 cm text block
    assert FB.natural_width(pdf) == "0.67\\textwidth"
    assert FB.natural_width(_pdf_bytes(2000)) == "1\\textwidth"


def test_builder_arrow_curve_and_line_tools(qapp, monkeypatch):
    from khervedoc import flowchart_builder as FB
    monkeypatch.setattr(FB.FlowchartBuilderDialog, "_schedule",
                        lambda self: None)
    fc = Flowchart()
    a = fc.add("process", "A")
    b = fc.add("process", "B")
    dlg = FB.FlowchartBuilderDialog(chart=fc)
    assert dlg.scheme.currentText() == DEFAULT_SCHEME
    items = {i.node.id: i for i in dlg.scene.items()
             if isinstance(i, FB.NodeItem)}
    dlg._tool_buttons["none"].setChecked(True)      # the Line tool
    assert dlg.view.connect_mode
    dlg._tool_click(items[a.id])
    dlg._tool_click(items[b.id])
    assert [(e.src, e.dst, e.head) for e in dlg.fc.edges] == \
        [(a.id, b.id, "none")]
    dlg._tool_click(None)                           # empty space: stop
    assert not dlg.view.connect_mode
    dlg._tool_buttons["curve"].setChecked(True)     # the Curve tool
    assert not dlg._tool_buttons["none"].isChecked()
    items = {i.node.id: i for i in dlg.scene.items()     # rebuilt
             if isinstance(i, FB.NodeItem)}
    dlg._tool_click(items[b.id])
    dlg._tool_click(items[a.id])
    curve = dlg.fc.edges[-1]
    assert (curve.src, curve.route, curve.head) == (b.id, "curve", "end")
    item = next(i for i in dlg.scene.items()
                if isinstance(i, FB.EdgeItem) and i.edge is curve)
    assert len(item._pts) > 10                      # drawn as a curve
    dlg._tool_buttons["curve"].setChecked(False)
    dlg.fc.edges.remove(curve)
    dlg._commit()
    edge = next(i for i in dlg.scene.items() if isinstance(i, FB.EdgeItem))
    dlg.scene.clearSelection()
    edge.setSelected(True)
    assert dlg._selected_edge is edge
    dlg._set_edge(head="both", src_side="east", dst_side="west")
    e = dlg.fc.edges[0]
    assert (e.head, e.src_side, e.dst_side) == ("both", "east", "west")
    edge = next(i for i in dlg.scene.items() if isinstance(i, FB.EdgeItem))
    assert len(edge._pts) >= 3                      # stub + elbow
    dlg._reverse_edge()
    dlg._step(-1)                                   # undo
    assert dlg.fc.edges[0].src == a.id
    dlg.close()


def test_editor_inserts_flowchart_and_reopens_it(qapp, tmp_path,
                                                 monkeypatch):
    from PySide6.QtWidgets import QDialog
    from khervedoc import editor as E
    from khervedoc import flowchart_builder as FB
    from khervedoc.model import Paragraph, Text

    seen: dict = {}

    def fake_exec(self):
        seen["chart"] = self.fc.to_json()
        self.result_chart = self.fc
        self.result_pdf = _pdf_bytes()
        self.result_tikz = to_tikz(self.fc)
        return QDialog.Accepted
    monkeypatch.setattr(FB.FlowchartBuilderDialog, "exec", fake_exec)
    monkeypatch.setattr(FB.FlowchartBuilderDialog, "_schedule",
                        lambda self: None)
    monkeypatch.setattr(E._InsertFigureDialog, "exec",
                        lambda self: QDialog.Accepted)

    ed = E.DocumentEditor()
    ed.resize(1000, 800)
    ed.set_document(Document(children=[Paragraph(children=[Text("Hi")])]))
    ed._images_dir = tmp_path
    ed.insert_flowchart()
    figs = [b for b in ed.get_document().children if isinstance(b, Figure)]
    assert len(figs) == 1
    fig = figs[0]
    assert fig.source == "flowchart" and fig.width == "0.67\\textwidth"
    png = tmp_path / "flowchart_001.png"
    assert fig.path == str(png) and png.exists()
    assert "\\begin{tikzpicture}" in png.with_suffix(".tikz").read_text()
    assert "{" + str(png.with_suffix(".pdf")).replace("\\", "/") + "}" \
        in serialize_block(fig)

    # double-click (the figure editor) reopens the builder on the chart
    saved = Flowchart.from_json(png.with_suffix(".flow.json").read_text())
    saved.nodes[0].text = "Begin"
    png.with_suffix(".flow.json").write_text(saved.to_json())
    seen.clear()
    table = next(ed._figure_tables())
    ed._edit_existing_figure(table)
    assert Flowchart.from_json(seen["chart"]).nodes[0].text == "Begin"
    figs = [b for b in ed.get_document().children if isinstance(b, Figure)]
    assert len(figs) == 1 and figs[0].path == str(png)   # replaced in place
    ed.close()


def test_insert_menu_and_shortcut(qapp):
    from PySide6.QtGui import QKeySequence
    from khervedoc.mainwindow import MainWindow
    win = MainWindow()
    try:
        act = win.act_flowchart
        assert act.shortcut().toString(QKeySequence.PortableText) == \
            "Ctrl+Shift+F"
        assert act in win._side_tb.actions()
        assert not act.icon().isNull()
    finally:
        win.close()
