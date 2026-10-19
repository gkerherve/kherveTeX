"""Word-style object tools: table rows/columns/delete/style, picture
alignment and width, equation numbering, and their LaTeX output."""
import os

import pytest

from khervedoc.model import (
    Document, Figure, MathBlock, Paragraph, Table, Text, from_json, to_json,
)
from khervedoc.serializer import serialize_block
from khervedoc.typst_serializer import serialize_document as typst_doc


@pytest.mark.parametrize("align,cmd", [("left", r"\raggedright"),
                                       ("center", r"\centering"),
                                       ("right", r"\raggedleft")])
def test_figure_alignment_in_latex(align, cmd):
    out = serialize_block(Figure(path="a.png", caption="c", align=align))
    assert cmd in out


def test_figure_alignment_round_trips_json_and_defaults_center():
    doc = Document(children=[Figure(path="a.png", align="right")])
    assert from_json(to_json(doc)).children[0].align == "right"
    import json
    d = json.loads(to_json(doc))
    del d["children"][0]["align"]
    assert from_json(json.dumps(d)).children[0].align == "center"


def test_figure_alignment_in_typst():
    out = typst_doc(Document(children=[Figure(path="a.png", align="left")]))
    assert "#align(left)[#figure(" in out


# ---------- editor ----------

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _editor(tmp_path, *blocks):
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from khervedoc.editor import DocumentEditor
    ed = DocumentEditor()
    ed.set_document_dir(tmp_path)
    ed.set_document(Document(children=list(blocks)))
    return ed


def _caret_in_frame(ed, n):
    frame = ed._edit.document().rootFrame().childFrames()[n]
    c = ed._edit.textCursor()
    c.setPosition(frame.firstPosition() + 1)
    ed._edit.setTextCursor(c)


def _picture(tmp_path):
    from PySide6.QtGui import QColor, QImage
    img = QImage(40, 30, QImage.Format_RGB32)
    img.fill(QColor("red"))
    path = tmp_path / "p.png"
    img.save(str(path))
    return str(path)


def test_table_rows_columns_style_and_delete(tmp_path):
    ed = _editor(tmp_path, Paragraph(children=[Text("x")]),
                 Table(rows=[["a", "b"], ["1", "2"]], caption="T"),
                 Paragraph(children=[Text("y")]))
    _caret_in_frame(ed, 0)
    assert ed.context_object() == "table"
    ed.set_table_style("booktabs")
    ed.table_insert_row(below=True)
    ed.table_insert_column(right=True)
    t = next(b for b in ed.get_document().children if isinstance(b, Table))
    assert t.style == "booktabs"
    assert len(t.rows) == 3 and len(t.rows[0]) == 3
    assert t.caption == "T"
    _caret_in_frame(ed, 0)
    ed.table_delete_row()
    t = next(b for b in ed.get_document().children if isinstance(b, Table))
    assert len(t.rows) == 2
    _caret_in_frame(ed, 0)
    ed.delete_current_table()
    assert not any(isinstance(b, Table) for b in ed.get_document().children)


def test_picture_align_buttons_and_width(tmp_path):
    ed = _editor(tmp_path, Paragraph(children=[Text("x")]),
                 Figure(path=_picture(tmp_path), caption="F"))
    _caret_in_frame(ed, 0)
    assert ed.context_object() == "figure"
    ed.apply_alignment("right")          # Home's align button
    ed.set_figure_width(0.25)
    fig = next(b for b in ed.get_document().children if isinstance(b, Figure))
    assert fig.align == "right" and fig.width == "0.25\\textwidth"
    assert ed.current_alignment() == "right"
    ed.delete_current_figure()
    assert not any(isinstance(b, Figure) for b in ed.get_document().children)


def test_equation_numbering_and_delete(tmp_path):
    ed = _editor(tmp_path, MathBlock("a=b"), Paragraph(children=[Text("z")]))
    c = ed._edit.textCursor()
    c.setPosition(ed._edit.document().begin().position())
    ed._edit.setTextCursor(c)
    assert ed.context_object() == "equation"
    ed.set_current_equation_numbered(True)
    m = next(b for b in ed.get_document().children if isinstance(b, MathBlock))
    assert m.numbered
    ed.delete_current_equation()
    assert not any(isinstance(b, MathBlock)
                   for b in ed.get_document().children)


def test_table_caption_label_and_column_alignment(tmp_path):
    ed = _editor(tmp_path, Paragraph(children=[Text("x")]),
                 Table(rows=[["a", "b"], ["1", "2"]], alignment="|l|p{3cm}|"),
                 Paragraph(children=[Text("y")]))
    _caret_in_frame(ed, 0)
    ed.set_caption("Results", "tab:res")
    _caret_in_frame(ed, 0)
    assert ed.current_caption() == ("Results", "tab:res")
    ed.set_column_alignment("r")
    t = next(b for b in ed.get_document().children if isinstance(b, Table))
    assert t.caption == "Results" and t.label == "tab:res"
    assert t.alignment == "|r|p{3cm}|"
    assert len(t.rows) == 2


def test_picture_caption(tmp_path):
    ed = _editor(tmp_path, Paragraph(children=[Text("x")]),
                 Figure(path=_picture(tmp_path), align="right"))
    _caret_in_frame(ed, 0)
    ed.set_caption("A red square", "fig:sq")
    fig = next(b for b in ed.get_document().children if isinstance(b, Figure))
    assert (fig.caption, fig.label, fig.align) == ("A red square", "fig:sq",
                                                   "right")
