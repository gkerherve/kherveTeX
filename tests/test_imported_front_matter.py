"""A Word or PDF import keeps its title page: the \\date{} it sets (no date
to print) is not taken for a Wiley author block."""
from khervedoc.model import Abstract, Author, Document, DocMeta, Paragraph, Text, Title
from khervedoc.serializer import serialize_document


def _imported(cls="article"):
    meta = DocMeta(documentclass=cls, title="Damped Oscillations", author="A. Morgan")
    meta.frontmatter_extras = "\\date{}"
    return Document(meta=meta, children=[
        Title(children=[Text(text="Damped Oscillations")]),
        Author(children=[Text(text="A. Morgan")]),
        Abstract(children=[Text(text="We measure the decay.")]),
        Paragraph(children=[Text(text="Body text.")]),
    ])


def test_abstract_follows_maketitle_as_an_environment():
    tex = serialize_document(_imported())
    body = tex.split("\\begin{document}", 1)[1]
    assert "\\abstract{" not in body
    assert body.index("\\date{}") < body.index("\\maketitle") < body.index("\\begin{abstract}")
    assert "\\begin{abstract}\nWe measure the decay.\n\\end{abstract}" in body


def test_wiley_front_matter_still_goes_before_maketitle():
    doc = _imported()
    doc.meta.frontmatter_extras = "\\author[1]{A. Morgan}\n\\date{}"
    body = serialize_document(doc).split("\\begin{document}", 1)[1]
    assert body.index("\\abstract{We measure the decay.}") < body.index("\\maketitle")
