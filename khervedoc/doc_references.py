"""The document's own references: a .bib that lives inside the .ktex.

KherveRef keeps a library of references shared between documents; a
document may also keep its own list, edited in References ▸ Manage
references (reference_manager.py). The list is the document's
kherveref.bib, bundled in the .ktex as the cited entries of a KherveRef
library are, and `DocMeta.ref_library` is DOCUMENT_LIBRARY. Unlike a
library's copy it holds every entry, cited or not; BibTeX prints only the
cited ones. A KherveTeX that predates the list reads it as the bundled
copy of a library it cannot find, so the document still compiles.

The list is kept as BibTeX source, entry by entry (key -> the entry's
text, as kherveref_link.split_bib gives it), so entries imported from
elsewhere keep every field and comment they had; an entry edited in the
form is written again from its fields.
"""
from __future__ import annotations

import re
import unicodedata

from .kherveref_link import DOCUMENT_LIBRARY, split_bib, string_definitions  # noqa: F401

HEADER = "% The references of this document, kept by KherveTeX.\n\n"

# The entry types offered, and the fields the form shows, in the order
# they are written.
ENTRY_TYPES = ["article", "book", "inproceedings", "incollection",
               "phdthesis", "mastersthesis", "techreport", "misc", "online"]
FIELDS = ["author", "title", "journal", "booktitle", "year", "volume",
          "number", "pages", "publisher", "school", "institution", "doi",
          "url", "note"]

_HEAD_RE = re.compile(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,")


def parse_entry(text: str) -> tuple[str, str, dict[str, str]]:
    """(type, key, fields) of one entry's source; field names lower-case,
    values without their outer braces or quotes, in source order."""
    m = _HEAD_RE.search(text)
    if not m:
        return "misc", "", {}
    etype, key = m.group(1).lower(), m.group(2)
    body = text[m.end():].rstrip()
    if body.endswith(("}", ")")):
        body = body[:-1]
    fields: dict[str, str] = {}
    i, n = 0, len(body)
    while i < n:
        fm = re.compile(r"\s*,?\s*([\w-]+)\s*=\s*").match(body, i)
        if not fm:
            break
        name = fm.group(1).lower()
        i = fm.end()
        if i < n and body[i] == "{":
            depth, j = 0, i
            while j < n:
                if body[j] == "\\":
                    j += 2
                    continue
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            value, i = body[i + 1:j], j + 1
        elif i < n and body[i] == '"':
            j = body.find('"', i + 1)
            j = n if j < 0 else j
            value, i = body[i + 1:j], j + 1
        else:
            bm = re.compile(r"[^,]*").match(body, i)
            value, i = bm.group(0).strip(), bm.end()
        fields.setdefault(name, value.strip())
    return etype, key, fields


def format_entry(etype: str, key: str, fields: dict[str, str]) -> str:
    """BibTeX source for an entry: the known fields in the form's order,
    then any others; empty fields left out."""
    names = [f for f in FIELDS if fields.get(f, "").strip()]
    names += [f for f in fields if f not in FIELDS and fields[f].strip()]
    width = max((len(f) for f in names), default=0)
    lines = [f"  {f.ljust(width)} = {{{fields[f].strip()}}}" for f in names]
    return f"@{etype}{{{key},\n" + ",\n".join(lines) + "\n}"


def _ascii(s: str) -> str:
    s = re.sub(r"\\.|[{}]", "", s)
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def suggest_key(author: str, year: str, title: str, taken) -> str:
    """A citation key as KherveRef makes one: the first author's surname,
    the year and the first word of the title (smith2020decay), with a
    letter added when the key is taken."""
    first = re.split(r"\s+and\s+", author.strip())[0] if author.strip() else ""
    surname = (first.split(",")[0] if "," in first else (first.split() or [""])[-1])
    words = [w for w in re.findall(r"[A-Za-z]+", _ascii(title))
             if w.lower() not in ("a", "an", "the", "on", "of", "in", "and")]
    base = (re.sub(r"[^a-z]", "", _ascii(surname).lower())
            + re.sub(r"\D", "", year)[:4]
            + (words[0].lower() if words else "")) or "ref"
    key, n = base, 0
    while key in taken:
        key = base + chr(ord("a") + n)
        n += 1
    return key


def entries(text: str) -> dict[str, str]:
    """key -> entry source, in the list's order."""
    return split_bib(text)


def write(items: dict[str, str], strings: list[str] = ()) -> str:
    """The list as a .bib: @string definitions first, then the entries;
    '' for an empty list."""
    if not items:
        return ""
    parts = list(dict.fromkeys(strings)) + list(items.values())
    return HEADER + "\n\n".join(parts) + "\n"


def merge(text: str, other: str) -> tuple[str, list[str]]:
    """Add the entries of *other* (a .bib) whose keys the list lacks;
    (new text, keys added). An entry already in the list stays as it is."""
    items = entries(text)
    added = []
    for key, src in entries(other).items():
        if key not in items:
            items[key] = src
            added.append(key)
    strings = string_definitions(text) + string_definitions(other)
    return write(items, strings), added


def set_entry(text: str, old_key: str | None, source: str) -> str:
    """The list with *source* in place of the entry *old_key* (at its
    place), or added at the end when old_key is None or not there."""
    items = entries(text)
    _t, key, _f = parse_entry(source)
    out: dict[str, str] = {}
    placed = False
    for k, v in items.items():
        if k == old_key:
            out[key] = source
            placed = True
        elif k != key:
            out[k] = v
    if not placed:
        out[key] = source
    return write(out, string_definitions(text))


def remove_entry(text: str, key: str) -> str:
    items = entries(text)
    items.pop(key, None)
    return write(items, string_definitions(text))


# What a row of the manager's list is.
CITED, NOT_CITED, MISSING = "cited", "not cited", "missing"


def rows(text: str, cited: list[str]) -> list[dict[str, str]]:
    """The manager's list: every entry (cited or not), then every cited
    key the list lacks (missing), each with its key, author, year, title
    and status."""
    from .references import parse_bibtex
    shown = parse_bibtex(text)
    out = []
    for key in entries(text):
        e = shown.get(key, {})
        out.append({"key": key, "author": e.get("author", ""),
                    "year": e.get("year", ""), "title": e.get("title", ""),
                    "status": CITED if key in cited else NOT_CITED})
    have = {r["key"] for r in out}
    for key in cited:
        if key not in have:
            out.append({"key": key, "author": "", "year": "", "title": "",
                        "status": MISSING})
    return out


def matches(row: dict[str, str], query: str) -> bool:
    """The search bar: every word in the key, author, year or title."""
    hay = " ".join((row["key"], row["author"], row["year"], row["title"])).lower()
    return all(w in hay for w in query.lower().split())
