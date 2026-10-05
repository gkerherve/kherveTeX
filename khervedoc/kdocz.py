"""Single-file `.ktex` container — a ZIP holding the document JSON plus
every image the document references. `.ktexz` / `.kdocz` are the same
container under its older names and still open.

Layout inside the archive:

    manifest.json   - schema version + producing app
    document.json   - the KherveTeX document model, image paths rewritten
                      to point at the bundled files ("figures/figure_001.png")
    document.tex    - the generated LaTeX, for readers without KherveTeX
    project.json    - only in a project's main document: the list and
                      order of the project's other .ktex files
    kherveref.bib   - the cited entries of a document whose citations
                      come from a KherveRef library
    figures/        - the bundled image files referenced by Figure nodes
                      (older archives used images/; paths in document.json
                      say which)

Saving: copies every Figure-referenced file into the archive and rewrites
the in-archive document's paths to those bundled locations, so reopening
the file on another machine still finds the images.

Loading: extracts the archive into a directory (a temp dir by default)
and rewrites the Figure paths to absolute paths under that directory, so
the LaTeX compiler can pick them up via the existing \\includegraphics
machinery.
"""
from __future__ import annotations

import json
import tempfile
import zipfile
from dataclasses import replace
from pathlib import Path

from .model import Document, Figure, from_json, to_json


SCHEMA_VERSION = 1
MANIFEST_BASENAME = "manifest.json"
DOC_BASENAME = "document.json"
TEX_BASENAME = "document.tex"
PROJECT_BASENAME = "project.json"
IMAGES_DIR = "figures"
EQUATIONS_DIR = "equations"
NATIVE_SUFFIX = ".ktex"
BIB_BASENAME = "kherveref.bib"


def is_kdocz_path(path: Path | str) -> bool:
    s = str(path).lower()
    return s.endswith((".ktex", ".kdocz", ".ktexz"))


def is_legacy_bundle(path: Path | str) -> bool:
    """A bundle under a pre-.ktex name; saving converts it to .ktex."""
    return str(path).lower().endswith((".kdocz", ".ktexz"))


_FIGURE_SIBLINGS = {"drawing": (".svg", ".pdf"),
                    "flowchart": (".pdf", ".flow.json", ".tikz")}


def _bundle_figures(doc: Document, base_dir: Path
                    ) -> tuple[Document, list[tuple[Path, str]]]:
    """A copy of *doc* whose Figure paths point at figures/…, plus the
    (source file, archive name) pairs to store. Figures whose file is
    missing keep their path so the user can re-link them later."""
    base_dir = Path(base_dir)
    rewritten_children: list = []
    images_to_bundle: list[tuple[Path, str]] = []  # (source, arcname)
    by_source: dict[str, str] = {}                 # de-dupe identical paths
    counter = 1

    for block in doc.children:
        if isinstance(block, Figure) and block.path:
            src = block.path
            if src in by_source:
                arc_name = by_source[src]
            else:
                src_path = Path(src)
                # Fall back to looking next to the saved .kdocz for relative
                # references — this is the common case for .docx-imported
                # documents that haven't been saved yet.
                if not src_path.is_absolute() and not src_path.exists():
                    candidate = base_dir / src
                    if candidate.exists():
                        src_path = candidate
                if src_path.exists():
                    ext = src_path.suffix or ".png"
                    arc_name = f"{IMAGES_DIR}/figure_{counter:03d}{ext}"
                    counter += 1
                    images_to_bundle.append((src_path, arc_name))
                    sib_exts = _FIGURE_SIBLINGS.get(block.source, ())
                    if sib_exts:
                        # The editable source and the PDF LaTeX includes
                        # live beside the PNG preview; keep them paired by
                        # stem.
                        for sib_ext in sib_exts:
                            sib = src_path.with_suffix(sib_ext)
                            if sib.exists():
                                images_to_bundle.append(
                                    (sib, arc_name[:-len(ext)] + sib_ext))
                    by_source[src] = arc_name
                else:
                    arc_name = src
                    by_source[src] = arc_name
            rewritten_children.append(replace(block, path=arc_name))
        else:
            rewritten_children.append(block)

    return (Document(meta=doc.meta, children=rewritten_children),
            images_to_bundle)


def save_kdocz(doc: Document, out_path: Path, bib_text: str = "") -> None:
    """Write `doc` and all its referenced images to `out_path`, with the
    generated LaTeX alongside so the archive is readable on its own.
    `bib_text` (the cited KherveRef entries) is bundled as kherveref.bib
    so the document compiles on machines without the library."""
    from .serializer import serialize_document
    out_path = Path(out_path)
    archive_doc, images = _bundle_figures(doc, out_path.parent)
    # A project's main document carries the project; saving its text
    # must not drop it.
    project = read_project_json(out_path)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if project is not None:
            zf.writestr(PROJECT_BASENAME, project)
        zf.writestr(MANIFEST_BASENAME, json.dumps(
            {"format": "ktex", "schema_version": SCHEMA_VERSION,
             "app": "KherveTeX"},
            indent=2))
        zf.writestr(DOC_BASENAME, to_json(archive_doc))
        zf.writestr(TEX_BASENAME, serialize_document(archive_doc))
        for src_path, arc_name in images:
            zf.write(src_path, arcname=arc_name)
        if bib_text:
            zf.writestr(BIB_BASENAME, bib_text)


def read_project_json(path: Path) -> str | None:
    """The project.json text stored in a .ktex, or None."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            if PROJECT_BASENAME in zf.namelist():
                return zf.read(PROJECT_BASENAME).decode("utf-8")
    except (OSError, zipfile.BadZipFile):
        pass
    return None


def write_project_json(path: Path, project_json: str) -> None:
    """Store *project_json* in the .ktex at *path*, keeping every other
    entry. Zip entries can't be replaced in place, so the archive is
    rewritten through a temp file."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(path, "r") as src, \
            zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            if item.filename != PROJECT_BASENAME:
                dst.writestr(item, src.read(item.filename))
        dst.writestr(PROJECT_BASENAME, project_json)
    tmp.replace(path)


def export_latex_zip(doc: Document, out_path: Path, base_dir: Path,
                     main_name: str = "main") -> None:
    """A ready-to-compile LaTeX package (Overleaf, journal upload):
    main.tex, figures/ and equations/ — one .tex per display equation, so
    they can be reused or submitted separately."""
    from .model import MathBlock
    from .serializer import serialize_document
    tex_doc, images = _bundle_figures(doc, base_dir)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{main_name}.tex", serialize_document(tex_doc))
        for src_path, arc_name in images:
            zf.write(src_path, arcname=arc_name)
        n = 0
        for block in doc.children:
            if isinstance(block, MathBlock) and block.latex.strip():
                n += 1
                env = "equation" if block.numbered else "equation*"
                label = f"\\label{{{block.label}}}\n" if block.label else ""
                zf.writestr(f"{EQUATIONS_DIR}/eq_{n:03d}.tex",
                            f"\\begin{{{env}}}\n{label}{block.latex.strip()}"
                            f"\n\\end{{{env}}}\n")


def load_kdocz(path: Path, extract_to: Path | None = None) -> tuple[Document, Path]:
    """Open a `.kdocz` archive.

    `extract_to` controls where the bundled files are unpacked; pass a
    persistent directory (e.g. next to the .kdocz) if you want the unpacked
    images to survive across runs. The default is a fresh temp dir per call.

    Returns `(document, extract_dir)`. Figure paths in the returned document
    are absolute paths under `extract_dir`, so the LaTeX compiler will find
    every image without any further setup.
    """
    if extract_to is None:
        extract_to = Path(tempfile.mkdtemp(prefix="kdocz-"))
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(path, "r") as zf:
        # Read the manifest if present (currently we only validate the
        # schema_version, but this is also where we'll branch on future
        # format revisions).
        if MANIFEST_BASENAME in zf.namelist():
            manifest = json.loads(zf.read(MANIFEST_BASENAME))
            if manifest.get("schema_version", 0) > SCHEMA_VERSION:
                raise ValueError(
                    f"{path.name} was produced by a newer KherveTeX "
                    f"(schema {manifest['schema_version']} > {SCHEMA_VERSION}).")
        zf.extractall(extract_to)

    doc_json = (extract_to / DOC_BASENAME).read_text(encoding="utf-8")
    doc = from_json(doc_json)

    # Rewrite Figure paths so they point at the just-extracted files. Forward
    # slashes keep LaTeX happy on Windows; absolute paths sidestep CWD issues
    # when tectonic runs in its own build directory.
    for block in doc.children:
        if isinstance(block, Figure) and block.path:
            candidate = extract_to / block.path
            if candidate.exists():
                block.path = str(candidate.resolve()).replace("\\", "/")

    return doc, extract_to


def read_bundled_bib(path: Path) -> str:
    """The kherveref.bib bundled in a .ktex, or ""."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            if BIB_BASENAME in zf.namelist():
                return zf.read(BIB_BASENAME).decode("utf-8", errors="replace")
    except (OSError, zipfile.BadZipFile):
        pass
    return ""
