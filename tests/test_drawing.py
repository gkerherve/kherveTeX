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
    assert {"images/figure_001.png", "images/figure_001.svg",
            "images/figure_001.pdf"} <= set(names)

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
    assert "images/figure_001.pdf" not in names
