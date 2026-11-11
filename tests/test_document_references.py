"""References ▸ Manage references: the document's own .bib, kept in the
.ktex, searched, edited, imported into and cited from, with the cited
keys it lacks listed as missing."""

import os

import pytest

from khervedoc import doc_references as dr
from khervedoc import kherveref_link as kr
from khervedoc.model import Citation, DocMeta, Document, Paragraph, Text

BIB = """@article{smith2020decay,
  author = {Smith, John and Doe, Anne},
  title  = {Radioactive {Decay} Revisited},
  journal = {Phys. Rev.},
  year   = {2020},
  pages  = "1--10",
  keywords = {nuclear}
}

@book{roe2018,
  author = {Roe, Bob},
  title = {Isotopes},
  year = 2018,
  publisher = {Wiley}
}
"""


def _doc(*keys, library=dr.DOCUMENT_LIBRARY):
    return Document(meta=DocMeta(ref_library=library), children=[Paragraph(children=[
        Text("See "), Citation(keys=list(keys)), Text(".")])])


def test_parse_entry_reads_every_field():
    etype, key, fields = dr.parse_entry(dr.entries(BIB)["smith2020decay"])
    assert (etype, key) == ("article", "smith2020decay")
    assert fields["title"] == "Radioactive {Decay} Revisited"
    assert fields["pages"] == "1--10"
    assert fields["keywords"] == "nuclear"
    assert dr.parse_entry(dr.entries(BIB)["roe2018"])[2]["year"] == "2018"


def test_format_entry_round_trips():
    etype, key, fields = dr.parse_entry(dr.entries(BIB)["smith2020decay"])
    again = dr.parse_entry(dr.format_entry(etype, key, fields))
    assert again == (etype, key, fields)


def test_suggest_key():
    assert dr.suggest_key("Müller, Jürgen", "2021", "The Half-life of Tritium",
                          set()) == "muller2021half"
    assert dr.suggest_key("Smith, John", "2020", "Decay", {"smith2020decay"}) \
        == "smith2020decaya"
    assert dr.suggest_key("", "", "", set()) == "ref"


def test_rows_show_cited_not_cited_and_missing():
    rows = dr.rows(BIB, ["roe2018", "ghost2001"])
    assert [(r["key"], r["status"]) for r in rows] == [
        ("smith2020decay", dr.NOT_CITED), ("roe2018", dr.CITED),
        ("ghost2001", dr.MISSING)]
    assert dr.matches(rows[0], "decay 2020")
    assert not dr.matches(rows[0], "decay 2019")


def test_merge_set_and_remove():
    text, added = dr.merge("", BIB)
    assert added == ["smith2020decay", "roe2018"]
    text, added = dr.merge(text, BIB)
    assert added == []
    new = dr.format_entry("misc", "roe2018b", {"title": "Notes"})
    text = dr.set_entry(text, "roe2018", new)
    assert list(dr.entries(text)) == ["smith2020decay", "roe2018b"]
    text = dr.remove_entry(text, "smith2020decay")
    assert list(dr.entries(text)) == ["roe2018b"]
    assert dr.remove_entry(text, "roe2018b") == ""


def test_own_list_is_kept_whole():
    # Uncited entries stay: the list is the document's, not a copy of the
    # cited part of a library.
    text, missing = kr.bibliography_for(_doc("roe2018", "ghost2001"), BIB)
    assert text == BIB
    assert missing == ["ghost2001"]
    text, missing = kr.bibliography_for(_doc(), BIB)
    assert text == BIB and missing == []


def test_document_with_own_list_compiles_its_bibliography():
    from khervedoc.serializer import serialize_document
    tex = serialize_document(_doc("roe2018"))
    assert "\\bibliography{kherveref}" in tex


# ---- the dialog ----

@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    yield QApplication.instance() or QApplication([])


def _manager(qapp, text=BIB, cited=("roe2018", "ghost2001")):
    from khervedoc.reference_manager import ReferenceManager
    return ReferenceManager(text, list(cited), dr.DOCUMENT_LIBRARY)


def _keys(m):
    return [r["key"] for r in m.rows()]


def test_search_and_filter(qapp):
    m = _manager(qapp)
    assert _keys(m) == ["smith2020decay", "roe2018", "ghost2001"]
    assert m._summary.text() == "2 references · 1 cited · 1 missing"
    m._search.setText("wiley")
    assert _keys(m) == []
    m._search.setText("isotopes")
    assert _keys(m) == ["roe2018"]
    m._search.clear()
    m._filter.setCurrentIndex(3)                # missing
    assert _keys(m) == ["ghost2001"]
    m._filter.setCurrentIndex(2)                # not cited
    assert _keys(m) == ["smith2020decay"]


def test_add_a_missing_reference(qapp):
    m = _manager(qapp)
    m.select("ghost2001")
    assert m._key.text() == "ghost2001"
    m.set_field("author", "Ghost, Casper")
    m.set_field("title", "Haunting")
    m.set_field("year", "2001")
    m.save_entry()
    assert "ghost2001" in dr.entries(m.text())
    assert m._summary.text() == "3 references · 2 cited"
    assert m.changed()


def test_new_entry_gets_a_key(qapp):
    m = _manager(qapp, "", ())
    m.new_entry()
    m.set_field("author", "Curie, Marie")
    m.set_field("title", "Radioactive substances")
    m.set_field("year", "1904")
    assert m.save_entry() == "curie1904radioactive"
    _t, _k, f = dr.parse_entry(dr.entries(m.text())["curie1904radioactive"])
    assert f["author"] == "Curie, Marie"


def test_edit_keeps_other_fields(qapp):
    m = _manager(qapp)
    m.select("smith2020decay")
    m.set_field("year", "2021")
    m.select("roe2018")                         # moving on keeps the edit
    _t, _k, f = dr.parse_entry(dr.entries(m.text())["smith2020decay"])
    assert f["year"] == "2021" and f["keywords"] == "nuclear"
    assert _keys(m)[1] == "roe2018"


def test_delete_import_and_cite(qapp):
    m = _manager(qapp)
    m.select("smith2020decay")
    m.delete_selected()
    assert list(dr.entries(m.text())) == ["roe2018"]
    assert m.add_bib(BIB) == ["smith2020decay"]
    m.select("roe2018")
    m.cite_selected()
    assert m.cite_keys() == ["roe2018"]


def test_window_keeps_the_list_in_the_document(qapp, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QDialog
    from khervedoc import reference_manager
    from khervedoc.mainwindow import MainWindow
    from khervedoc import kdocz
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)

    def fake_exec(self):
        self.add_bib(BIB)
        self.select("roe2018")
        self._cite = ["roe2018"]
        return QDialog.Accepted
    monkeypatch.setattr(reference_manager.ReferenceManager, "exec", fake_exec)
    w = MainWindow()
    try:
        w.act_manage_references.trigger()
        doc = w._editor.get_document()
        assert doc.meta.ref_library == dr.DOCUMENT_LIBRARY
        assert kr.cited_keys(doc) == ["roe2018"]
        path = tmp_path / "paper.ktex"
        w._current_path = path
        w._write_to(path)
        # Saved whole in the .ktex, the uncited entry too.
        assert "smith2020decay" in kdocz.read_bundled_bib(path)
    finally:
        w.close()
