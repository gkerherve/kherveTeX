"""The KhervePaint-based drawing dialog: tools create items from mouse
gestures, undo/redo, SVG round-trip, the three output files and legacy
JSON drawings."""
import json
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc.paint import canvas as C  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


@pytest.fixture
def dlg(qapp, tmp_path):
    from khervedoc.drawing_dialog import DrawingDialog
    d = DrawingDialog(tmp_path)
    d.resize(1200, 800)
    d.show()
    qapp.processEvents()
    d.view.zoom_reset()
    d.view.centerOn(450, 300)
    qapp.processEvents()
    yield d
    d.close()


def _pt(d, x, y):
    return d.view.mapFromScene(QPointF(x, y))


def _drag(d, tool, a, b):
    d.set_tool(tool)
    vp = d.view.viewport()
    QTest.mousePress(vp, Qt.LeftButton, Qt.NoModifier, _pt(d, *a))
    for i in range(1, 5):
        QTest.mouseMove(vp, _pt(d, a[0] + (b[0] - a[0]) * i / 4,
                                a[1] + (b[1] - a[1]) * i / 4))
    QTest.mouseRelease(vp, Qt.LeftButton, Qt.NoModifier, _pt(d, *b))


def _click(d, tool, a):
    d.set_tool(tool)
    QTest.mouseClick(d.view.viewport(), Qt.LeftButton, Qt.NoModifier,
                     _pt(d, *a))


SHAPE_TOOLS = [
    (C.LINE, C.LineItem), (C.ARROW, C.ArrowItem),
    (C.DIMENSION, C.DimensionItem), (C.RECT, C.RectItem),
    (C.ROUNDRECT, C.RoundedRectItem), (C.CIRCLE, C.EllipseItem),
    (C.ELLIPSE, C.EllipseItem), (C.HALFCIRCLE, C.ArcShapeItem),
    (C.QUARTERCIRCLE, C.ArcShapeItem), (C.TRIANGLE, C.PolygonItem),
    (C.HEXAGON, C.PolygonItem), (C.STAR, C.PolygonItem),
    (C.PENCIL, C.PathItem),
]


@pytest.mark.parametrize("tool,cls", SHAPE_TOOLS)
def test_shape_tool_creates_item(dlg, tool, cls):
    _drag(dlg, tool, (100, 100), (220, 180))
    items = dlg.scene.vector_items()
    assert len(items) == 1
    assert isinstance(items[0], cls)


def test_symbol_and_text_tools(dlg):
    dlg.scene.flow_element = "decision"
    _click(dlg, C.FLOW_PLACE, (300, 300))
    dlg.scene.elec_element = "resistor"
    _click(dlg, C.ELEC_PLACE, (100, 300))
    _click(dlg, C.TEXT, (100, 100))
    kinds = [type(i) for i in dlg.scene.vector_items()]
    assert kinds.count(C.GroupItem) == 2
    assert C.TextItem in kinds


def test_bucket_eraser_protractor(dlg):
    _drag(dlg, C.RECT, (100, 100), (200, 200))
    _click(dlg, C.BUCKET, (150, 150))
    assert [type(i) for i in dlg.scene.vector_items()] == [C.PathItem,
                                                           C.RectItem]
    _drag(dlg, C.ERASER, (100, 150), (100, 150))
    assert C.RectItem not in [type(i) for i in dlg.scene.vector_items()]
    dlg.set_tool(C.PROTRACTOR)
    for p in ((400, 300), (500, 300), (400, 200)):
        QTest.mouseClick(dlg.view.viewport(), Qt.LeftButton, Qt.NoModifier,
                         _pt(dlg, *p))
    assert isinstance(dlg.scene.vector_items()[-1], C.GroupItem)


def test_undo_redo(dlg):
    _drag(dlg, C.RECT, (50, 50), (150, 150))
    _drag(dlg, C.ELLIPSE, (200, 50), (300, 150))
    assert len(dlg.scene.vector_items()) == 2
    dlg._undo.undo()
    assert len(dlg.scene.vector_items()) == 1
    dlg._undo.undo()
    assert len(dlg.scene.vector_items()) == 0
    dlg._undo.redo()
    dlg._undo.redo()
    assert len(dlg.scene.vector_items()) == 2


def test_style_applies_to_selection_and_is_undoable(dlg):
    _drag(dlg, C.RECT, (50, 50), (150, 150))
    rect = dlg.scene.vector_items()[0]
    rect.setSelected(True)
    dlg._stroke_btn.set_color(QColor("#d8000c"), emit=True)
    assert dlg.scene.vector_items()[0].pen().color().name() == "#d8000c"
    dlg._undo.undo()
    assert dlg.scene.vector_items()[0].pen().color().name() != "#d8000c"


def test_group_copy_paste_delete(dlg):
    _drag(dlg, C.RECT, (50, 50), (150, 150))
    _drag(dlg, C.CIRCLE, (200, 50), (300, 150))
    dlg._select_all()
    dlg.scene.group_selection()
    assert [type(i) for i in dlg.scene.vector_items()] == [C.GroupItem]
    dlg.duplicate_selection()
    assert len(dlg.scene.vector_items()) == 2
    dlg.delete_selection()
    assert len(dlg.scene.vector_items()) == 1


def _populate(scene):
    from PySide6.QtGui import QBrush, QPen
    from khervedoc.paint import gradient
    r = C.RoundedRectItem(QRectF(10, 20, 120, 60), 10)
    r.setBrush(gradient.brush_for("linear", QColor("#ffffff"),
                                  QColor("#1a6dd8"), 90))
    a = C.ArrowItem(QLineF(140, 50, 260, 50))
    a.set_head("double")
    pen = QPen(QColor("#d8000c"), 3)
    pen.setStyle(Qt.DashLine)
    a.setPen(pen)
    poly = C.PolygonItem(kind=C.HEXAGON)
    poly.set_rect(QRectF(280, 10, 90, 80))
    dim = C.DimensionItem(QLineF(10, 120, 130, 120))
    t = C.TextItem("Label")
    t.setPos(30, 150)
    for it in (r, a, poly, dim, t):
        scene.addItem(it)
    scene.place_flow_element("process", QPointF(200, 200))
    return [r, a, poly, dim, t]


def test_svg_round_trip_preserves_items(qapp, tmp_path):
    from khervedoc.paint import export
    s = C.PaintScene(900, 600)
    _populate(s)
    before = s.vector_items()
    path = tmp_path / "d.svg"
    export.save_svg(s, path)
    s2 = C.PaintScene(10, 10)
    export.load_svg(s2, path)
    after = s2.vector_items()
    assert [type(i) for i in after] == [type(i) for i in before]
    for x, y in zip(before, after):
        bx, by = x.sceneBoundingRect(), y.sceneBoundingRect()
        for u, v in ((bx.x(), by.x()), (bx.y(), by.y()),
                     (bx.width(), by.width()), (bx.height(), by.height())):
            assert abs(u - v) < 1.5
    arrow = after[1]
    assert arrow.head == "double"
    assert arrow.pen().style() == Qt.DashLine
    assert after[0].brush().gradient() is not None
    assert after[4].toPlainText() == "Label"


def test_save_drawing_writes_svg_pdf_png(qapp, tmp_path):
    from khervedoc.paint import export
    s = C.PaintScene(900, 600)
    _populate(s)
    png = tmp_path / "drawing_001.png"
    assert export.save_drawing(s, png)
    for ext in (".png", ".svg", ".pdf"):
        assert png.with_suffix(ext).stat().st_size > 0
    assert png.with_suffix(".pdf").read_bytes().startswith(b"%PDF")
    # The blank raster page is not embedded in the editable SVG.
    assert "<image" not in png.with_suffix(".svg").read_text()


def test_empty_drawing_saves_nothing(qapp, tmp_path):
    from khervedoc.paint import export
    assert not export.save_drawing(C.PaintScene(), tmp_path / "x.png")


def test_dialog_ok_then_reopen(dlg, qapp, tmp_path):
    from khervedoc.drawing_dialog import DrawingDialog
    _drag(dlg, C.RECT, (50, 50), (150, 150))
    _drag(dlg, C.ARROW, (160, 100), (260, 100))
    dlg._accept_and_save()
    png = dlg.saved_path()
    assert png is not None and png.name == "drawing_001.png"
    assert png.with_suffix(".svg").exists()
    again = DrawingDialog(tmp_path, existing_path=png)
    kinds = [type(i) for i in again.scene.vector_items()]
    assert kinds == [C.RectItem, C.ArrowItem]
    again.close()


def test_legacy_json_drawing_loads(qapp, tmp_path):
    from khervedoc.drawing_dialog import DrawingDialog, drawing_source_for
    png = tmp_path / "drawing_001.png"
    png.write_bytes(b"")
    legacy = {"version": 1, "items": [
        {"type": "rect", "x": 10, "y": 10, "w": 50, "h": 40,
         "color": "#000000", "width": 2},
        {"type": "ellipse", "x": 70, "y": 10, "w": 50, "h": 40,
         "color": "#1a6dd8", "width": 2},
        {"type": "line", "x1": 0, "y1": 0, "x2": 30, "y2": 30,
         "color": "#000000", "width": 2},
        {"type": "text", "x": 5, "y": 60, "text": "hi", "color": "#000000",
         "font_size": 12},
        {"type": "arrow", "color": "#000000", "width": 2, "elements": [
            {"t": "M", "x": 0, "y": 100}, {"t": "L", "x": 80, "y": 100},
            {"t": "M", "x": 80, "y": 100}, {"t": "L", "x": 72, "y": 96}]},
        {"type": "path", "color": "#000000", "width": 2, "elements": [
            {"t": "M", "x": 0, "y": 0}, {"t": "L", "x": 5, "y": 8}]},
    ]}
    png.with_suffix(".json").write_text(json.dumps(legacy))
    assert drawing_source_for(png) == png.with_suffix(".json")
    d = DrawingDialog(tmp_path, existing_path=png)
    kinds = [type(i) for i in d.scene.vector_items()]
    assert kinds == [C.RectItem, C.EllipseItem, C.LineItem, C.TextItem,
                     C.ArrowItem, C.PathItem]
    d._accept_and_save()
    assert png.with_suffix(".svg").exists()
    assert drawing_source_for(png) == png.with_suffix(".svg")
    d.close()
