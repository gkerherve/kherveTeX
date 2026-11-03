"""Sending to and getting from Overleaf, against a local git repository
standing in for git.overleaf.com."""
from pathlib import Path

import pytest

pygit2 = pytest.importorskip("pygit2")

from khervedoc import overleaf  # noqa: E402
from khervedoc.model import (  # noqa: E402
    DocMeta, Document, Paragraph, Section, Text, Title,
)


def _overleaf_project(tmp_path: Path) -> str:
    """A bare repository on branch master holding a main.tex, as Overleaf
    creates every project."""
    bare = tmp_path / "server.git"
    pygit2.init_repository(str(bare), bare=True, initial_head="master")
    seed = pygit2.clone_repository(str(bare), str(tmp_path / "seed"))
    (tmp_path / "seed" / "main.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}\n")
    seed.index.add_all()
    seed.index.write()
    sig = pygit2.Signature("Overleaf", "o@example.com")
    seed.create_commit("refs/heads/master", sig, sig, "Initial",
                       seed.index.write_tree(), [])
    seed.remotes["origin"].push(["refs/heads/master"])
    return str(bare)


def _doc(text: str) -> Document:
    return Document(meta=DocMeta(title="Shared"), children=[
        Title(children=[Text("Shared")]),
        Section(level=1, children=[Text("Intro")]),
        Paragraph(children=[Text(text)])])


@pytest.mark.parametrize("link,want", [
    ("https://www.overleaf.com/project/0123456789abcdef01234567",
     "https://git.overleaf.com/0123456789abcdef01234567"),
    ("https://git.overleaf.com/0123456789abcdef01234567",
     "https://git.overleaf.com/0123456789abcdef01234567"),
    ("0123456789abcdef01234567",
     "https://git.overleaf.com/0123456789abcdef01234567"),
])
def test_any_overleaf_link_becomes_its_git_address(link, want):
    assert overleaf.git_url(link) == want


@pytest.mark.parametrize("link", ["", "my project"])
def test_unusable_link_is_explained(link):
    with pytest.raises(overleaf.OverleafError):
        overleaf.git_url(link)


def test_send_writes_the_document_into_the_projects_main_file(tmp_path):
    server = _overleaf_project(tmp_path)
    msg = overleaf.send(_doc("Our first draft."), tmp_path, server, "",
                        tmp_path / "cache",
                        extra_files={"kherveref.bib": "@misc{k,title={T}}\n"})
    assert "main.tex" in msg
    check = pygit2.clone_repository(server, str(tmp_path / "check"))
    tex = (Path(check.workdir) / "main.tex").read_text()
    assert "Our first draft." in tex and "\\section{Intro}" in tex
    assert (Path(check.workdir) / "kherveref.bib").exists()
    # Nothing new to send the second time.
    again = overleaf.send(_doc("Our first draft."), tmp_path, server, "",
                          tmp_path / "cache")
    assert "already" in again


def test_receive_reads_a_collaborators_change(tmp_path):
    server = _overleaf_project(tmp_path)
    overleaf.send(_doc("Our first draft."), tmp_path, server, "",
                  tmp_path / "cache")
    # A collaborator edits the .tex on Overleaf.
    other = pygit2.clone_repository(server, str(tmp_path / "coauthor"))
    main = Path(other.workdir) / "main.tex"
    main.write_text(main.read_text().replace("Our first draft.",
                                             "Their better sentence."))
    other.index.add_all()
    other.index.write()
    sig = pygit2.Signature("Co Author", "c@example.com")
    other.create_commit("refs/heads/master", sig, sig, "Edit on Overleaf",
                        other.index.write_tree(), [other.head.target])
    other.remotes["origin"].push(["refs/heads/master"])

    doc, folder = overleaf.receive(server, "", tmp_path / "cache")
    text = " ".join(getattr(c, "text", "") for b in doc.children
                    for c in getattr(b, "children", []))
    assert "Their better sentence." in text
    assert folder == tmp_path / "cache"
