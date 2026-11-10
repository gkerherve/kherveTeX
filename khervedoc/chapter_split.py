"""Split a long document into a project with one document per chapter.

An imported thesis or book (.tex, Word, PDF) is one long document; editing
and compiling it as a project of chapter documents is much faster, since
the editor lays out and the compiler typesets one chapter at a time while
the project still builds the whole book. `chapter_plan` finds the chapters,
`should_offer` says whether the document is long enough to be worth
splitting, and `write_chapter_project` writes the documents and the
project that lists them.

The split keeps the book as it was: every chapter-level heading starts a
document of its own, in order and numbered as before (an "Appendix" or
"Bibliography" chapter stays a chapter, the chapters after an \\appendix
are appendices), and what comes before the first
chapter (the title, an abstract, acknowledgements) is a front-matter
document. The project prints the same pages as the single document.
"""
from __future__ import annotations

import copy
import dataclasses
import re
from pathlib import Path

from . import kdocz, project_store
from .model import (
    ChapterEntry, Document, Project, Section, class_supports_chapter,
    project_to_json,
)

# A document shorter than this is quick enough as it is.
SPLIT_MIN_PAGES = 30
# Characters of body text on a typical page, and what a figure, table and
# display equation take of one.
_CHARS_PER_PAGE = 2600
_FIGURE_PAGES = 0.35
_TABLE_PAGES = 0.25
_EQUATION_PAGES = 0.05


def _text_len(node) -> int:
    """The characters of text in a block (its inlines, items, cells)."""
    if isinstance(node, str):
        return 0
    if isinstance(node, (list, tuple)):
        return sum(_text_len(n) for n in node)
    if not dataclasses.is_dataclass(node):
        return 0
    n = len(getattr(node, "text", "") or "") if isinstance(
        getattr(node, "text", None), str) else 0
    for f in dataclasses.fields(node):
        if f.name in ("children", "items", "rows", "cells"):
            n += _text_len(getattr(node, f.name))
    return n


def estimate_pages(doc: Document) -> int:
    """About how many pages the document prints."""
    pages = 0.0
    chars = 0
    for b in doc.children:
        kind = type(b).__name__
        if kind == "Figure":
            pages += _FIGURE_PAGES
        elif kind == "Table":
            pages += _TABLE_PAGES
        elif kind == "MathBlock":
            pages += _EQUATION_PAGES
        chars += _text_len(b)
    return round(pages + chars / _CHARS_PER_PAGE)


def _chapter_levels(doc: Document) -> tuple[int, ...]:
    """The heading levels that start a chapter. In report and book, the
    Chapter style (0) and Heading 1 (1) both print as \\chapter; in a plain
    article (a Word or PDF thesis comes in as one) Heading 1 is the
    chapter, and the project becomes a report so it prints as one."""
    cls = (doc.meta.documentclass or "").lower()
    if class_supports_chapter(cls):
        return (0, 1)
    if cls == "article":
        return (0, 1)
    return ()


def _heading_text(sec: Section) -> str:
    return "".join(getattr(c, "text", "") or "" for c in sec.children).strip()


_APPENDIX_RE = re.compile(r"\s*\\appendix\s*")


def _is_appendix_mark(block) -> bool:
    """An \\appendix on its own: a raw block, or a paragraph holding only
    that command."""
    kind = type(block).__name__
    if kind == "RawLatex":
        return bool(_APPENDIX_RE.fullmatch(block.text or ""))
    if kind == "Paragraph":
        kids = [c for c in block.children
                if not (type(c).__name__ == "Text" and not c.text.strip())]
        return (len(kids) == 1 and type(kids[0]).__name__ == "InlineRaw"
                and bool(_APPENDIX_RE.fullmatch(kids[0].latex or "")))
    return False


# A heading that only says which chapter follows ("CHAPTER I", "Chapter 2",
# "Part III"): a PDF or Word thesis sets it on a line of its own.
_CHAPTER_MARK_RE = re.compile(
    r"(?:chapter|part)\s*(?:[ivxlcdm]+|\d+)?\s*[.:]?", re.I)
# The pages before the first chapter.
_FRONT_RE = re.compile(
    r"(?:acknowledge?ments?|contents|table of contents|list of (?:figures|tables|"
    r"abbreviations|symbols|publications)|abstract|preface|dedication|"
    r"declaration(?: of originality)?|nomenclature|glossary|foreword)\s*[.:]?", re.I)
_APPENDIX_TITLE_RE = re.compile(r"appendi(?:x|ces)\b", re.I)


def _merge_label(texts: list[str]) -> str:
    """One chapter's title from the headings that open it: the chapter mark
    dropped, a title broken over two headings joined."""
    words = [t for t in texts if not _CHAPTER_MARK_RE.fullmatch(t)] or texts
    return " ".join(words)


def chapter_plan(doc: Document, by: str = "chapter") -> list[tuple[str, str, list]]:
    """[(label, chapter_type, blocks)] for each document of the split: a
    front matter first when anything comes before the first chapter, then
    one per chapter, or with by="section" also one per section of a
    chapter (chapter_type "section": it continues its chapter's page).
    Empty when there are fewer than two chapters.

    Chapter headings with nothing between them open one chapter ("CHAPTER
    I" then "Introduction"; a long title an import broke in two). The title
    page, acknowledgements, contents and lists of figures and tables at the
    start are the front matter. An \\appendix between chapters, or a
    chapter called Appendix, starts the appendices: the project writes
    \\appendix itself before them and letters them A, B... as the document
    did (inside the chapter before, it was undone by the chapter counter
    the project sets), so the mark is left out.
    """
    levels = _chapter_levels(doc)
    if not levels:
        return []
    cls = (doc.meta.documentclass or "").lower()
    section_level = 2 if by == "section" and class_supports_chapter(cls) else None
    children = doc.children
    # Each document: where it starts, the headings that open it, and
    # whether it is a chapter (else a section of one).
    groups: list[tuple[int, list[str], bool]] = []
    for i, b in enumerate(children):
        if not isinstance(b, Section) or not _heading_text(b):
            continue
        if b.level in levels:
            if groups and groups[-1][2] and i == groups[-1][0] + len(groups[-1][1]):
                groups[-1][1].append(_heading_text(b))
            else:
                groups.append((i, [_heading_text(b)], True))
        elif b.level == section_level and groups:
            groups.append((i, [_heading_text(b)], False))
    labels = [_merge_label(t) for _, t, _ in groups]
    chapters = [g for g in range(len(groups)) if groups[g][2]]
    # The front matter runs to the last front-matter heading in the first
    # half (the title heading of a PDF before its acknowledgements too).
    front = -1
    for g in chapters[:max(1, len(chapters) // 2)]:
        if _FRONT_RE.fullmatch(labels[g]):
            front = g
    body = list(range(front + 1, len(groups)))
    if sum(1 for g in body if groups[g][2]) < 2:
        return []
    marks = [i for i, b in enumerate(children) if _is_appendix_mark(b)]
    first = groups[body[0]][0]
    appendix_from = min([m for m in marks if m > first]
                        + [groups[g][0] for g in body
                           if groups[g][2] and _APPENDIX_TITLE_RE.match(labels[g])]
                        + [len(children)])
    keep = lambda blocks: [b for b in blocks if not _is_appendix_mark(b)]  # noqa: E731
    plan: list[tuple[str, str, list]] = []
    if first > 0:
        plan.append(("Front matter", "frontmatter", keep(children[:first])))
    for k, g in enumerate(body):
        at = groups[g][0]
        end = groups[body[k + 1]][0] if k + 1 < len(body) else len(children)
        if not groups[g][2]:
            ctype = "section"
        else:
            ctype = "appendix" if at >= appendix_from else "chapter"
        plan.append((labels[g], ctype, keep(children[at:end])))
    return plan


def should_offer(doc: Document) -> bool:
    """A document with chapters, long enough that splitting it pays."""
    return len([p for p in chapter_plan(doc) if p[1] in ("chapter", "appendix")]) >= 2 \
        and estimate_pages(doc) >= SPLIT_MIN_PAGES


def _file_stem(label: str, limit: int = 48) -> str:
    s = re.sub(r"[^\w\- ]+", "", label, flags=re.UNICODE).strip()
    s = re.sub(r"\s+", " ", s)[:limit].strip()
    return s or "Chapter"


def project_folder(source: Path) -> Path:
    """Where the split of `source` goes: a new folder beside it."""
    source = Path(source)
    base = source.parent / f"{source.stem} (chapters)"
    folder = base
    n = 2
    while folder.exists():
        folder = source.parent / f"{base.name} {n}"
        n += 1
    return folder


def write_chapter_project(doc: Document, folder: Path, title: str,
                          by: str = "chapter") -> Path:
    """Write each document of the split into `folder` (created) and the
    project into the first of them, the project's main .ktex; return that
    file. The documents share the original's settings; a plain article
    becomes a report so its chapters print as chapters."""
    plan = chapter_plan(doc, by)
    if not plan:
        raise ValueError("The document has fewer than two chapters.")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    meta = copy.deepcopy(doc.meta)
    # Split by chapter, an article's Heading 1 are its chapters: a report
    # prints them so. Split by section, it stays an article.
    if by == "chapter" and (meta.documentclass or "").lower() == "article":
        meta.documentclass = "report"
    proj = Project(meta=copy.deepcopy(meta))
    proj.meta.title = title
    main: Path | None = None
    number = 0
    section = 0
    for k, (label, ctype, blocks) in enumerate(plan):
        if ctype == "section":
            section += 1
            stem = f"{number:02d}.{section} {_file_stem(label)}"
        elif ctype != "frontmatter":
            number += 1
            section = 0
            stem = f"{number:02d} {_file_stem(label)}"
        else:
            stem = _file_stem(label)
        path = project_store.unique_path(folder, stem)
        project_store.write_doc(Document(meta=copy.deepcopy(meta), children=blocks), path)
        proj.chapters.append(ChapterEntry(
            path=path.name, label=label, enabled=True,
            start_page=1 if k == 0 else None, numbering="arabic",
            chapter_type=ctype))
        if main is None:
            main = path
    assert main is not None
    kdocz.write_project_json(main, project_to_json(proj))
    return main
