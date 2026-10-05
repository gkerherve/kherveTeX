"""Resolve citations and cross-references for on-screen display.

The visual editor shows `\\cite{smith2020}` as "[1]" or "Smith (2020)"
and `\\ref{sec:intro}` as "2.1", the way the compiled PDF will, instead
of raw keys. Everything here is read-only over the document model; the
LaTeX output is untouched.
"""
from __future__ import annotations

import re
from dataclasses import fields, is_dataclass
from pathlib import Path

from .model import (
    Citation, Document, Figure, MathBlock, RawLatex, Section, Table,
)

_BIB_SOURCE_RE = re.compile(
    r"\\(?:bibliography|addbibresource)(?:\[[^\]]*\])?\{([^}]+)\}")
_BIBITEM_RE = re.compile(r"\\bibitem(?:\[([^\]]*)\])?\{([^}]+)\}")
_ENTRY_START_RE = re.compile(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,")


def _walk(node):
    """Yield every model node below *node*, depth first, in order."""
    yield node
    if is_dataclass(node):
        for f in fields(node):
            val = getattr(node, f.name)
            if isinstance(val, list):
                for item in val:
                    if is_dataclass(item):
                        yield from _walk(item)


def _field_value(body: str, name: str) -> str:
    """The value of `name = {..}` / `"..."` / bare in a BibTeX entry body."""
    m = re.search(r"(?<![\w-])" + name + r"\s*=\s*", body, re.IGNORECASE)
    if not m:
        return ""
    i = m.end()
    if i >= len(body):
        return ""
    if body[i] == "{":
        depth, j = 0, i
        while j < len(body):
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    return body[i + 1:j]
            j += 1
        return body[i + 1:]
    if body[i] == '"':
        j = body.find('"', i + 1)
        return body[i + 1:j if j != -1 else None]
    return re.match(r"[^,}\s]*", body[i:]).group(0)


def parse_bibtex(text: str) -> dict[str, dict[str, str]]:
    """Parse the fields needed for display (author, year, title) out of
    BibTeX source. Tolerant: malformed entries are skipped, not fatal."""
    entries: dict[str, dict[str, str]] = {}
    starts = list(_ENTRY_START_RE.finditer(text))
    for n, m in enumerate(starts):
        kind = m.group(1).lower()
        if kind in ("comment", "string", "preamble"):
            continue
        end = starts[n + 1].start() if n + 1 < len(starts) else len(text)
        body = text[m.end():end]
        entries[m.group(2)] = {
            "author": _field_value(body, "author")
                      or _field_value(body, "editor"),
            "year": _field_value(body, "year")
                    or _field_value(body, "date")[:4],
            "title": _field_value(body, "title"),
        }
    return entries


def _clean(s: str) -> str:
    return re.sub(r"[{}]", "", s).strip()


def short_author(author: str) -> str:
    """'Smith, J. and Doe, A. and Roe, B.' -> 'Smith et al.'"""
    people = [p.strip() for p in re.split(r"\s+and\s+", _clean(author))
              if p.strip()]
    if not people:
        return ""

    def surname(p: str) -> str:
        return p.split(",")[0].strip() if "," in p else p.split()[-1]

    if len(people) == 1:
        return surname(people[0])
    if len(people) == 2:
        return f"{surname(people[0])} and {surname(people[1])}"
    return f"{surname(people[0])} et al."


class ReferenceResolver:
    """Display text for the citations and cross-references of one document."""

    def __init__(self, doc: Document, base_dir: Path | None = None,
                 extra_bib: str = ""):
        self.entries: dict[str, dict[str, str]] = {}
        self._bibitem_labels: dict[str, str] = {}
        self.cite_numbers: dict[str, int] = {}
        self.labels: dict[str, str] = {}
        self._load_bibliography(doc, base_dir)
        # Citations from a KherveRef library (kherveref_link).
        for key, entry in parse_bibtex(extra_bib).items():
            self.entries.setdefault(key, entry)
        self._number_citations(doc)
        self._number_labels(doc)

    def _load_bibliography(self, doc: Document, base_dir: Path | None):
        for node in _walk(doc):
            if not isinstance(node, RawLatex):
                continue
            for m in _BIBITEM_RE.finditer(node.text):
                key = m.group(2).strip()
                self.entries.setdefault(key, {})
                if m.group(1):
                    self._bibitem_labels[key] = m.group(1)
            if base_dir is None:
                continue
            for m in _BIB_SOURCE_RE.finditer(node.text):
                for name in m.group(1).split(","):
                    path = base_dir / name.strip()
                    if path.suffix != ".bib":
                        path = path.with_name(path.name + ".bib")
                    try:
                        text = path.read_text(encoding="utf-8",
                                              errors="replace")
                    except OSError:
                        continue
                    for key, entry in parse_bibtex(text).items():
                        self.entries.setdefault(key, entry)

    def _number_citations(self, doc: Document):
        # Order of first citation, as unsrt / most numeric styles do.
        for node in _walk(doc):
            if isinstance(node, Citation):
                for key in node.keys:
                    self.cite_numbers.setdefault(
                        key, len(self.cite_numbers) + 1)

    def _number_labels(self, doc: Document):
        blocks = list(_walk(doc))
        has_chapters = any(isinstance(b, Section) and b.level == 0
                           for b in blocks)
        counters = [0] * 7   # index 0 = chapter, 1..5 = section levels
        fig = tab = eq = 0

        def prefixed(n: int) -> str:
            return f"{counters[0]}.{n}" if has_chapters else str(n)

        for b in blocks:
            if isinstance(b, Section) and b.numbered:
                lvl = b.level
                counters[lvl] += 1
                for i in range(lvl + 1, len(counters)):
                    counters[i] = 0
                if lvl == 0:
                    fig = tab = eq = 0
                start = 0 if has_chapters else 1
                number = ".".join(str(c) for c in counters[start:lvl + 1])
                if b.label:
                    self.labels[b.label] = number
            elif isinstance(b, Figure):
                fig += 1
                if b.label:
                    self.labels[b.label] = prefixed(fig)
            elif isinstance(b, Table):
                tab += 1
                if b.label:
                    self.labels[b.label] = prefixed(tab)
            elif isinstance(b, MathBlock) and b.numbered:
                eq += 1
                if b.label:
                    self.labels[b.label] = prefixed(eq)

    def cite_text(self, keys: list[str], style: str = "cite") -> str:
        if style in ("citet", "citep"):
            parts = []
            for k in keys:
                e = self.entries.get(k) or {}
                who = short_author(e.get("author", ""))
                year = _clean(e.get("year", ""))
                if not who:
                    parts.append(f"{k}?")
                elif style == "citet":
                    parts.append(f"{who} ({year})" if year else who)
                else:
                    parts.append(f"{who}, {year}" if year else who)
            return "; ".join(parts) if style == "citet" \
                else "(" + "; ".join(parts) + ")"
        shown = []
        for k in keys:
            if k in self._bibitem_labels:
                shown.append(self._bibitem_labels[k])
            elif self.entries and k not in self.entries:
                shown.append(f"{k}?")
            else:
                shown.append(str(self.cite_numbers.get(k, "?")))
        return "[" + ", ".join(shown) + "]"

    def ref_text(self, label: str, kind: str = "ref") -> str:
        if kind == "pageref":
            return "p.\u2009?"
        number = self.labels.get(label, "??")
        return f"({number})" if kind == "eqref" else number
