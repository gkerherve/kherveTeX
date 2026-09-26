"""Math layout engine, the equation canvas widget and the reworked
equation dialog (offscreen)."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc import mathbox as mb, mathlayout as ml  # noqa: E402
from khervedoc.equation_editor import EquationEditorDialog  # noqa: E402
from khervedoc.math_widget import MathEditWidget  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def lay(latex, display=True):
    return ml.Layout(32, display).layout(mb.parse_latex(latex))


# ----------------------------------------------------------------- layout

def test_fraction_is_taller_than_a_letter(qapp):
    x = lay("x")
    f = lay(r"\frac{x}{y}")
    assert f.asc > x.asc * 1.5
    assert f.desc > x.desc + 5


def test_scripts_are_smaller_and_raised(qapp):
    b = lay("x^2")
    base, scripts = b.kids[0][2], b.kids[1][2]
    sup_dx, sup_dy, sup = scripts.kids[0]
    assert sup_dy < 0                         # raised
    assert sup.em == pytest.approx(base.em * 0.7)


def test_display_limits_go_above_and_below(qapp):
    disp = lay(r"\sum_{i=1}^{n} i", display=True)
    inline = lay(r"\sum_{i=1}^{n} i", display=False)
    assert disp.asc + disp.desc > inline.asc + inline.desc


def test_delimiters_grow_with_content(qapp):
    small = lay(r"\left( x \right)")
    tall = lay(r"\left( \frac{\frac{a}{b}}{c} \right)")
    assert tall.asc + tall.desc > (small.asc + small.desc) * 1.8


def test_matrix_grid_is_wider_than_one_cell(qapp):
    m = lay(r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}")
    assert m.w > lay("ab").w
    assert m.asc + m.desc > lay("a").asc * 2.5


def test_row_geometry_has_a_gap_per_caret_position(qapp):
    row = mb.parse_latex("a+b")
    box = ml.Layout(32).layout(row)
    geo = ml.collect_rows(box)
    g = geo[id(row)]
    assert len(g.gaps) == 4
    assert g.gaps == sorted(g.gaps)


def test_render_image_is_not_blank(qapp):
    img = ml.render_image(mb.parse_latex(r"\sqrt{x^2+1}"), 24)
    assert img.width() > 20 and img.height() > 20
    inked = sum(img.pixelColor(x, y).alpha() > 0
                for x in range(0, img.width(), 2)
                for y in range(0, img.height(), 2))
    assert inked > 20


# ----------------------------------------------------------------- widget

@pytest.fixture
def w(qapp):
    widget = MathEditWidget()
    widget.resize(500, 200)
    widget.show()
    widget.setFocus()
    yield widget
    widget.close()


def test_widget_typing_builds_structure(w):
    QTest.keyClicks(w, "x^2")
    QTest.keyClick(w, Qt.Key_Right)
    QTest.keyClicks(w, "+1/y")
    assert w.latex() == r"x^2 + \frac{1}{y}"


def test_widget_tab_and_backspace(w):
    w.insert_latex(r"\frac{\square}{\square}")
    QTest.keyClicks(w, "a")
    QTest.keyClick(w, Qt.Key_Tab)
    QTest.keyClicks(w, "b")
    assert w.latex() == r"\frac{a}{b}"
    QTest.keyClick(w, Qt.Key_Backspace)
    QTest.keyClick(w, Qt.Key_Backspace)     # unwrap at slot start
    assert w.latex() == "a"


def test_widget_undo_shortcut(w):
    QTest.keyClicks(w, "ab")
    QTest.keyClick(w, Qt.Key_Z, Qt.ControlModifier)
    assert w.latex() == "a"


def test_widget_completion_popup(w):
    QTest.keyClicks(w, "\\alph")
    assert w._completer is not None and w._completer.isVisible()
    QTest.keyClick(w, Qt.Key_Return)
    assert w.latex() == r"\alpha"
    assert not w._completer.isVisible()


def test_widget_copy_paste_as_latex(w):
    QTest.keyClicks(w, "a/b")
    QTest.keyClick(w, Qt.Key_A, Qt.ControlModifier)
    QTest.keyClick(w, Qt.Key_C, Qt.ControlModifier)
    assert QGuiApplication.clipboard().text() == r"\frac{a}{b}"
    QTest.keyClick(w, Qt.Key_Right)
    QTest.keyClicks(w, "=")
    QTest.keyClick(w, Qt.Key_V, Qt.ControlModifier)
    assert w.latex() == r"\frac{a}{b} = \frac{a}{b}"


def test_widget_click_places_caret_in_denominator(w):
    w.set_latex(r"\frac{a}{b}")
    w._relayout()
    frac = w.editor.root.children[0]
    g = w._rows[id(frac.den)]
    w.editor.set_cursor(w.editor.root, 0)
    QTest.mouseClick(w, Qt.LeftButton, pos=QPointF(
        g.gaps[-1], g.y).toPoint())
    assert w.editor.row is frac.den


def test_widget_zoom(w):
    px = w.font_px()
    QTest.keyClick(w, Qt.Key_Equal, Qt.ControlModifier)
    assert w.font_px() > px
    QTest.keyClick(w, Qt.Key_0, Qt.ControlModifier)
    assert w.font_px() == px


# ----------------------------------------------------------------- dialog

def test_dialog_api_round_trip_unchanged(qapp):
    src = r"E = mc^{2}"
    d = EquationEditorDialog(initial_latex=src)
    try:
        # untouched re-edit gives back exactly what came in
        assert d.latex() == src
        assert d._display_cb.isHidden()
    finally:
        d.close()


def test_dialog_structural_reedit(qapp):
    d = EquationEditorDialog(initial_latex=r"\frac{a}{b}")
    try:
        assert isinstance(d._math.editor.root.children[0], mb.Frac)
        d._math.editor.set_cursor(d._math.editor.root, 1)
        QTest.keyClicks(d._math, "+c")
        assert d.latex() == r"\frac{a}{b} + c"
    finally:
        d.close()


def test_dialog_new_equation_defaults(qapp):
    d = EquationEditorDialog()
    try:
        assert d.is_display() is True
        assert d.latex() == ""
        assert d._source_panel.isHidden()
        d._latex_toggle.setChecked(True)
        assert not d._source_panel.isHidden()
    finally:
        d.close()


def test_dialog_template_wraps_selection(qapp):
    d = EquationEditorDialog()
    try:
        QTest.keyClicks(d._math, "x")
        d._math.editor.select_all()
        d._insert_template(r"\sqrt{\square}")
        assert d.latex() == r"\sqrt{x}"
    finally:
        d.close()


def test_dialog_source_edit_updates_tree(qapp):
    d = EquationEditorDialog()
    try:
        d._edit.setPlainText(r"\sqrt{\square} + 1")
        assert isinstance(d._math.editor.root.children[0], mb.Sqrt)
        assert d._ph_hint.text().startswith("1 empty slot")
        QTest.keyClicks(d._math, "y")
        assert d._edit.toPlainText() == r"\sqrt{\square} + 1y"
        assert d.latex() == r"\sqrt{} + 1y"
    finally:
        d.close()


def test_dialog_insert_multiline_environment(qapp):
    d = EquationEditorDialog()
    try:
        d._insert_template(
            r"\begin{cases}\n\square & \text{if } \square \\\\\n"
            r"\square & \text{otherwise}\n\end{cases}")
        m = d._math.editor.root.children[0]
        assert isinstance(m, mb.Matrix) and m.env == "cases"
        assert len(m.rows) == 2
    finally:
        d.close()
