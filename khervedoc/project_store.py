"""Where a document's files live on disk.

A folder holds only the user's .ktex files (and exported PDFs). Every
working file — generated .tex, equation previews, pasted figures,
unpacked project documents — goes in a hidden `.kherve/` folder beside
them, which Git still tracks so history stays readable.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import kdocz
from .model import Document, Project, from_json, project_from_json, to_json

WORK_DIR = ".kherve"


def work_dir(folder: Path) -> Path:
    d = Path(folder) / WORK_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def doc_stem(path: Path) -> str:
    name = Path(path).name
    for ext in (".kdocproj.json", ".ktex.json", ".kdoc.json"):
        if name.endswith(ext):
            return name[:-len(ext)]
    return Path(path).stem


# A folder a cloud service keeps in sync (OneDrive, iCloud Drive, Dropbox,
# Google Drive).
_SYNCED_RE = re.compile(
    r"[\\/]Library[\\/](?:CloudStorage|Mobile Documents)[\\/]"
    r"|[\\/](?:OneDrive|Dropbox|Google Drive|iCloud Drive)[^\\/]*[\\/]", re.I)


def is_synced_folder(folder: Path) -> bool:
    return bool(_SYNCED_RE.search(str(folder) + "/"))


def _fnv(s: str) -> str:
    h = 0x811C9DC5
    for ch in s:
        h = ((h ^ ord(ch)) * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def files_dir(folder: Path, stem: str) -> Path:
    """Where a document's figures unpack: under .kherve/, or for a folder a
    cloud service syncs, in a local folder of the project's own. There the
    service uploaded every unpacked picture again, and while it did reading
    one timed out: the compile stopped ("Operation timed out")."""
    if is_synced_folder(folder):
        import tempfile
        d = Path(tempfile.gettempdir()) / "khervetex-files" / _fnv(str(folder)) / stem
        d.mkdir(parents=True, exist_ok=True)
        return d
    return work_dir(folder) / "files" / stem


def read_doc(path: Path) -> Document:
    """Load a project document; .ktex figures unpack under .kherve/ (or
    files_dir's local folder)."""
    path = Path(path)
    if kdocz.is_kdocz_path(path):
        doc, _ = kdocz.load_kdocz(path, files_dir(path.parent, doc_stem(path)))
        return doc
    return from_json(path.read_text(encoding="utf-8"))


def write_doc(doc: Document, path: Path) -> None:
    path = Path(path)
    if kdocz.is_kdocz_path(path):
        kdocz.save_kdocz(doc, path)
    else:
        path.write_text(to_json(doc), encoding="utf-8")


def read_project(path: Path) -> Project | None:
    """The project in a main .ktex (or a legacy .kdocproj.json)."""
    path = Path(path)
    if path.name.lower().endswith(".kdocproj.json"):
        return project_from_json(path.read_text(encoding="utf-8"))
    text = kdocz.read_project_json(path) if kdocz.is_kdocz_path(path) \
        else None
    return project_from_json(text) if text else None


def unique_path(folder: Path, stem: str, suffix: str = ".ktex") -> Path:
    dest = Path(folder) / f"{stem}{suffix}"
    n = 1
    while dest.exists():
        dest = Path(folder) / f"{stem}_{n}{suffix}"
        n += 1
    return dest
