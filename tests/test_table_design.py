"""Word's table tools: merged cells, header row (repeated), shading,
style gallery and sorting — model, LaTeX, import, Typst, Word, editor."""
import os

import pytest

from khervedoc.importers import import_tex
from khervedoc.model import Document, Paragraph, Table, Text, from_json, to_json
from khervedoc.serializer import serialize_document
from khervedoc.typst_serializer import serialize_document as typst


def _table(**kw):
    base = dict(rows=[["Name", "A", "B"], ["x", "1", ""], ["y", "2", "3"],
                      ["", "4", "5"]],
                caption="T", label="tab:t", alignment="lcr",
                merges=[[1, 1, 1, 2], [2, 0, 2, 1]], header=True,
                shading={"1,1": "#ffeb3b"})
    base.update(kw)
    return Table(**base)


def _tex(t):
    return serialize_document(Document(children=[
        Paragraph(children=[Text("x")]), t]))


def test_latex_merges_header_shading():
    tex = _tex(_table())
    assert r"\textbf{Name} & \textbf{A} & \textbf{B}" in tex
    assert r"\multicolumn{2}{c}{\cellcolor[HTML]{FFEB3B}1}" in tex
    assert r"\multirow{2}{*}{y}" in tex
    for pkg in ("multirow", "colortbl", "xcolor"):
        assert f"\\usepackage{{{pkg}}}" in tex


def test_grid_rules_skip_a_vertically_merged_cell():
    tex = _tex(_table(style="grid", alignment="|l|c|r|"))
    assert r"\multirow{2}{*}{y} & 2 & 3 \\ \cline{2-3}" in tex


def test_repeat_header_makes_longtable():
    tex = _tex(_table(repeat_header=True, style="striped"))
    assert "\\begin{longtable}{lcr}" in tex and "\\endhead" in tex
    assert "\\usepackage{longtable}" in tex
    assert r"\rowcolor[HTML]{EEF3FA}" in tex


@pytest.mark.parametrize("style", ["", "grid", "plain", "booktabs",
                                   "striped"])
@pytest.mark.parametrize("repeat", [False, True])
def test_latex_round_trip(style, repeat):
    t = _table(style=style, repeat_header=repeat,
               alignment="|l|c|r|" if style == "grid" else "lcr")
    back = [b for b in import_tex(_tex(t)).children if isinstance(b, Table)]
    assert back == [t]


def test_json_round_trip_and_defaults():
    t = _table(repeat_header=True)
    assert from_json(to_json(Document(children=[t]))).children[0] == t
    legacy = from_json('{"type": "Document", "children": [{"type": "Table",'
                       ' "rows": [["a"]]}]}').children[0]
    assert (legacy.merges, legacy.header, legacy.shading) == ([], False, {})


def test_typst_cells():
    out = typst(Document(children=[_table(repeat_header=True)]))
    assert "table.header([*Name*], [*A*], [*B*])" in out
    assert 'table.cell(colspan: 2, fill: rgb("#ffeb3b"))[1]' in out
    assert "table.cell(rowspan: 2)[y]" in out


def test_word_export(tmp_path):
    docx = pytest.importorskip("docx")
    from khervedoc.docx_exporter import export_docx
    path = tmp_path / "t.docx"
    export_docx(Document(children=[_table(repeat_header=True)]), path)
    tb = docx.Document(str(path)).tables[0]
    assert tb.cell(1, 1)._tc is tb.cell(1, 2)._tc
    assert tb.cell(2, 0)._tc is tb.cell(3, 0)._tc
    assert "tblHeader" in tb.rows[0]._tr.xml
    assert "FFEB3B" in tb.cell(1, 1)._tc.xml


# ---------- editor ----------

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def ed(tmp_path):
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from khervedoc.editor import DocumentEditor
    e = DocumentEditor()
    e.set_document_dir(tmp_path)
    e.set_document(Document(children=[
        Paragraph(children=[Text("x")]),
        Table(rows=[["Sample", "Mass"], ["B", "2.5"], ["A", "10"],
                    ["C", "1"]], caption="M"),
        Paragraph(children=[Text("y")])]))
    return e


def _cells(e, r, c, r2=None, c2=None):
    from PySide6.QtGui import QTextCursor
    t = e._edit.document().rootFrame().childFrames()[0]
    cur = t.cellAt(r, c).firstCursorPosition()
    if r2 is not None:
        cur.setPosition(t.cellAt(r2, c2).firstCursorPosition().position(),
                        QTextCursor.KeepAnchor)
    e._edit.setTextCursor(cur)


def _model(e):
    return next(b for b in e.get_document().children
                if isinstance(b, Table))


def test_editor_header_sort_shading_style(ed):
    _cells(ed, 1, 1)
    ed.set_table_header(True)
    assert ed.sort_table() is None
    assert [r[1] for r in _model(ed).rows] == ["Mass", "1", "2.5", "10"]
    ed.sort_table(descending=True)
    assert [r[1] for r in _model(ed).rows] == ["Mass", "10", "2.5", "1"]
    _cells(ed, 2, 0)
    ed.set_cell_shading("#dce8f7")
    ed.set_table_style("grid")
    _cells(ed, 0, 0)
    ed.set_table_repeat_header(True)
    t = _model(ed)
    assert (t.header, t.repeat_header, t.style) == (True, True, "grid")
    assert t.shading == {"2,0": "#dce8f7"}
    _cells(ed, 2, 0)
    ed.set_cell_shading(None)
    assert _model(ed).shading == {}


def test_editor_merge_and_split(ed):
    _cells(ed, 1, 0, 2, 0)
    assert ed.table_merge_cells()
    t = _model(ed)
    assert t.merges == [[1, 0, 2, 1]] and t.rows[1][0] == "B A"
    assert t.rows[2][0] == ""
    assert ed.sort_table() is not None         # refused while merged
    _cells(ed, 1, 0)
    ed.table_split_cell()
    assert _model(ed).merges == []
