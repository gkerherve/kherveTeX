"""Work on a document with collaborators on Overleaf.

Overleaf keeps every project in a git repository (https://git.overleaf.com/
<project id>), reachable with the user name "git" and a Git authentication
token from Overleaf's account settings. Sending writes the document as
LaTeX (main .tex, figures, bibliography) into a local clone of that
repository and pushes it; getting pulls what collaborators changed and reads
the .tex back into a document.

Overleaf's git access needs a plan that includes it. On a free plan the same
files go up as a zip through Overleaf's "Upload project" (File > Share >
Download for Overleaf).
"""
from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from .model import Document

GIT_HOST = "https://git.overleaf.com/"
BRANCH = "master"
_ID_RE = re.compile(r"\b([0-9a-f]{24})\b")


class OverleafError(Exception):
    """A message for the user: what went wrong and what to do about it."""


def git_url(link: str) -> str:
    """The project's git address from whatever the user pasted: the
    browser link (overleaf.com/project/<id>), the git link, or the bare id.
    Anything else is taken as a git address as it is (a test server)."""
    link = (link or "").strip()
    if not link:
        raise OverleafError("Paste the link of your Overleaf project.")
    m = _ID_RE.search(link)
    if m and ("overleaf.com" in link or link == m.group(1)):
        return GIT_HOST + m.group(1)
    if "://" in link or link.startswith("/"):
        return link
    raise OverleafError(
        "That does not look like an Overleaf project link. Open the project "
        "on overleaf.com and copy the address from the browser.")


def _callbacks(token: str):
    import pygit2
    if not token:
        return None
    return pygit2.RemoteCallbacks(
        credentials=pygit2.UserPass("git", token))


def _explain(exc: Exception) -> OverleafError:
    text = str(exc)
    if re.search(r"401|403|auth|credential", text, re.I):
        return OverleafError(
            "Overleaf did not accept the token. Create a Git authentication "
            "token in Overleaf (Account Settings > Git Integration) and paste "
            "it again. Git access needs an Overleaf plan that includes it; "
            "on a free plan use Download for Overleaf instead.")
    if re.search(r"404|not found|does not appear", text, re.I):
        return OverleafError(
            "Overleaf could not find that project. Check the link, and that "
            "your account can open the project.")
    return OverleafError(f"Overleaf: {text}")


def _clone(url: str, token: str, into: Path):
    import pygit2
    if (into / ".git").exists():
        repo = pygit2.Repository(str(into))
        if repo.remotes["origin"].url == url:
            repo.remotes["origin"].fetch(callbacks=_callbacks(token))
            remote = repo.lookup_reference(f"refs/remotes/origin/{BRANCH}")
            repo.checkout_tree(repo.get(remote.target),
                               strategy=pygit2.GIT_CHECKOUT_FORCE)
            repo.set_head(remote.target)
            return repo
        shutil.rmtree(into)
    into.parent.mkdir(parents=True, exist_ok=True)
    return pygit2.clone_repository(url, str(into), callbacks=_callbacks(token),
                                   checkout_branch=BRANCH)


def main_tex(folder: Path) -> Path | None:
    """The project's main file: the root .tex that starts a document,
    preferring main.tex as Overleaf does."""
    if (folder / "main.tex").exists():
        return folder / "main.tex"
    for path in sorted(folder.glob("*.tex")):
        if "\\documentclass" in path.read_text(errors="ignore"):
            return path
    return None


def write_project(doc: Document, base_dir: Path, folder: Path,
                  main_name: str = "main",
                  extra_files: dict[str, str] | None = None) -> Path:
    """Write *doc* as an Overleaf project into *folder*: the same files as
    the LaTeX package export, plus any extra files (the bibliography)."""
    from .kdocz import export_latex_zip
    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / "project.zip"
        export_latex_zip(doc, bundle, base_dir, main_name=main_name)
        with zipfile.ZipFile(bundle) as zf:
            zf.extractall(folder)
    for name, text in (extra_files or {}).items():
        (folder / name).write_text(text, encoding="utf-8")
    return folder / f"{main_name}.tex"


def send(doc: Document, base_dir: Path, link: str, token: str,
         cache_dir: Path, extra_files: dict[str, str] | None = None,
         message: str = "Update from KherveTeX") -> str:
    """Push *doc* to the Overleaf project. Returns a line for the status bar."""
    import pygit2
    url = git_url(link)
    try:
        repo = _clone(url, token, cache_dir)
    except Exception as exc:
        raise _explain(exc) from exc
    folder = Path(repo.workdir)
    existing = main_tex(folder)
    main_name = existing.stem if existing else "main"
    write_project(doc, base_dir, folder, main_name, extra_files)
    repo.index.add_all()
    repo.index.write()
    tree = repo.index.write_tree()
    if not repo.head_is_unborn and repo.head.peel().tree.id == tree:
        return "Overleaf already has this version."
    from .git_backend import _signature
    sig = _signature(repo)
    parents = [] if repo.head_is_unborn else [repo.head.target]
    repo.create_commit(f"refs/heads/{BRANCH}", sig, sig, message, tree,
                       parents)
    try:
        repo.remotes["origin"].push([f"refs/heads/{BRANCH}"],
                                    callbacks=_callbacks(token))
    except Exception as exc:
        raise _explain(exc) from exc
    return f"Sent to Overleaf ({main_name}.tex)."


def receive(link: str, token: str, cache_dir: Path) -> tuple[Document, Path]:
    """The project as Overleaf has it now, read back into a document, with
    the folder its figures are in."""
    from .importers import import_tex
    url = git_url(link)
    try:
        repo = _clone(url, token, cache_dir)
    except Exception as exc:
        raise _explain(exc) from exc
    folder = Path(repo.workdir)
    main = main_tex(folder)
    if main is None:
        raise OverleafError("The Overleaf project has no main .tex file yet.")
    return import_tex(main.read_text(encoding="utf-8", errors="replace"),
                      base_dir=folder), folder
