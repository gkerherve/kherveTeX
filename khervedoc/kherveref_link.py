"""Citations from KherveRef libraries.

KherveRef (the sibling reference manager) keeps each library as a folder
whose `library.bib` it regenerates in classic BibTeX after every change.
KherveTeX reads that file directly, so KherveRef need not be running.

A document that cites from a library records the library's folder in
`DocMeta.ref_library`. Its cited entries are written to `kherveref.bib`
— staged next to every compile and bundled inside the .ktex — so the
document still compiles on a machine without the library, from the
copy it carries.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .model import Citation, Document
from .references import _walk

BIB_NAME = "kherveref"           # \bibliography{kherveref}
BIB_FILE = f"{BIB_NAME}.bib"
LIBRARY_BIB = "library.bib"

_ENTRY_START_RE = re.compile(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,")


def _settings():
    from PySide6.QtCore import QSettings
    return QSettings("kherve", "KherveRef")


def is_library(path: Path | str) -> bool:
    return bool(path) and (Path(path) / LIBRARY_BIB).is_file()


def library_name(path: Path | str) -> str:
    try:
        data = json.loads((Path(path) / "library.json").read_text(encoding="utf-8"))
        return data.get("name") or Path(path).name
    except (OSError, ValueError):
        return Path(path).name


def known_libraries() -> list[Path]:
    """Libraries KherveRef has opened on this machine, most recent first."""
    try:
        s = _settings()
        recent = s.value("recent_libraries", []) or []
        last = s.value("last_library", "") or ""
    except Exception:
        return []
    if isinstance(recent, str):
        recent = [recent]
    out: list[Path] = []
    for p in [last, *recent]:
        if p and is_library(p) and Path(p) not in out:
            out.append(Path(p))
    return out


def split_bib(text: str) -> dict[str, str]:
    """key -> the entry's full source text, for every @entry in *text*
    (@string / @comment / @preamble are skipped)."""
    out: dict[str, str] = {}
    for m in _ENTRY_START_RE.finditer(text):
        if m.group(1).lower() in ("string", "comment", "preamble"):
            continue
        opener = text.index("{" if "{" in m.group(0) else "(", m.start())
        closer = "}" if text[opener] == "{" else ")"
        depth, i = 0, opener
        while i < len(text):
            ch = text[i]
            if ch == "\\":
                i += 2
                continue
            if ch == "{" or (closer == ")" and ch == "("):
                depth += 1
            elif ch == "}" or (closer == ")" and ch == ")"):
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out.setdefault(m.group(2), text[m.start():i + 1].strip())
    return out


_STRING_RE = re.compile(r"@string\s*[{(]", re.IGNORECASE)


def string_definitions(text: str) -> list[str]:
    """Every @string{...} block in *text*: cited entries may use them."""
    out = []
    for m in _STRING_RE.finditer(text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] in "{(":
                depth += 1
            elif text[i] in "})":
                depth -= 1
                if depth == 0:
                    out.append(text[m.start():i + 1])
                    break
            i += 1
    return out


def load_library(path: Path | str) -> dict[str, str]:
    try:
        return split_bib((Path(path) / LIBRARY_BIB).read_text(
            encoding="utf-8", errors="replace"))
    except OSError:
        return {}


def cited_keys(doc: Document) -> list[str]:
    """Every cited key, in order of first citation."""
    keys: list[str] = []
    for node in _walk(doc):
        if isinstance(node, Citation):
            for k in node.keys:
                if k and k not in keys:
                    keys.append(k)
    return keys


def build_bib(keys: list[str], sources: list[dict[str, str]],
              strings: list[str] = ()) -> tuple[str, list[str]]:
    """(.bib text with the entries for *keys*, keys found nowhere).
    Earlier sources win: the live library before the bundled copy.
    *strings* (@string definitions) go first, so macros resolve."""
    parts, missing = list(dict.fromkeys(strings)), []
    for k in keys:
        for src in sources:
            if k in src:
                parts.append(src[k])
                break
        else:
            missing.append(k)
    head = "% Cited entries, written by KherveTeX from KherveRef.\n\n"
    found = len(parts) > len(dict.fromkeys(strings))
    return (head + "\n\n".join(parts) + "\n") if found else "", missing


def bibliography_for(doc: Document, bundled: str = "",
                     extra_dirs: list[Path] = ()) -> tuple[str, list[str]]:
    """The kherveref.bib text for *doc* and the cited keys it lacks.

    Sources, in order: the document's own library (when present on this
    machine), the copy bundled in the .ktex, then any .bib files in
    *extra_dirs* (e.g. the document's folder)."""
    texts: list[str] = []
    if is_library(doc.meta.ref_library):
        try:
            texts.append((Path(doc.meta.ref_library) / LIBRARY_BIB).read_text(
                encoding="utf-8", errors="replace"))
        except OSError:
            pass
    if bundled:
        texts.append(bundled)
    for d in extra_dirs:
        for f in sorted(Path(d).glob("*.bib")):
            if f.name != BIB_FILE:
                try:
                    texts.append(f.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    keys = cited_keys(doc)
    if not keys:
        return "", []
    strings = [d for t in texts for d in string_definitions(t)]
    return build_bib(keys, [split_bib(t) for t in texts], strings)


def search(entries: dict[str, dict[str, str]], text: str) -> list[str]:
    """Keys whose key / author / year / title contain every word."""
    words = text.lower().split()
    out = []
    for key, e in entries.items():
        hay = " ".join([key, e.get("author", ""), e.get("year", ""),
                        e.get("title", "")]).lower()
        if all(w in hay for w in words):
            out.append(key)
    return out
