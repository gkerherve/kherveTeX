"""Figure.source for drawings: model round-trip, LaTeX/Typst paths and
.kdocz bundling of the SVG/PDF siblings."""
import json
import zipfile

from khervedoc.kdocz import load_kdocz, save_kdocz
from khervedoc.model import Document, Figure, from_json, to_json
from khervedoc.serializer import serialize_block
from khervedoc.typst_serializer import serialize_block as typst_block


def test_figure_source_round_trips():
    doc = Document(children=[Figure(path="images/drawing_001.png",
                                    caption="c", source="drawing")])
    back = from_json(to_json(doc))
    assert back.children[0].source == "drawing"


def test_figure_source_defaults_for_old_json():
    data = json.loads(to_json(Document(children=[Figure(path="a.png")])))
    del data["children"][0]["source"]
    back = from_json(json.dumps(data))
    assert back.children[0].source == ""


def test_latex_uses_pdf_for_drawings():
    tex = serialize_block(Figure(path="images\\drawing_001.png",
                                 source="drawing"))
    assert "{images/drawing_001.pdf}" in tex


def test_latex_keeps_plain_figures_unchanged():
    tex = serialize_block(Figure(path="images/photo.png"))
    assert "{images/photo.png}" in tex


def test_typst_uses_svg_for_drawings():
    out = typst_block(Figure(path="images/drawing_001.png", source="drawing"))
    assert 'image("images/drawing_001.svg"' in out


def test_kdocz_bundles_drawing_siblings(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for ext in (".png", ".svg", ".pdf"):
        (src / f"drawing_001{ext}").write_bytes(b"x" + ext.encode())
    doc = Document(children=[Figure(path=str(src / "drawing_001.png"),
                                    source="drawing")])
    out = tmp_path / "doc.kdocz"
    save_kdocz(doc, out)
    names = zipfile.ZipFile(out).namelist()
    assert {"figures/figure_001.png", "figures/figure_001.svg",
            "figures/figure_001.pdf"} <= set(names)

    loaded, extract = load_kdocz(out, tmp_path / "x")
    fig = loaded.children[0]
    assert fig.source == "drawing"
    assert fig.path.endswith("figure_001.png")
    assert (extract / "images" / "figure_001.pdf").exists()


def test_kdocz_does_not_bundle_siblings_of_plain_figures(tmp_path):
    (tmp_path / "photo.png").write_bytes(b"png")
    (tmp_path / "photo.pdf").write_bytes(b"pdf")
    out = tmp_path / "doc.kdocz"
    save_kdocz(Document(children=[Figure(path=str(tmp_path / "photo.png"))]),
               out)
    names = zipfile.ZipFile(out).namelist()
    assert "figures/figure_001.pdf" not in names


def test_figure_is_shown_at_its_latex_width_and_resizes_with_mouse(tmp_path):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QColor, QImage, QMouseEvent
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from khervedoc.editor import DocumentEditor
    from khervedoc.model import Document, Figure

    img = QImage(400, 200, QImage.Format_RGB32)
    img.fill(QColor("steelblue"))
    path = tmp_path / "pic.png"
    img.save(str(path))
    ed = DocumentEditor()
    ed.resize(1000, 800)
    from khervedoc.model import Paragraph, Text
    # Text before the figure: a figure lives in a table, and positions
    # computed from the cell's own layout put the handle at the top of
    # the page instead of on the image.
    ed.set_document(Document(children=[
        Paragraph(children=[Text("Some text above. " * 30)]),
        Figure(path=str(path), caption="c", width="0.5\\textwidth")]))
    ed.show()
    QApplication.processEvents()
    edit = ed._edit
    text_w = edit.text_width_px()
    table = next(f for f in edit.document().rootFrame().childFrames())
    pos = table.cellAt(0, 0).firstCursorPosition().position()
    rect = edit._image_view_rect(pos, _image_fmt(edit, pos))
    assert abs(rect.width() - 0.5 * text_w) < 2        # 0.5\textwidth
    under = edit.cursorForPosition(rect.center().toPoint()).position()
    assert under in (pos, pos + 1)                     # rect is on the image
    assert rect.top() > 60
    assert abs(rect.height() - rect.width() / 2) < 2   # aspect kept

    def send(kind, at, buttons):
        ev = QMouseEvent(kind, at, at, Qt.LeftButton if kind != QEvent.MouseMove
                         else Qt.NoButton, buttons, Qt.NoModifier)
        {QEvent.MouseMove: edit.mouseMoveEvent,
         QEvent.MouseButtonPress: edit.mousePressEvent,
         QEvent.MouseButtonRelease: edit.mouseReleaseEvent}[kind](ev)

    corner = QPointF(rect.right(), rect.bottom())
    send(QEvent.MouseMove, corner, Qt.NoButton)            # hover
    assert edit._hover_img is not None
    send(QEvent.MouseButtonPress, corner, Qt.LeftButton)
    target = QPointF(corner.x() + 0.2 * text_w, corner.y())
    send(QEvent.MouseMove, target, Qt.LeftButton)
    send(QEvent.MouseButtonRelease, target, Qt.NoButton)
    fig = next(b for b in ed.get_document().children
               if isinstance(b, Figure))
    assert fig.width == "0.70\\textwidth"


def _image_fmt(edit, pos):
    from PySide6.QtGui import QTextCursor
    c = QTextCursor(edit.document())
    c.setPosition(pos)
    c.setPosition(pos + 1, QTextCursor.KeepAnchor)
    return c.charFormat().toImageFormat()
