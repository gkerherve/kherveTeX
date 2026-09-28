"""WYSIWYG editor widget — QTextEdit driving the document model.

Per-block: user-state encodes node type (0=Paragraph, 1-5=Section, 99=MathBlock,
other sentinels for figure/table/raw whose body is stored as block text).

Inlines: special spans (math, link, footnote, citation, cross-ref) are stored
as text fragments with a custom char-format property holding the payload. The
visible text is the human-readable representation; serialization rebuilds the
LaTeX from the property.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import time

from PySide6.QtCore import QEvent, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import (
    QAction, QBrush, QColor, QTextFormat, QFont, QFontDatabase, QFontMetricsF, QImage, QKeySequence, QTextBlockFormat,
    QTextCharFormat, QTextCursor, QTextFrameFormat, QTextImageFormat,
    QTextLength, QTextListFormat, QTextTable, QTextTableFormat,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox,
    QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from . import page_sizes
from .paged_edit import PagedTextEdit


# LaTeX document classes shown in the toolbar combo. Order = display order.
TEMPLATE_CHOICES = [
    # Standard
    "article", "report", "book", "letter", "beamer", "memoir",
    # KOMA-Script
    "scrartcl", "scrreprt", "scrbook", "scrlttr2",
    # Journal / conference
    "elsarticle", "IEEEtran", "revtex4-2", "achemso", "amsart",
    "llncs", "acmart", "svjour3", "sn-jnl", "mnras", "aa",
    # Thesis / long-form
    "tufte-handout", "tufte-book", "mimosis",
    "hepthesis", "suftesi", "toptesi", "disser",
    # Book
    "amsbook", "ElegantBook",
    # Social-science / humanities
    "apa7",
    # CV / résumé
    "moderncv", "europasscv",
    # Poster
    "tikzposter", "a0poster",
    # Exam / problem sets
    "exam",
    # Standalone (TikZ figures, snippets)
    "standalone",
]

from .model import (
    Abstract, Affiliation, Author, Citation, Correspondence, Comment, CrossRef, Document, DocMeta, Figure,
    Footnote, Frame, Highlight, HIGHLIGHT_COLORS, InlineRaw, Keywords, Link,
    List as ListNode, ListItem, MathBlock, MathInline, Paragraph, RawLatex,
    Section, Table, Text, Title,
)


# ---- rendered math (matplotlib mathtext) ----
import re as _re
import hashlib as _hashlib
from io import BytesIO as _BytesIO

_MATH_IMAGE_CACHE: dict[str, Path | None] = {}
# Equations are rasterised at 12pt / _MATH_DPI and shown scaled to the
# body size and zoom. 300 dpi leaves enough pixels for Retina screens,
# where the old 150 dpi, shown 1:1, was both blurry and ~1.8x too big.
_MATH_DPI = 300
_MATH_RENDER_PT = 12
_math_tmp_dir: Path | None = None


def _math_cache_dir() -> Path:
    """Lazy-init a temp directory for rendered math PNGs."""
    global _math_tmp_dir
    if _math_tmp_dir is None:
        _math_tmp_dir = Path(tempfile.mkdtemp(prefix="khervedoc-math-"))
    return _math_tmp_dir

_ENV_STRIP_RE = _re.compile(
    r"\\begin\{(equation|align|gather|multline|displaymath|eqnarray"
    r"|alignat|split)\*?\}(.*?)\\end\{\1\*?\}",
    _re.DOTALL)


def _contains_raw(node, _seen=None) -> bool:
    """True if a parsed equation has parts the typesetter can't draw."""
    from . import mathbox as mb
    seen = set() if _seen is None else _seen
    if id(node) in seen:
        return False
    seen.add(id(node))
    if isinstance(node, mb.Raw):
        return True
    if isinstance(node, (list, tuple)):
        return any(_contains_raw(n, seen) for n in node)
    attrs = dict(getattr(node, "__dict__", {}))
    for slot in getattr(type(node), "__slots__", ()):
        attrs[slot] = getattr(node, slot, None)
    for name, val in attrs.items():
        # Rows point back at their owner; following that loops forever.
        if name in ("owner", "parent") or val is None \
                or isinstance(val, (str, int, float, bool)):
            continue
        if _contains_raw(val, seen):
            return True
    return False


_CE_ARROWS = {"<=>": r"\rightleftharpoons", "<->": r"\leftrightarrow",
              "->": r"\rightarrow", "<-": r"\leftarrow",
              "=": "=", "+": "+"}


def _ce_species(tok: str) -> str:
    """One mhchem species ("2H2O", "SO4^2-", "Na+", "CuSO4.5H2O", "H2O(l)")
    as upright math: element symbols roman, counts subscripted, charge up,
    hydrate dots centred."""
    if "." in tok or "*" in tok:
        return r"\cdot ".join(_ce_species(p) for p in _re.split(r"[.*]", tok))
    m = _re.match(r"^(\d*)(.*?)(\((?:s|l|g|aq)\))?$", tok)
    coeff, body, state = m.group(1), m.group(2), m.group(3) or ""
    charge = ""
    cm = _re.search(r"\^\{?([0-9]*[+-])\}?$", body) \
        or _re.search(r"(?<=[A-Za-z0-9)\]])([0-9]*[+-])$", body)
    if cm and body[:cm.start()]:
        charge, body = cm.group(1), body[:cm.start()]
    out = []
    for part in _re.findall(r"[A-Z][a-z]?|\d+|[a-z]+|.", body):
        if part.isdigit():
            out.append(f"_{{{part}}}")
        elif part.isalpha():
            out.append(rf"\mathrm{{{part}}}")
        else:
            out.append(part)
    res = "".join(out)
    if charge:
        res += f"^{{{charge}}}"
    if state:
        res += rf"\,\mathrm{{{state}}}"
    return rf"{coeff}\,{res}" if coeff else res


def _ce_to_math(latex: str) -> str:
    """Rewrite \\ce{...} (mhchem) into plain math the typesetter draws,
    covering ordinary formulas and reactions; the LaTeX output still
    uses mhchem. Anything unusual is left as it was."""
    def conv(m):
        body = m.group(1).strip()
        parts = []
        for tok in body.split():
            parts.append(_CE_ARROWS.get(tok) or _ce_species(tok))
        return " ".join(parts)
    return _re.sub(r"\\ce\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", conv, latex)


def _render_math_typeset(latex: str, png_path: Path, display: bool) -> bool:
    """Typeset *latex* with the equation editor's own engine (Latin
    Modern Math), so an inserted equation looks exactly as it did in the
    editor. False when it has constructs only LaTeX knows (\\ce, custom
    macros...) — the caller then falls back to matplotlib rather than
    showing grey placeholder chips on the page."""
    try:
        from . import mathbox as mb, mathlayout as ml
        src = _re.sub(r"\\(label\{[^}]*\}|nonumber|notag)", "", latex.strip())
        if "\\ce{" in src:
            src = _ce_to_math(src)
        row = mb.parse_latex(src)
        if _contains_raw(row):
            return False
        px = _MATH_RENDER_PT * _MATH_DPI / 72
        img = ml.render_image(row, px=px, display=display, dpr=1.0,
                              pad=px * 0.12)
        return not img.isNull() and img.save(str(png_path), "PNG")
    except Exception:
        return False


def _render_math_image(latex: str, font_size: int = _MATH_RENDER_PT,
                       cache_dir: Path | None = None,
                       display: bool = True) -> Path | None:
    """Render a LaTeX math expression to a PNG file using matplotlib.

    Handles multi-line equations (align, gather, etc.) by splitting on
    ``\\\\`` and rendering each line separately, stacked vertically.
    Returns the path to the PNG file, or None on failure. Results are
    cached on disk.  When *cache_dir* is given the PNG is written there
    instead of the global temp directory."""
    key = latex if display else "\x00inline" + latex
    if key in _MATH_IMAGE_CACHE:
        cached = _MATH_IMAGE_CACHE[key]
        if cached is not None and cached.exists():
            return cached
    h = _hashlib.md5(latex.encode()).hexdigest()[:12]
    dest = cache_dir if cache_dir is not None else _math_cache_dir()
    typeset_png = dest / f"math_{h}{'' if display else '-i'}.png"
    if _render_math_typeset(latex, typeset_png, display):
        _MATH_IMAGE_CACHE[key] = typeset_png
        return typeset_png
    try:
        from matplotlib.figure import Figure as MplFigure
    except ImportError:
        _MATH_IMAGE_CACHE[key] = None
        return None
    # Strip environment wrappers to get bare math.
    raw = latex.strip()
    m = _ENV_STRIP_RE.search(raw)
    if m:
        raw = m.group(2).strip()
    raw = raw.strip("$").strip()
    if not raw:
        _MATH_IMAGE_CACHE[key] = None
        return None
    # Translate LaTeX commands that mathtext doesn't know about.
    # \square (the palette placeholder) renders as a bullet, matching the
    # equation-editor preview — otherwise an equation inserted with an
    # unfilled slot showed no picture at all in the Visual view.
    raw = raw.replace("\\square", "\\bullet")
    raw = raw.replace("\\tfrac", "\\frac")
    raw = raw.replace("\\dfrac", "\\frac")
    raw = raw.replace("\\text{", "\\mathrm{")
    raw = raw.replace("\\operatorname{", "\\mathrm{")
    raw = raw.replace("\\displaystyle", "")
    raw = raw.replace("\\textstyle", "")
    raw = raw.replace("\\nonumber", "")
    raw = raw.replace("\\notag", "")
    raw = raw.replace("\\label{", "\\mathrm{")  # hide labels
    # Handle \begin{cases}...\end{cases} sub-environments: matplotlib's
    # mathtext can't render them, so we expand into separate lines with
    # a left-brace prefix to visually indicate the case structure.
    _cases_re = _re.compile(
        r"\\begin\{(cases|rcases|dcases)\}(.*?)\\end\{\1\}", _re.DOTALL)
    cm = _cases_re.search(raw)
    if cm:
        prefix = raw[:cm.start()].strip().rstrip("=").strip()
        case_body = cm.group(2).strip()
        suffix = raw[cm.end():].strip()
        case_lines = _re.split(r"\\\\", case_body)
        case_lines = [ln.replace("&", "\\quad ").strip()
                       for ln in case_lines if ln.strip()]
        lines = []
        if prefix:
            lines.append(prefix + " =")
        for j, cl in enumerate(case_lines):
            # Use \left\{ ... \right. (invisible right) for the first
            # line, plain indent for subsequent lines.
            if j == 0:
                lines.append("\\left\\{ " + cl + " \\right.")
            else:
                lines.append("\\;\\;\\;\\;\\; " + cl)
        if suffix:
            lines.append(suffix)
    else:
        # Strip matrix-like sub-envs that mathtext can't handle.
        raw = _re.sub(
            r"\\begin\{(matrix|pmatrix|bmatrix|vmatrix|Bmatrix|"
            r"smallmatrix)\}(.*?)\\end\{\1\}",
            lambda m2: m2.group(2).replace("&", "\\;\\;"),
            raw, flags=_re.DOTALL)
        # Split multi-line math on \\ and clean up alignment markers.
        lines = _re.split(r"\\\\", raw)
        lines = [ln.replace("&", " ").strip() for ln in lines]
        lines = [ln for ln in lines if ln]
    # Fix \left / \right pairs that span multiple lines: matplotlib
    # requires them balanced on every line. Strip the sizing prefix
    # from any unmatched \left or \right, keeping the bare delimiter.
    for idx, ln in enumerate(lines):
        n_left = len(_re.findall(r"\\left\b", ln))
        n_right = len(_re.findall(r"\\right\b", ln))
        if n_left != n_right:
            ln = _re.sub(r"\\left\b\s*", "", ln)
            ln = _re.sub(r"\\right\b\s*", "", ln)
            lines[idx] = ln.strip()
    lines = [ln for ln in lines if ln]
    if not lines:
        _MATH_IMAGE_CACHE[key] = None
        return None
    try:
        n = len(lines)
        line_height = 0.35
        fig_h = max(0.4, n * line_height)
        fig = MplFigure(figsize=(6, fig_h), dpi=_MATH_DPI)
        fig.patch.set_alpha(0)
        for i, line in enumerate(lines):
            y = 1.0 - (i + 0.5) / n
            fig.text(0.5, y, f"${line}$", fontsize=font_size,
                     ha="center", va="center", math_fontfamily="cm")
        h = _hashlib.md5(latex.encode()).hexdigest()[:12]
        dest = cache_dir if cache_dir is not None else _math_cache_dir()
        png_path = dest / f"math_{h}.png"
        fig.savefig(str(png_path), format="png", bbox_inches="tight",
                    pad_inches=0.04, transparent=True)
        _MATH_IMAGE_CACHE[key] = png_path
        return png_path
    except Exception as exc:
        import traceback, sys as _sys
        try:
            log = Path(tempfile.gettempdir()) / "khervedoc-math-errors.log"
            with open(log, "a") as fh:
                fh.write(f"--- {latex[:80]!r} ---\n")
                traceback.print_exc(file=fh)
        except Exception:
            pass
        _MATH_IMAGE_CACHE[key] = None
        return None


_COMPLEX_MATH_RE = _re.compile(
    r"\\(frac|left|right|sum|prod|int|begin|sqrt|matrix|cases)")


def _is_complex_math(latex: str) -> bool:
    """True when inline math is too complex for readable raw-text display."""
    return "\n" in latex or bool(_COMPLEX_MATH_RE.search(latex))


def _latex_to_display(s: str) -> str:
    """Simplify raw LaTeX to readable plain text for visual summaries."""
    s = _re.sub(r"\\textit\{([^}]*)\}", r"\1", s)
    s = _re.sub(r"\\textbf\{([^}]*)\}", r"\1", s)
    s = _re.sub(r"\\textsc\{([^}]*)\}", r"\1", s)
    s = _re.sub(r"\\emph\{([^}]*)\}", r"\1", s)
    s = _re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = _re.sub(r"\\mathrm\{([^}]*)\}", r"\1", s)
    # Inline math: $x_2$ → x₂, $x^2$ → x²  (simple cases)
    s = s.replace("$", "")
    s = s.replace(r"\_", "_")
    s = s.replace(r"\&", "&")
    return s


# ---- per-block user state encoding ----
_STATE_PARAGRAPH = 0
_STATE_TITLE = 7        # Word-style "Title" paragraph; emits \maketitle
_STATE_AUTHOR = 8       # Author of the document; pulled into \author{} preamble
_STATE_ABSTRACT = 9     # Abstract paragraph; consecutive blocks merge
_STATE_KEYWORDS = 10    # Keyword line; consecutive blocks merge with \sep
_STATE_CHAPTER = 11     # \chapter — only valid in report/book/memoir classes
_STATE_FRAME = 12       # \begin{frame} — only valid in beamer class
_STATE_AFFILIATION = 13  # Institution line under the authors
_STATE_CORRESPONDENCE = 14  # Corresponding-author note (\thanks)
# Unnumbered variants: \section*{}, \subsection*{}, etc.
# State = 20 + level for headings, 31 for chapter*.
_STATE_HEADING_STAR_BASE = 20   # 21..25 = heading 1*..5*
_STATE_CHAPTER_STAR = 31
_STATE_MATH_BLOCK = 99
_STATE_FIGURE = 100
_STATE_TABLE = 101
_STATE_RAW = 102


# Re-export from model so existing imports (tests, etc.) keep working.
from .model import CHAPTER_CLASSES, class_supports_chapter  # noqa: F401
from .references import ReferenceResolver
from .paged_edit import HEADING_NUMBER_PROPERTY


# ---- char-format custom property ids ----
_P_MATH = QTextCharFormat.UserProperty + 1
_P_LINK = QTextCharFormat.UserProperty + 2     # value = url
_P_FOOTNOTE = QTextCharFormat.UserProperty + 3  # value = note text
_P_CITATION = QTextCharFormat.UserProperty + 4  # value = "key1,key2|style"
_P_CROSSREF = QTextCharFormat.UserProperty + 5  # value = "label|kind"
_P_RAW = QTextCharFormat.UserProperty + 6       # value = raw LaTeX source
_P_HIGHLIGHT = QTextCharFormat.UserProperty + 7  # value = color name
_P_COMMENT = QTextCharFormat.UserProperty + 8    # value = "note|author|timestamp|resolved"
_P_RAW_BLOCK = QTextCharFormat.UserProperty + 9  # original RawLatex source on block format
# Block-format properties for math blocks. Without them every visual edit
# demoted \begin{equation} to equation* and dropped the \label{} — the
# block text only carries the LaTeX body.
_P_MATH_NUMBERED = QTextCharFormat.UserProperty + 10  # value = bool
_P_MATH_LABEL = QTextCharFormat.UserProperty + 11     # value = label str


# ---- block payload storage (figures/tables/raw) ----
# Block-text holds a compact serialization the editor doesn't try to render
# visually beyond a stub. Each block's TYPE is identified by its userState
# (figures get _STATE_FIGURE, etc.), so the stub text doesn't need a
# "[TABLE]" / "[FIGURE]" prefix — those were developer-noise and have been
# removed. Current format examples (all kept in one QTextBlock by
# substituting U+2028 for '\n'):
#   Figure: <path>
#           Caption: <text>
#           Label: <label>
#           Width: <width>
#   Table:  r1c1<TAB>r1c2<TAB>...
#           r2c1<TAB>r2c2<TAB>...
#           Caption: <text>
#           Label: <label>
#           Alignment: <align>
#   Raw / Code / Bibliography: raw LaTeX text with internal '\n' replaced
#           by U+2028 so Qt keeps every line in the same QTextBlock.
# The OLD prefixed format ("[TABLE] ... || cap | label | align") is still
# accepted by _table_from_stub / _figure_from_stub etc. so sessions
# carrying stale stubs still load cleanly.
_FIGURE_PREFIX = "[FIGURE] "      # legacy — accepted on read, never written
_TABLE_PREFIX = "[TABLE] "        # legacy — accepted on read, never written
_RAW_PREFIX = "[RAW] "            # legacy — accepted on read, never written
_CODE_PREFIX = "[CODE] "          # legacy — accepted on read, never written
_BIB_PREFIX = "[BIBLIOGRAPHY] "   # legacy — accepted on read, never written
# Read-back prefix list. Kept for backward compatibility with older
# documents whose RawLatex stubs were prefixed.
_RAW_PREFIXES = (_CODE_PREFIX, _BIB_PREFIX, _RAW_PREFIX)
# Field labels for the meta line(s) appended to a figure/table stub.
_META_CAPTION = "Caption: "
_META_LABEL = "Label: "
_META_WIDTH = "Width: "
_META_ALIGNMENT = "Alignment: "
_META_KEYS = (_META_CAPTION, _META_LABEL, _META_WIDTH, _META_ALIGNMENT)


def _figure_stub(block) -> str:
    """Render a Figure as a multi-line stub kept inside one QTextBlock
    (lines joined with U+2028). Each metadata field is on its own
    visible line with a clear "Caption:" / "Label:" / "Width:" label
    so the editor doesn't expose `|`-separated developer noise."""
    parts = [block.path]
    parts.append(f"{_META_CAPTION}{block.caption or ''}")
    parts.append(f"{_META_LABEL}{block.label or ''}")
    parts.append(f"{_META_WIDTH}{block.width or ''}")
    return _LINE_SEP.join(parts)


def _table_stub(block) -> str:
    """Render a Table the same way: rows first (TAB-separated cells,
    U+2028-separated rows), then one metadata line per attribute."""
    rows = [_LINE_SEP.join("\t".join(r) for r in block.rows)] if block.rows else []
    meta = [
        f"{_META_CAPTION}{block.caption or ''}",
        f"{_META_LABEL}{block.label or ''}",
        f"{_META_ALIGNMENT}{block.alignment or ''}",
    ]
    return _LINE_SEP.join(filter(None, rows + meta))


def _split_stub_meta(text: str) -> tuple[list[str], dict[str, str]]:
    """Split a stub into (content lines, metadata dict).

    Walks the trailing lines of `text` (split on U+2028) and pulls off
    any that start with one of the known meta labels. Stops as soon as
    a line doesn't look like a meta line — the rest are content.
    Returns the content lines in their original order plus a {label
    (no trailing space): value} dict."""
    if not text:
        return [], {}
    lines = text.split(_LINE_SEP)
    meta: dict[str, str] = {}
    # Walk from the back; remove meta lines as we encounter them.
    while lines:
        last = lines[-1]
        matched = None
        for key in _META_KEYS:
            if last.startswith(key):
                matched = key
                break
        if matched is None:
            break
        meta[matched.rstrip(": ")] = last[len(matched):]
        lines.pop()
    return lines, meta
# Qt splits text into separate QTextBlocks at every '\n'. For block-text
# fields that NEED to carry literal newlines (multi-line lstlisting and
# verbatim envs, multi-row tables) we substitute U+2028 (Unicode "Line
# Separator"), which Qt renders as a soft line break inside one block
# and which round-trips losslessly on read-back.
_LINE_SEP = chr(0x2028)
# Separates a typeset equation image from its (hidden) LaTeX source.
# Zero-width, so the equation sits inline instead of forcing the line
# break the old U+2028 separator did.
_MATH_SEP = "\u200b"


# Heading sizes: 0 is reserved for \chapter (the largest), then the
# usual section / subsection / … hierarchy. Chapter sits above
# Heading 1 because that's how LaTeX's book / report layout typesets it.
# Heading size as a multiple of the body size, from LaTeX's standard
# classes at 12pt: \chapter \huge, \section \Large, \subsection
# \large, and body size below that.
_HEADING_SCALE = {0: 24.88 / 12, 1: 17.28 / 12, 2: 14.4 / 12,
                  3: 1.0, 4: 1.0, 5: 1.0}
# Space above / below headings in body ems, after article.cls
# (\section 3.5ex / 2.3ex, \subsection 3.25ex / 1.5ex; 1ex ~ 0.43em).
_HEADING_SPACING = {0: (3.0, 2.0), 1: (1.5, 1.0), 2: (1.4, 0.65),
                    3: (1.4, 0.65), 4: (1.4, 0.0), 5: (1.4, 0.0)}
# Levels LaTeX numbers by default (secnumdepth 3 in article).
_NUMBERED_HEADING_LEVELS = (0, 1, 2, 3)
_P_HEADING_NUMBER = HEADING_NUMBER_PROPERTY

# Bidirectional mapping for paragraph alignment.
_QT_ALIGNMENT = {
    "left": Qt.AlignLeft,
    "center": Qt.AlignHCenter,
    "right": Qt.AlignRight,
    "justify": Qt.AlignJustify,
}
# Qt.AlignLeft is the default for new blocks; in LaTeX semantics that
# corresponds to justified text (no wrapper env). Map both to "justify"
# so paragraphs don't spuriously acquire \begin{flushleft} wrappers.
_ALIGNMENT_FROM_QT = {
    Qt.AlignLeft: "justify",
    Qt.AlignHCenter: "center",
    Qt.AlignRight: "right",
    Qt.AlignJustify: "justify",
}
_TITLE_SCALE = 20.74 / 12   # \maketitle uses \LARGE

_PX_PER_CM = 96 / 2.54

# Screen stand-ins for the LaTeX body fonts, best match first. Georgia
# (the old fixed default) is much wider than Computer Modern, so lines
# and pages broke in different places on screen than in the PDF.
_SCREEN_FONTS_FOR_LATEX = {
    "default":   ["Latin Modern Roman", "LM Roman 10", "CMU Serif",
                  "Computer Modern", "Times New Roman", "Times"],
    "times":     ["Times New Roman", "Times", "TeX Gyre Termes",
                  "Nimbus Roman"],
    "palatino":  ["Palatino Linotype", "Palatino", "TeX Gyre Pagella",
                  "Book Antiqua"],
    "helvetica": ["Helvetica", "Arial", "TeX Gyre Heros", "Liberation Sans"],
    "courier":   ["Courier New", "Courier", "TeX Gyre Cursor"],
    "charter":   ["Charter", "Bitstream Charter", "XCharter"],
    "libertine": ["Linux Libertine O", "Linux Libertine",
                  "Libertinus Serif"],
}


def screen_font_for(meta: DocMeta) -> str:
    """The editor font for *meta*: the user's explicit choice, or — when
    left at the default — the closest installed match to the PDF font."""
    chosen = meta.visual_font_family
    if chosen and chosen != "Georgia":
        return chosen
    if meta.body_font_family == "default":
        from . import latex_fonts
        if latex_fonts.ensure_loaded(meta.body_font_pt):
            return latex_fonts.FAMILY
    installed = set(QFontDatabase.families())
    for family in _SCREEN_FONTS_FOR_LATEX.get(meta.body_font_family, []):
        if family in installed:
            return family
    return chosen or "Georgia"


def _style_code(state: int) -> int | None:
    """apply_heading's code for a text-block style, None for anything
    that is not a styled text line (math, figures, tables, unset)."""
    if state == _STATE_PARAGRAPH: return 0
    if state == _STATE_TITLE: return -1
    if state == _STATE_AUTHOR: return -2
    if state == _STATE_ABSTRACT: return -3
    if state == _STATE_KEYWORDS: return -4
    if state in (_STATE_CHAPTER, _STATE_CHAPTER_STAR): return -5
    if state == _STATE_FRAME: return -6
    if state == _STATE_AFFILIATION: return -7
    if state == _STATE_CORRESPONDENCE: return -8
    if 1 <= state <= 5: return state
    if _STATE_HEADING_STAR_BASE < state <= _STATE_HEADING_STAR_BASE + 5:
        return state - _STATE_HEADING_STAR_BASE
    return None


def _heading_char_format(level: int, body_pt: float = 12,
                         family: str | None = None) -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont(family) if family else QFont()
    f.setBold(True)
    f.setPointSizeF(body_pt * _HEADING_SCALE.get(level, 1.0))
    fmt.setFont(f)
    return fmt


def _frame_char_format() -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont()
    f.setBold(True)
    f.setPointSize(18)
    fmt.setFont(f)
    fmt.setForeground(QColor("#1565C0"))
    return fmt


def _title_char_format(body_pt: float = 12,
                       family: str | None = None) -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont(family) if family else QFont()
    f.setBold(True)
    f.setPointSizeF(body_pt * _TITLE_SCALE)
    fmt.setFont(f)
    return fmt


def _title_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setAlignment(Qt.AlignHCenter)
    bfmt.setTopMargin(8); bfmt.setBottomMargin(8)
    return bfmt


# Title-block line sizes relative to body text, matching \maketitle's
# \large author and \small affiliation so the page looks like the PDF.
_TITLE_BLOCK_SCALE = {-2: 1.2, -7: 0.9, -8: 0.8}


def _author_char_format(body_pt: float = 12,
                        family: str | None = None) -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont(family) if family else QFont()
    f.setItalic(True); f.setPointSizeF(body_pt * _TITLE_BLOCK_SCALE[-2])
    fmt.setFont(f)
    fmt.setForeground(QColor("#555"))
    return fmt


def _author_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setAlignment(Qt.AlignHCenter)
    bfmt.setTopMargin(0); bfmt.setBottomMargin(24)
    return bfmt


def _affiliation_char_format(correspondence: bool = False,
                             body_pt: float = 12,
                             family: str | None = None) -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont(family) if family else QFont()
    f.setItalic(not correspondence)
    f.setPointSizeF(body_pt * _TITLE_BLOCK_SCALE[-8 if correspondence else -7])
    fmt.setFont(f)
    fmt.setForeground(QColor("#555"))
    return fmt


def _affiliation_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setAlignment(Qt.AlignHCenter)
    bfmt.setTopMargin(0); bfmt.setBottomMargin(6)
    return bfmt


def _abstract_char_format() -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont()
    f.setPointSize(11)
    fmt.setFont(f)
    return fmt


def _abstract_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    # Inset the abstract on both sides + warm cream highlight so it
    # reads as a journal-style abstract block at a glance, clearly
    # distinct from body text.
    bfmt.setLeftMargin(48); bfmt.setRightMargin(48)
    bfmt.setTopMargin(8); bfmt.setBottomMargin(8)
    bfmt.setBackground(QColor("#fff5d6"))
    return bfmt


def _keywords_char_format() -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont()
    f.setItalic(True); f.setPointSize(11)
    fmt.setFont(f)
    fmt.setForeground(QColor("#444"))
    return fmt


def _keywords_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    # Pale blue band to mark keywords as a separate "metadata" block,
    # distinct from both body text and the abstract above it.
    bfmt.setLeftMargin(48); bfmt.setRightMargin(48)
    bfmt.setTopMargin(4); bfmt.setBottomMargin(18)
    bfmt.setBackground(QColor("#e3f0ff"))
    return bfmt


def _math_block_char_format() -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont("Consolas"); f.setStyleHint(QFont.Monospace); f.setPointSize(11)
    fmt.setFont(f)
    fmt.setBackground(QColor("#eef3ff")); fmt.setForeground(QColor("#1a3a8c"))
    return fmt


def _math_hidden_format(latex: str | None = None) -> QTextCharFormat:
    """Invisible run holding an equation's LaTeX next to its typeset
    image: the model reads the source back from the text, but on the
    page only the equation shows, as it will in the PDF."""
    fmt = QTextCharFormat()
    f = QFont()
    f.setPointSizeF(1)
    fmt.setFont(f)
    fmt.setForeground(QColor(0, 0, 0, 0))
    if latex is not None:
        fmt.setProperty(_P_MATH, latex)
    return fmt


def _math_inline_format(latex: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont("Consolas"); f.setStyleHint(QFont.Monospace)
    fmt.setFont(f)
    fmt.setBackground(QColor("#fff5d6")); fmt.setForeground(QColor("#7a4c00"))
    fmt.setProperty(_P_MATH, latex)
    return fmt


def _link_format(url: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor("#1a6dd8")); fmt.setFontUnderline(True)
    fmt.setToolTip(url); fmt.setProperty(_P_LINK, url)
    return fmt


def _footnote_format(note: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor("#7a4c00")); fmt.setBackground(QColor("#fff0d0"))
    f = fmt.font(); f.setPointSize(max(8, f.pointSize() - 2)); fmt.setFont(f)
    fmt.setToolTip(note); fmt.setProperty(_P_FOOTNOTE, note)
    return fmt


def _citation_format(keys_style: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor("#5b2d83")); fmt.setBackground(QColor("#f1e5ff"))
    fmt.setProperty(_P_CITATION, keys_style)
    fmt.setToolTip("\\cite{" + keys_style.partition("|")[0] + "}")
    return fmt


def _crossref_format(label_kind: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor("#0a6")); fmt.setBackground(QColor("#e3f5ea"))
    fmt.setProperty(_P_CROSSREF, label_kind)
    label, _, kind = label_kind.partition("|")
    fmt.setToolTip(f"\\{kind or 'ref'}{{{label}}}")
    return fmt


def _raw_inline_format(latex: str) -> QTextCharFormat:
    """Display InlineRaw nodes (unknown macros preserved from .tex
    imports, text-mode symbol-palette inserts like \\Kstroke) in a
    monospace muted tag so the user can see they're verbatim LaTeX
    rather than typeable letters."""
    fmt = QTextCharFormat()
    f = QFont("Consolas"); f.setStyleHint(QFont.Monospace)
    fmt.setFont(f)
    fmt.setForeground(QColor("#0a3d62")); fmt.setBackground(QColor("#e8f0fb"))
    fmt.setToolTip(latex); fmt.setProperty(_P_RAW, latex)
    return fmt


def _highlight_format(color: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    hex_color = HIGHLIGHT_COLORS.get(color, "#FFFF00")
    fmt.setBackground(QColor(hex_color))
    fmt.setProperty(_P_HIGHLIGHT, color)
    return fmt


def _comment_format(note: str, author: str, timestamp: str,
                    resolved: bool) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setBackground(QColor("#FFE4B5"))
    fmt.setUnderlineStyle(QTextCharFormat.DashUnderline)
    fmt.setUnderlineColor(QColor("#d96b00"))
    resolved_str = "1" if resolved else "0"
    payload = f"{note}|{author}|{timestamp}|{resolved_str}"
    fmt.setProperty(_P_COMMENT, payload)
    tip = f"{author}: {note}" if author else note
    fmt.setToolTip(tip)
    return fmt


def _stub_block_format() -> QTextBlockFormat:
    # Generic stub backdrop — kept as a fallback for code paths that
    # don't yet differentiate by content type. Per-type variants below
    # give each kind of block a distinct visual hint.
    bfmt = QTextBlockFormat()
    bfmt.setTopMargin(6); bfmt.setBottomMargin(6)
    bfmt.setBackground(QColor("#f5f5f7"))
    return bfmt


# Theme-aware palettes for table/figure/raw block widgets. The editor
# stores its current theme on self._dark and looks up the matching
# palette here. Keys match the field name; values are QColor strings.
_LIGHT_PALETTE = {
    "figure_block_bg":  "#e8f5e9",
    "table_block_bg":   "#fff3e0",
    "table_border":     "#e6a85c",
    "table_bg":         "#fff3e0",
    "table_header_bg":  "#ffe0b2",
    "table_header_fg":  "#e65100",
    "table_cell_fg":    "#333333",
    "table_caption_fg": "#888888",
    "figure_border":    "#c8e6c9",
    "figure_bg":        "#e8f5e9",
    "figure_caption_fg": "#2e7d32",
}
_DARK_PALETTE = {
    # Backgrounds tuned to be clearly visible against the editor's
    # #2d2d2d dark page while keeping enough lightness to read text on.
    "figure_block_bg":  "#1f3d2a",
    "table_block_bg":   "#3d2e1a",
    "table_border":     "#a37745",
    "table_bg":         "#3d2e1a",
    "table_header_bg":  "#5a3f1f",
    "table_header_fg":  "#ffab40",
    "table_cell_fg":    "#e8e0d4",
    "table_caption_fg": "#b0a99a",
    "figure_border":    "#5a8a5a",
    "figure_bg":        "#1f3d2a",
    "figure_caption_fg": "#a5d6a7",
}


def _palette(dark: bool) -> dict:
    return _DARK_PALETTE if dark else _LIGHT_PALETTE


def _figure_block_format(dark: bool = False) -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setTopMargin(6); bfmt.setBottomMargin(6)
    bfmt.setBackground(QColor(_palette(dark)["figure_block_bg"]))
    return bfmt


def _table_block_format(dark: bool = False) -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setTopMargin(6); bfmt.setBottomMargin(6)
    bfmt.setBackground(QColor(_palette(dark)["table_block_bg"]))
    return bfmt


def _make_table_format(ncols: int, dark: bool = False) -> QTextTableFormat:
    """A borderless, centred, natural-width table like LaTeX's tabular;
    the rules themselves are drawn per cell by `_apply_table_rules`."""
    tfmt = QTextTableFormat()
    tfmt.setBorder(0)
    tfmt.setBorderCollapse(True)
    tfmt.setCellPadding(0)
    tfmt.setCellSpacing(0)
    tfmt.setMargin(8)
    tfmt.setAlignment(Qt.AlignHCenter)
    return tfmt


_COL_SPEC_RE = _re.compile(
    r"\|"                                   # vertical rule
    r"|[@!<>]\{(?:[^{}]|\{[^{}]*\})*\}"     # @{..} >{..} <{..}: no column
    r"|[pmbw]\{(?:[^{}]|\{[^{}]*\})*\}"     # fixed-width column
    r"|[lcrXSs]")


def _parse_column_spec(spec: str, ncols: int) -> tuple[list[str], list[bool]]:
    """Per-column alignment ('l'/'c'/'r') and, for each of the ncols+1
    column boundaries, whether a vertical rule ('|') sits there."""
    aligns: list[str] = []
    vrules = [False]
    for tok in _COL_SPEC_RE.findall(spec or ""):
        if tok == "|":
            vrules[-1] = True
        elif tok[0] in "@!<>":
            continue
        else:
            aligns.append({"c": "c", "r": "r"}.get(tok[0], "l"))
            vrules.append(False)
    aligns = (aligns + ["l"] * ncols)[:ncols]
    vrules = (vrules + [False] * (ncols + 1))[:ncols + 1]
    return aligns, vrules


_CELL_ALIGN = {"l": Qt.AlignLeft, "c": Qt.AlignHCenter, "r": Qt.AlignRight}


def _cell_display_text(raw: str) -> str:
    display = _re.sub(r"\\(?:textbf|textit|emph|texttt)\{([^}]*)\}", r"\1", raw)
    return display.strip()


# Custom property to store table metadata (caption, label, alignment)
# on the QTextTable's frame format so we can read it back.
_P_TABLE_CAPTION = QTextCharFormat.UserProperty + 20
_P_TABLE_LABEL = QTextCharFormat.UserProperty + 21
_P_TABLE_ALIGNMENT = QTextCharFormat.UserProperty + 22
_P_TABLE_STYLE = QTextCharFormat.UserProperty + 23
_P_CELL_RAW = QTextCharFormat.UserProperty + 24       # cell's LaTeX source
_P_CAPTION_ROW = QTextCharFormat.UserProperty + 25    # on caption cell

# Figure-table properties (figures rendered as 1-column QTextTable).
_P_FIGURE_PATH = QTextCharFormat.UserProperty + 30
_P_FIGURE_LABEL = QTextCharFormat.UserProperty + 31
_P_FIGURE_WIDTH = QTextCharFormat.UserProperty + 32
_P_FIGURE_SOURCE = QTextCharFormat.UserProperty + 38
_P_IS_FIGURE = QTextCharFormat.UserProperty + 33


def _make_figure_table_format(dark: bool = False) -> QTextTableFormat:
    """QTextTableFormat for a figure widget (1-column table)."""
    p = _palette(dark)
    tfmt = QTextTableFormat()
    tfmt.setBorderBrush(QColor(p["figure_border"]))
    tfmt.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)
    tfmt.setBorder(1)
    tfmt.setCellPadding(8)
    tfmt.setCellSpacing(0)
    tfmt.setBackground(QColor(p["figure_bg"]))
    tfmt.setMargin(10)
    tfmt.setAlignment(Qt.AlignHCenter)
    tfmt.setColumnWidthConstraints(
        [QTextLength(QTextLength.PercentageLength, 100)])
    tfmt.setProperty(_P_IS_FIGURE, True)
    return tfmt


def _code_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setTopMargin(6); bfmt.setBottomMargin(6)
    bfmt.setBackground(QColor("#eef2f7"))   # pale slate — "code"
    return bfmt


def _bibliography_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setTopMargin(6); bfmt.setBottomMargin(6)
    bfmt.setBackground(QColor("#f3e5f5"))   # pale purple — "references"
    return bfmt


def _raw_block_format() -> QTextBlockFormat:
    bfmt = QTextBlockFormat()
    bfmt.setTopMargin(6); bfmt.setBottomMargin(6)
    bfmt.setBackground(QColor("#ffebee"))   # pale red — "raw LaTeX, careful"
    return bfmt


def _typed_stub_char_format(color_hex: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont("Consolas"); f.setStyleHint(QFont.Monospace); f.setPointSize(10)
    fmt.setFont(f); fmt.setForeground(QColor(color_hex))
    return fmt


# ---- Insert dialogs (consolidated) ------------------------------------

class _InsertFigureDialog(QDialog):
    """Single dialog for inserting a figure: path, caption, label."""

    def __init__(self, parent=None, *, path_value: str = "",
                 path_readonly: bool = False,
                 title: str = "Insert figure"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        form = QFormLayout()

        # Path row with browse button.
        path_row = QHBoxLayout()
        self._path = QLineEdit(path_value)
        self._path.setReadOnly(path_readonly)
        path_row.addWidget(self._path, 1)
        if not path_readonly:
            browse = QPushButton("Browse...")
            browse.clicked.connect(self._browse)
            path_row.addWidget(browse)
        form.addRow("Image path:", path_row)

        self._caption = QLineEdit()
        form.addRow("Caption:", self._caption)

        self._label = QLineEdit()
        self._label.setPlaceholderText("e.g. fig:my-figure")
        form.addRow("Label:", self._label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select image",
            filter="Images (*.png *.jpg *.jpeg *.pdf *.eps *.svg);;All (*)")
        if path:
            self._path.setText(path)

    def path(self) -> str:
        return self._path.text().strip()

    def caption(self) -> str:
        return self._caption.text().strip()

    def label(self) -> str:
        return self._label.text().strip()


class _InsertTableDialog(QDialog):
    """Single dialog for inserting a table: rows, columns, caption, label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert table")
        self.setMinimumWidth(320)
        form = QFormLayout()

        self._rows = QSpinBox()
        self._rows.setRange(1, 50)
        self._rows.setValue(3)
        form.addRow("Rows:", self._rows)

        self._cols = QSpinBox()
        self._cols.setRange(1, 20)
        self._cols.setValue(3)
        form.addRow("Columns:", self._cols)

        self._caption = QLineEdit()
        form.addRow("Caption:", self._caption)

        self._label = QLineEdit()
        self._label.setPlaceholderText("e.g. tab:my-table")
        form.addRow("Label:", self._label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def dimensions(self) -> tuple[int, int]:
        return self._rows.value(), self._cols.value()

    def caption(self) -> str:
        return self._caption.text().strip()

    def label(self) -> str:
        return self._label.text().strip()


class DocumentEditor(QWidget):
    """Rich-text editor that maintains a bidirectional binding with Document."""

    documentChanged = Signal()  # debounced after the user stops typing
    zoomChanged = Signal(int)   # emitted when fit-to-width recalculates zoom
    documentDropped = Signal(str)  # file path dropped onto the editor

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._building = False
        # Initialise meta up front — _apply_page_size below reads it.
        self._meta = DocMeta()
        self._heading_offset: list[int] = [0] * 6
        # Zoom state: tracked so set_zoom_percent can compute deltas.
        self._base_font_pt = 12
        self._body_font_pt = 12   # user-controllable body text size
        self._zoom_percent = 100
        self._zoom_delta = 0
        self._fit_to_width = True
        # Current colour theme. Block formats for tables / figures
        # / raw blocks read this when constructing their palettes so
        # the cells stay readable against the editor's dark / light
        # page background.
        self._dark = False

        # MS Word look: a white "page" card centered on a grey desk, sized
        # to real A4/Letter/Legal paper at 96 DPI. The text flows as one
        # editable surface but page-break lines mark the paginations Latex
        # will produce in the PDF.
        self._visual_font_family = "Georgia"
        self._edit = PagedTextEdit()
        self._edit.setAcceptRichText(False)
        self._edit.image_resizable = (
            lambda fmt: not fmt.property(_P_MATH)
            and self._figure_table_at_image(fmt) is not None)
        self._edit.imageResized.connect(self._on_image_resized)
        self._edit.setFrameShape(QFrame.NoFrame)
        f = QFont(self._visual_font_family); f.setPointSize(12)
        self._edit.setFont(f)
        # ~1 inch of inner padding at 100% zoom; scaled by set_zoom_percent
        # so the number of characters per line stays constant when zooming.
        self._base_doc_margin = 72
        self._edit.document().setDocumentMargin(self._base_doc_margin)
        self._edit.setStyleSheet("QTextEdit { background: white; border: none; }")
        self._edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self._edit.customContextMenuRequested.connect(self._show_context_menu)
        self._edit.installEventFilter(self)
        # Mouse events land on the viewport, not the QTextEdit itself.
        self._edit.viewport().installEventFilter(self)
        self._extra_context_actions: list[tuple[str, object]] = []
        self._in_key_edit = False
        self._edit.document().contentsChange.connect(self._restyle_unstyled)

        self._page = QFrame()
        self._page.setObjectName("page")
        self._page.setStyleSheet(
            "#page { background: white; border: none; }")
        # Sheets draw their own edges and gaps (PagedTextEdit); the card
        # just casts a soft shadow onto the desk.
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self._page)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 70))
        self._page.setGraphicsEffect(shadow)
        page_layout = QVBoxLayout(self._page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(self._edit, 1)
        self._apply_page_size(page_sizes.by_code(self._meta.page_size))
        self._apply_page_layout()

        # Attach the live spell-check highlighter. The class is a
        # graceful no-op when pyspellchecker isn't installed, so this
        # always returns SOMETHING the View > Check spelling toggle
        # can call into.
        from .spellcheck import SpellHighlighter
        self._spell_highlighter = SpellHighlighter(self._edit.document())

        desk = QWidget()
        desk.setObjectName("desk")
        desk.setStyleSheet("#desk { background: #d0d4d8; }")
        # Vertical outer layout anchors the page row to the top of the
        # desk, so the white card sits at the top of the visible area
        # rather than being stretched to fill the entire scroll viewport.
        desk_layout = QVBoxLayout(desk)
        desk_layout.setContentsMargins(0, 24, 0, 32)
        page_row = QHBoxLayout()
        page_row.addStretch(1)
        page_row.addWidget(self._page, 0, Qt.AlignTop)
        page_row.addStretch(1)
        desk_layout.addLayout(page_row)
        desk_layout.addStretch(1)

        self._scroll = QScrollArea(self)
        self._scroll.setWidget(desk)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        # Resize the QTextEdit to its document height so the outer scrollbar
        # is the only one — like a real page in Word that grows downward.
        self._edit.document().documentLayout().documentSizeChanged.connect(
            self._resize_to_document)

        self._fit_debounce = QTimer(self)
        self._fit_debounce.setSingleShot(True)
        self._fit_debounce.setInterval(150)
        self._fit_debounce.timeout.connect(self._apply_fit_to_width)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(450)
        self._debounce.timeout.connect(self._refresh_reference_labels)
        self._debounce.timeout.connect(self.documentChanged)

        self._math_refresh = QTimer(self)
        self._math_refresh.setSingleShot(True)
        self._math_refresh.setInterval(600)
        self._math_refresh.timeout.connect(self._refresh_math_images)

        self._edit.textChanged.connect(self._on_text_changed)

        # Per-session image scratch dir. Pasted clipboard images and dropped
        # image files land here; the figure stub points at the saved path.
        # save_kdocz will bundle them into the archive on Save As .kdocz.
        self._images_dir = Path(tempfile.mkdtemp(prefix="khervedoc-imgs-"))
        self._equations_dir: Path | None = None
        self._doc_dir: Path | None = None
        self._resolver = ReferenceResolver(Document())
        # Full-resolution equation renders by resource URL, kept so zoom
        # changes can re-scale from the original rather than a copy.
        self._math_sources: dict[str, QImage] = {}
        self._edit.set_images_dir(self._images_dir)
        self._edit.imageReceived.connect(self._on_image_received)
        self._edit.documentDropped.connect(self.documentDropped)
        self._source_dir: Path | None = None

    # ---------- public ----------

    @property
    def text_edit(self) -> PagedTextEdit:
        return self._edit

    def cursor_snippet(self, max_chars: int = 30) -> str:
        """Return a short text snippet around the cursor for cross-tab nav."""
        cursor = self._edit.textCursor()
        block = cursor.block()
        text = block.text().strip()
        # Strip object replacement chars and control chars
        text = text.replace("\ufffc", "").replace("\u2028", " ").strip()
        if len(text) > max_chars:
            # Centre the snippet around the cursor position within the block
            pos_in_block = cursor.positionInBlock()
            start = max(0, pos_in_block - max_chars // 2)
            text = text[start:start + max_chars]
        return text

    def scroll_to_snippet(self, snippet: str) -> bool:
        """Find *snippet* in the document and scroll to it. Returns True
        if found."""
        if not snippet:
            return False
        doc = self._edit.document()
        cursor = doc.find(snippet)
        if cursor.isNull():
            return False
        self._edit.setTextCursor(cursor)
        self._edit.centerCursor()
        return True

    def set_source_dir(self, path: Path | None) -> None:
        self._source_dir = path

    def set_document_dir(self, doc_dir: Path) -> None:
        """Point image storage at permanent subdirs next to the document.

        Creates ``equations/`` and ``figures/`` folders under *doc_dir*
        and migrates any images that were in the previous temp dirs."""
        import shutil

        eq_dir = doc_dir / "equations"
        fig_dir = doc_dir / "figures"
        eq_dir.mkdir(exist_ok=True)
        fig_dir.mkdir(exist_ok=True)

        # Migrate existing equation PNGs
        old_eq = self._equations_dir or _math_tmp_dir
        if old_eq and old_eq.exists() and old_eq != eq_dir:
            for f in old_eq.glob("math_*.png"):
                dest = eq_dir / f.name
                if not dest.exists():
                    shutil.copy2(f, dest)

        # Migrate existing figure images
        old_fig = self._images_dir
        if old_fig.exists() and old_fig != fig_dir:
            for f in old_fig.iterdir():
                if f.is_file():
                    dest = fig_dir / f.name
                    if not dest.exists():
                        shutil.copy2(f, dest)

        self._equations_dir = eq_dir
        self._doc_dir = doc_dir
        self._images_dir = fig_dir
        self._edit.set_images_dir(fig_dir)

        # Update cached math paths so they point at the new location
        for latex_key, old_path in list(_MATH_IMAGE_CACHE.items()):
            if old_path is None:
                continue
            new_path = eq_dir / old_path.name
            if new_path.exists():
                _MATH_IMAGE_CACHE[latex_key] = new_path

    def cleanup_orphaned_equations(self, doc: "Document") -> None:
        """Delete equation PNGs that no longer belong to any MathBlock."""
        eq_dir = self._equations_dir
        if eq_dir is None or not eq_dir.exists():
            return
        live: set[str] = set()
        def _collect(blocks):
            for block in blocks:
                if isinstance(block, MathBlock):
                    h = _hashlib.md5(block.latex.encode()).hexdigest()[:12]
                    live.add(f"math_{h}.png")
                elif isinstance(block, Section):
                    _collect(block.children)
        _collect(doc.children)
        for f in eq_dir.glob("math_*.png"):
            if f.name not in live:
                f.unlink(missing_ok=True)
                for k, v in list(_MATH_IMAGE_CACHE.items()):
                    if v == f:
                        del _MATH_IMAGE_CACHE[k]

    def meta(self) -> DocMeta:
        return self._meta

    def set_meta(self, meta: DocMeta) -> None:
        prev_size = self._meta.page_size if self._meta else None
        prev_vfont = self._visual_font_family
        self._meta = meta
        if meta.page_size != prev_size:
            self._apply_page_size(page_sizes.by_code(meta.page_size))
        if screen_font_for(meta) != prev_vfont:
            self._apply_visual_font(screen_font_for(meta))
        self._apply_page_layout()
        self._on_text_changed()

    def set_page_size(self, code: str) -> None:
        self._meta.page_size = code
        self._apply_page_size(page_sizes.by_code(code))
        self._apply_page_layout()
        self._resize_figure_images()
        self._on_text_changed()

    def _apply_visual_font(self, family: str) -> None:
        """Switch the visual editor's body font to *family*, updating
        all existing Paragraph blocks so the change is immediate."""
        self._visual_font_family = family
        f = QFont(family)
        f.setPointSize(self._body_font_pt)
        self._edit.setFont(f)
        self._building = True
        try:
            doc = self._edit.document()
            block = doc.firstBlock()
            zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
            c = QTextCursor(block)
            c.beginEditBlock()
            while block.isValid():
                state = block.userState()
                if state in (0, -1):
                    bc = QTextCursor(block)
                    bc.select(QTextCursor.BlockUnderCursor)
                    fmt = bc.charFormat()
                    bf = fmt.font()
                    bf.setFamily(family)
                    fmt.setFont(bf)
                    bc.setCharFormat(fmt)
                block = block.next()
            c.endEditBlock()
        finally:
            self._building = False

    def _apply_page_size(self, page: "page_sizes.PageSize") -> None:
        # Honour the current zoom so switching page sizes while zoomed in
        # doesn't snap the card back to 100%.
        scale = self._zoom_percent / 100 if self._zoom_percent else 1.0
        w = round(page.width_px * scale)
        h = round(page.height_px * scale)
        self._page.setFixedWidth(w)
        self._edit.set_page_size_px(w, h)
        self._resize_to_document()

    def _resize_to_document(self, size=None) -> None:
        """Size the editor to its whole pages. The document is laid out
        paginated (PagedTextEdit), so its height is a whole number of
        sheets: a new document shows one full, empty A4 page, and a new
        sheet appears as soon as text flows onto it."""
        self._edit._apply_pagination()
        page_h = self._edit.page_height_px()
        if page_h > 0:
            total_h = page_h * self._edit.sheet_count()
        else:
            total_h = max(int(self._edit.document().size().height()), 240)
        self._edit.setMinimumHeight(total_h)
        self._edit.setMaximumHeight(total_h)
        # The page frame also needs explicit height clamps; without these
        # the QHBoxLayout that centres it would stretch the frame to fill
        # the available vertical space, painting white below the text.
        self._page.setMinimumHeight(total_h)
        self._page.setMaximumHeight(total_h)

    def set_document(self, doc: Document) -> None:
        self._building = True
        try:
            self._meta = doc.meta
            if screen_font_for(doc.meta) != self._visual_font_family:
                self._visual_font_family = screen_font_for(doc.meta)
                f = QFont(self._visual_font_family)
                f.setPointSize(self._body_font_pt)
                self._edit.setFont(f)
            self._resolver = ReferenceResolver(doc, self._doc_dir)
            self._edit.clear()
            cursor = self._edit.textCursor()
            cursor.movePosition(QTextCursor.Start)

            first = True
            for block in doc.children:
                if not first:
                    cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
                first = False
                self._render_block(cursor, block)
            self._apply_page_layout()
            # Clearing the editor reset the page margins, so figures were
            # sized against the wrong text width while being inserted.
            self._resize_figure_images()
            # A freshly loaded document has nothing unsaved; MCP tools
            # read this before discarding it.
            self._edit.document().setModified(False)
        finally:
            self._building = False
        self.documentChanged.emit()

    def insert_blocks(self, blocks: list) -> None:
        """Insert model *blocks* at the current cursor as real, editable
        content — the write path used by the AI assistant.

        Unlike `set_document`, this does not clear the document and does
        not suppress change signals: the insertion registers as a normal
        user edit (one undo step, marks the document dirty, retriggers the
        preview). Each block is rendered with the same `_render_block`
        machinery `set_document` uses, so sections, math, lists, tables
        and raw LaTeX all come out identical to typed content.
        """
        if not blocks:
            return
        cursor = self._edit.textCursor()
        cursor.beginEditBlock()
        first = True
        for block in blocks:
            # Start a fresh paragraph before the first block only when the
            # cursor sits in a non-empty block, so inserting into an empty
            # document (or an empty trailing line) doesn't leave a blank
            # line above the inserted content.
            if not first or cursor.block().text().strip():
                cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
            first = False
            self._render_block(cursor, block)
        cursor.endEditBlock()
        self._apply_page_layout()
        self._edit.setTextCursor(cursor)
        self._edit.ensureCursorVisible()

    def replace_body(self, blocks: list) -> None:
        """Replace the whole document body with *blocks* in a single undoable
        edit — the rewrite path used by the AI assistant to move, delete,
        reorder or rewrite existing content.

        Leading Title / Author blocks are preserved (they carry the
        document's front-matter identity and aren't part of the body the
        assistant reasons about), and `meta` is untouched. Everything else
        is discarded and rebuilt from *blocks*, so an AI reordering — e.g.
        moving a Conclusion above Availability, or de-duplicating a repeated
        section — takes effect wholesale rather than appending.
        """
        preserved = [b for b in self.get_document().children
                     if isinstance(b, (Title, Author))]
        cursor = self._edit.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.removeSelectedText()
        first = True
        for block in preserved + list(blocks):
            if not first:
                cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
            first = False
            self._render_block(cursor, block)
        cursor.endEditBlock()
        self._apply_page_layout()
        cursor.movePosition(QTextCursor.Start)
        self._edit.setTextCursor(cursor)
        self._edit.ensureCursorVisible()

    def get_document(self) -> Document:
        qdoc = self._edit.document()
        blocks: list = []
        # QTextLists span multiple QTextBlocks. We coalesce them.
        seen_lists: dict[int, list] = {}
        seen_tables: set[int] = set()
        block = qdoc.firstBlock()
        while block.isValid():
            # Detect QTextTable frames — all blocks inside a table belong
            # to the same QTextTable object. We extract the whole table on
            # the first block we encounter and skip the rest.
            cursor = QTextCursor(block)
            qtable = cursor.currentTable()
            if qtable is not None:
                tid = id(qtable)
                if tid not in seen_tables:
                    seen_tables.add(tid)
                    tfmt = qtable.format()
                    if tfmt.property(_P_IS_FIGURE):
                        blocks.append(self._figure_from_qtexttable(qtable))
                    else:
                        blocks.append(self._table_from_qtexttable(qtable))
                block = block.next()
                continue

            text_list = block.textList()
            if text_list is not None:
                tl_id = id(text_list)
                if tl_id not in seen_lists:
                    ordered = text_list.format().style() in (
                        QTextListFormat.ListDecimal, QTextListFormat.ListLowerAlpha,
                        QTextListFormat.ListUpperAlpha, QTextListFormat.ListLowerRoman,
                        QTextListFormat.ListUpperRoman,
                    )
                    node = ListNode(ordered=ordered, items=[])
                    seen_lists[tl_id] = node
                    blocks.append(node)
                seen_lists[tl_id].items.append(
                    ListItem(children=self._inlines_from_block(block))
                )
            else:
                state = block.userState()
                text = block.text()
                if state == _STATE_MATH_BLOCK:
                    raw = text.replace("\ufffc", "").replace(_MATH_SEP, "").strip(_LINE_SEP).strip()
                    bf = block.blockFormat()
                    blocks.append(MathBlock(
                        latex=raw.replace(_LINE_SEP, "\n"),
                        numbered=bool(bf.property(_P_MATH_NUMBERED)),
                        label=bf.property(_P_MATH_LABEL) or None))
                elif state == _STATE_FIGURE:
                    blocks.append(self._figure_from_stub(text))
                elif state == _STATE_TABLE:
                    # Legacy stub-based tables (from older documents).
                    blocks.append(self._table_from_stub(text))
                elif state == _STATE_RAW:
                    # figure*/table* blocks store the original LaTeX in
                    # a block-format property because the visible text is
                    # a compact summary, not the real source.
                    stored = block.blockFormat().property(_P_RAW_BLOCK)
                    if stored:
                        blocks.append(RawLatex(text=stored))
                    else:
                        # Strip whichever prefix is present; supports
                        # documents saved before the typed prefixes existed.
                        raw = text
                        for prefix in _RAW_PREFIXES:
                            if raw.startswith(prefix):
                                raw = raw[len(prefix):]
                                break
                        # Restore the real newlines we substituted on render
                        # so the LaTeX serializer emits a well-formed verbatim
                        # / lstlisting / etc. environment.
                        raw = raw.replace(_LINE_SEP, "\n")
                        blocks.append(RawLatex(text=raw))
                else:
                    # Text blocks: determine the paragraph style from how
                    # the block CURRENTLY looks, not the stored state.
                    # When a user presses Enter after a heading the new
                    # block inherits the heading's font but its state
                    # stays unset (-1), and vice versa for manual format
                    # changes. Trusting the visible formatting keeps the
                    # PDF in sync with what the user sees on screen.
                    blocks.append(self._classify_text_block(block))
            block = block.next()
        return Document(children=blocks, meta=self._meta)

    # ---------- block rendering ----------

    def _render_block(self, cursor: QTextCursor, block) -> None:
        if isinstance(block, Title):
            cursor.setBlockFormat(_title_block_format())
            cursor.block().setUserState(_STATE_TITLE)
            for inline in block.children:
                self._insert_inline(cursor, inline, base_format=self._title_fmt())
            return
        if isinstance(block, Author):
            cursor.setBlockFormat(_author_block_format())
            cursor.block().setUserState(_STATE_AUTHOR)
            for inline in block.children:
                self._insert_inline(cursor, inline, base_format=self._title_block_fmt(-2))
            return
        if isinstance(block, (Affiliation, Correspondence)):
            corr = isinstance(block, Correspondence)
            cursor.setBlockFormat(_affiliation_block_format())
            cursor.block().setUserState(
                _STATE_CORRESPONDENCE if corr else _STATE_AFFILIATION)
            for inline in block.children:
                self._insert_inline(
                    cursor, inline, base_format=self._title_block_fmt(-8 if corr else -7))
            return
        if isinstance(block, Abstract):
            cursor.setBlockFormat(_abstract_block_format())
            cursor.block().setUserState(_STATE_ABSTRACT)
            for inline in block.children:
                self._insert_inline(cursor, inline, base_format=_abstract_char_format())
            return
        if isinstance(block, Keywords):
            cursor.setBlockFormat(_keywords_block_format())
            cursor.block().setUserState(_STATE_KEYWORDS)
            for inline in block.children:
                self._insert_inline(cursor, inline, base_format=_keywords_char_format())
            return
        if isinstance(block, Frame):
            cursor.block().setUserState(_STATE_FRAME)
            cfmt = _frame_char_format()
            for inline in block.children:
                self._insert_inline(cursor, inline, base_format=cfmt)
            return
        if isinstance(block, Section):
            if block.level == 0:
                state = _STATE_CHAPTER_STAR if not block.numbered else _STATE_CHAPTER
            elif not block.numbered:
                state = _STATE_HEADING_STAR_BASE + block.level
            else:
                state = block.level
            cursor.block().setUserState(state)
            # Headings are always flush left; without this a heading that
            # lands in the first block keeps a removed title's centring.
            hfmt = cursor.blockFormat()
            hfmt.setAlignment(Qt.AlignLeft)
            cursor.setBlockFormat(hfmt)
            cfmt = self._heading_fmt(block.level)
            for inline in block.children:
                self._insert_inline(cursor, inline, base_format=cfmt)
        elif isinstance(block, Paragraph):
            cursor.block().setUserState(_STATE_PARAGRAPH)
            bfmt = QTextBlockFormat()
            bfmt.setAlignment(_QT_ALIGNMENT.get(block.alignment, Qt.AlignLeft))
            cursor.setBlockFormat(bfmt)
            # Pass an explicit body char format so every Text run
            # carries Georgia + body_font_pt as its baseline. Without
            # this, _insert_inline emits Text fragments with an empty
            # font, which inherits whatever the cursor's current font
            # happens to be — which can be the previous block's font
            # (a heading, a code span, the last block of a different
            # body size) and produces visibly mismatched paragraphs
            # when the user presses Enter to start a new one.
            body_fmt = self._body_char_format()
            for inline in block.children:
                self._insert_inline(cursor, inline, base_format=body_fmt)
        elif isinstance(block, MathBlock):
            cursor.block().setUserState(_STATE_MATH_BLOCK)
            bfmt = cursor.blockFormat()
            bfmt.setProperty(_P_MATH_NUMBERED, bool(block.numbered))
            if block.label:
                bfmt.setProperty(_P_MATH_LABEL, block.label)
            bfmt.setAlignment(Qt.AlignHCenter)
            cursor.setBlockFormat(bfmt)
            shown = self._insert_math_image(cursor, block.latex)
            visible = block.latex.replace("\n", _LINE_SEP)
            cursor.insertText(visible, _math_hidden_format() if shown
                              else _math_block_char_format())
        elif isinstance(block, ListNode):
            lfmt = QTextListFormat()
            lfmt.setStyle(QTextListFormat.ListDecimal if block.ordered
                          else QTextListFormat.ListDisc)
            # Capture the QTextList from createList(); cursor.currentList()
            # returns None right after an insertBlock, which crashed the
            # previous implementation on every list with more than one item.
            text_list = None
            for item in block.items:
                if text_list is None:
                    text_list = cursor.createList(lfmt)
                else:
                    cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
                    text_list.add(cursor.block())
                cursor.block().setUserState(_STATE_PARAGRAPH)
                # List items are body text in LaTeX; without an explicit
                # format they fell back to the widget's UI sans font.
                body_fmt = self._body_char_format()
                for inline in item.children:
                    self._insert_inline(cursor, inline, base_format=body_fmt)
        elif isinstance(block, Figure):
            self._insert_figure_widget(cursor, block)
        elif isinstance(block, Table):
            self._insert_table_widget(cursor, block)
        elif isinstance(block, RawLatex):
            cursor.block().setUserState(_STATE_RAW)
            text = block.text
            if "\\begin{lstlisting}" in text or "\\begin{verbatim}" in text:
                cursor.setBlockFormat(_code_block_format())
                color = "#1a3a8c"      # slate / blue
            elif "\\begin{thebibliography}" in text:
                cursor.setBlockFormat(_bibliography_block_format())
                color = "#6a1b9a"      # purple
            else:
                cursor.setBlockFormat(_raw_block_format())
                color = "#b71c1c"      # red
            # For figure*/table* blocks that contain an image, show a
            # preview thumbnail above the raw LaTeX source.
            if ("\\begin{figure*}" in text or "\\begin{table*}" in text):
                inc = _re.search(
                    r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text)
                if inc:
                    self._insert_figure_thumbnail(cursor, inc.group(1))
                    cursor.insertText(_LINE_SEP)
                # Show a compact summary instead of the full LaTeX.
                cap = _re.search(r"\\caption\{", text)
                cap_text = ""
                if cap:
                    from .importers import _consume_braced
                    cap_text, _ = _consume_braced(text, cap.end() - 1)
                    cap_text = _latex_to_display(cap_text or "")
                lab = _re.search(r"\\label\{([^}]*)\}", text)
                env = "figure*" if "\\begin{figure*}" in text else "table*"
                summary = f"[{env}]"
                if cap_text:
                    summary += f" {cap_text}"
                if lab:
                    summary += f"  ({lab.group(1)})"
                cursor.insertText(summary, _typed_stub_char_format("#1565c0"))
                # Store the full original LaTeX on the block so
                # reconstruction recovers the real source, not the
                # compact display summary.
                bfmt = cursor.blockFormat()
                bfmt.setProperty(_P_RAW_BLOCK, text)
                cursor.setBlockFormat(bfmt)
            else:
                visible = text.replace("\n", _LINE_SEP)
                cursor.insertText(visible, _typed_stub_char_format(color))

    # ---------- figure thumbnail ----------

    _THUMB_MAX_WIDTH = 320
    _THUMB_MAX_HEIGHT = 200

    def _insert_figure_thumbnail(self, cursor: QTextCursor, img_path: str) -> None:
        """Try to load the image and insert a scaled thumbnail below the stub."""
        resolved = self._resolve_image_path(img_path)
        if resolved is None:
            return
        img = QImage(str(resolved))
        if img.isNull():
            return
        # Scale to thumbnail size preserving aspect ratio.
        if img.width() > self._THUMB_MAX_WIDTH or img.height() > self._THUMB_MAX_HEIGHT:
            img = img.scaled(
                self._THUMB_MAX_WIDTH, self._THUMB_MAX_HEIGHT,
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
        url = QUrl.fromLocalFile(str(resolved))
        self._edit.document().addResource(2, url, img)  # 2 = ImageResource
        cursor.insertText("\n")
        img_fmt = QTextImageFormat()
        img_fmt.setName(url.toString())
        img_fmt.setWidth(img.width())
        img_fmt.setHeight(img.height())
        cursor.insertImage(img_fmt)

    def _insert_table_widget(self, cursor: QTextCursor, table: Table) -> None:
        """Insert a Table model node as a real QTextTable in the editor,
        drawn the way LaTeX typesets it: horizontal rules only (plus any
        '|' rules from the column spec), natural column widths, caption
        underneath as "Table N: ..."."""
        cursor.beginEditBlock()
        nrows = len(table.rows) if table.rows else 1
        ncols = max((len(r) for r in table.rows), default=1) if table.rows else 1
        number = 1 + self._count_tables_before(cursor.position())
        tfmt = _make_table_format(ncols, dark=self._dark)
        tfmt.setProperty(_P_TABLE_CAPTION, table.caption or "")
        tfmt.setProperty(_P_TABLE_LABEL, table.label or "")
        tfmt.setProperty(_P_TABLE_ALIGNMENT, table.alignment or "")
        tfmt.setProperty(_P_TABLE_STYLE, table.style or "")
        has_caption = bool(table.caption)
        total_rows = nrows + (1 if has_caption else 0)
        qtable = cursor.insertTable(total_rows, ncols, tfmt)
        body = self._body_char_format()
        for r, row in enumerate(table.rows):
            for c in range(ncols):
                cell = qtable.cellAt(r, c)
                raw = row[c] if c < len(row) else ""
                cf = cell.format()
                cf.setProperty(_P_CELL_RAW, raw)
                cell.setFormat(cf)
                fmt = QTextCharFormat(body)
                if "\\textbf{" in raw:
                    fmt.setFontWeight(QFont.Bold)
                if "\\textit{" in raw or "\\emph{" in raw:
                    fmt.setFontItalic(True)
                cell.firstCursorPosition().insertText(
                    _cell_display_text(raw), fmt)
        if has_caption:
            qtable.mergeCells(nrows, 0, 1, ncols)
            cap_cell = qtable.cellAt(nrows, 0)
            cf = cap_cell.format()
            cf.setProperty(_P_CAPTION_ROW, True)
            cap_cell.setFormat(cf)
            cap_cursor = cap_cell.firstCursorPosition()
            bf = cap_cursor.blockFormat()
            bf.setAlignment(Qt.AlignHCenter)
            # A short caption shouldn't wrap inside a narrow table; LaTeX
            # sets it across the text width.
            bf.setNonBreakableLines(len(table.caption) <= 60)
            cap_cursor.setBlockFormat(bf)
            cap_cursor.insertText(
                f"Table {number}: {_cell_display_text(table.caption)}",
                QTextCharFormat(body))
        self._apply_table_rules(qtable)
        # Move the cursor past the table so subsequent content goes after it.
        cursor.movePosition(QTextCursor.End)
        cursor.endEditBlock()

    def _count_tables_before(self, pos: int) -> int:
        n = 0
        for frame in self._edit.document().rootFrame().childFrames():
            if isinstance(frame, QTextTable) and frame.firstPosition() < pos \
                    and not frame.format().property(_P_IS_FIGURE):
                n += 1
        return n

    def _apply_table_rules(self, qtable: QTextTable) -> None:
        """Draw LaTeX's rules on the cells: top / header / bottom
        horizontal rules (heavier outer rules for booktabs) and vertical
        rules where the column spec has '|'. Re-run after row/column
        edits, since the rules depend on which row is first/last."""
        tfmt = qtable.format()
        booktabs = tfmt.property(_P_TABLE_STYLE) == "booktabs"
        ncols = qtable.columns()
        nrows = qtable.rows()
        caption_row = nrows > 1 and bool(
            qtable.cellAt(nrows - 1, 0).format().property(_P_CAPTION_ROW)
            or qtable.cellAt(nrows - 1, 0).firstCursorPosition()
                .block().text().startswith("Caption: "))
        last = nrows - (2 if caption_row else 1)
        aligns, vrules = _parse_column_spec(
            tfmt.property(_P_TABLE_ALIGNMENT) or "", ncols)
        heavy, thin = (1.4, 0.8) if booktabs else (0.8, 0.8)
        black = QBrush(QColor("#000000"))
        none = QTextFrameFormat.BorderStyle_None
        solid = QTextFrameFormat.BorderStyle_Solid
        for r in range(nrows):
            for c in range(ncols):
                cell = qtable.cellAt(r, c)
                cf = cell.format().toTableCellFormat()
                cf.setLeftPadding(8); cf.setRightPadding(8)
                cf.setTopPadding(2); cf.setBottomPadding(2)
                top = heavy if r == 0 else 0
                bottom = (heavy if r == last else
                          thin if r == 0 and last > 0 else 0)
                if r > last:            # caption row: no rules, gap above
                    top = bottom = 0
                    cf.setTopPadding(8)
                left = vrules[c] and r <= last
                right = vrules[c + 1] and r <= last
                for side, width in (("Top", top), ("Bottom", bottom),
                                    ("Left", 0.8 if left else 0),
                                    ("Right", 0.8 if right else 0)):
                    getattr(cf, f"set{side}Border")(width)
                    getattr(cf, f"set{side}BorderBrush")(black)
                    getattr(cf, f"set{side}BorderStyle")(
                        solid if width else none)
                cell.setFormat(cf)
                if r <= last:
                    bc = cell.firstCursorPosition()
                    bf = bc.blockFormat()
                    bf.setAlignment(_CELL_ALIGN[aligns[c]])
                    bc.setBlockFormat(bf)

    def _math_png(self, latex: str, display: bool = True) -> Path | None:
        return _render_math_image(latex, cache_dir=self._equations_dir,
                                  display=display)

    def _add_math_resource(self, url: QUrl, img: QImage) -> tuple[int, int]:
        """Register *img* for *url* pre-scaled to its display size (at the
        screen's pixel ratio) and return that logical size. Qt's own
        scaling of document images is unsmoothed, which made thin strokes
        such as '=' and fraction bars vanish."""
        self._math_sources[url.toString()] = img
        w, h = self._capped_math_size(img)
        dpr = self._edit.devicePixelRatioF() or 1.0
        shown = img.scaled(max(1, round(w * dpr)), max(1, round(h * dpr)),
                           Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        shown.setDevicePixelRatio(dpr)
        self._edit.document().addResource(2, url, shown)
        return w, h

    def _capped_math_size(self, img: QImage) -> tuple[int, int]:
        """Logical size for a math image: its 12pt render scaled to the
        body font and zoom, capped to 90% of the editor viewport."""
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        scale = (96 / _MATH_DPI) * zoom * self._body_font_pt / _MATH_RENDER_PT
        max_w = int(self._edit.text_width_px() * 0.98)
        w, h = round(img.width() * scale), round(img.height() * scale)
        if w > max_w and max_w > 0:
            h = int(h * max_w / w)
            w = max_w
        return w, h

    def _insert_math_image(self, cursor: QTextCursor, latex: str,
                           inline: bool = False) -> bool:
        """Typeset math into the document as a picture, followed by an
        invisible separator; the caller then adds the (hidden) source.
        Returns False if nothing could be rendered, so the caller shows
        the source visibly instead."""
        png_path = self._math_png(latex, display=not inline)
        if png_path is None or not png_path.exists():
            return False
        img = QImage(str(png_path))
        if img.isNull():
            return False
        url = QUrl.fromLocalFile(str(png_path))
        w, h = self._add_math_resource(url, img)
        img_fmt = QTextImageFormat()
        img_fmt.setName(url.toString())
        img_fmt.setWidth(w)
        img_fmt.setHeight(h)
        # Stamp the source onto the picture itself. Without this the image
        # fragment has no back-link to its LaTeX, so a click on the rendered
        # equation can't find it — and get_document() can't tell a math
        # preview apart from an image the user pasted.
        img_fmt.setProperty(_P_MATH, latex)
        img_fmt.setVerticalAlignment(QTextCharFormat.AlignMiddle)
        cursor.insertImage(img_fmt)
        cursor.insertText(_MATH_SEP, _math_hidden_format())
        return True

    def _insert_figure_widget(self, cursor: QTextCursor, figure: Figure) -> None:
        """Insert a Figure model node as a centered QTextTable with image,
        caption, and label rows."""
        cursor.beginEditBlock()
        has_caption = bool(figure.caption)
        has_label = bool(figure.label)
        total_rows = 1 + int(has_caption) + int(has_label)
        p = _palette(self._dark)
        tfmt = _make_figure_table_format(dark=self._dark)
        tfmt.setProperty(_P_FIGURE_PATH, figure.path or "")
        tfmt.setProperty(_P_FIGURE_LABEL, figure.label or "")
        tfmt.setProperty(_P_FIGURE_WIDTH, figure.width or "0.8\\textwidth")
        tfmt.setProperty(_P_FIGURE_SOURCE, figure.source or "")
        qtable = cursor.insertTable(total_rows, 1, tfmt)
        # Row 0: centered image.
        img_cursor = qtable.cellAt(0, 0).firstCursorPosition()
        bf = img_cursor.blockFormat()
        bf.setAlignment(Qt.AlignHCenter)
        img_cursor.setBlockFormat(bf)
        resolved = self._resolve_image_path(figure.path)
        if resolved is not None:
            img = QImage(str(resolved))
            if not img.isNull():
                url = QUrl.fromLocalFile(str(resolved))
                self._edit.document().addResource(2, url, img)
                w, h = self._figure_display_size(
                    figure.width or "0.8\\textwidth", img)
                img_fmt = QTextImageFormat()
                img_fmt.setName(url.toString())
                img_fmt.setWidth(w)
                img_fmt.setHeight(h)
                img_cursor.insertImage(img_fmt)
            else:
                img_cursor.insertText(
                    f"[Image not found: {figure.path}]",
                    _typed_stub_char_format("#999999"))
        else:
            img_cursor.insertText(
                f"[Image: {figure.path}]",
                _typed_stub_char_format("#999999"))
        # Row 1: caption (if present).
        row_idx = 1
        if has_caption:
            cap_cursor = qtable.cellAt(row_idx, 0).firstCursorPosition()
            bf = cap_cursor.blockFormat()
            bf.setAlignment(Qt.AlignHCenter)
            cap_cursor.setBlockFormat(bf)
            cap_fmt = QTextCharFormat()
            cap_fmt.setFontItalic(True)
            cap_fmt.setForeground(QColor(p["figure_caption_fg"]))
            cap_cursor.insertText(f"Figure: {figure.caption}", cap_fmt)
            row_idx += 1
        # Row 2: label (if present).
        if has_label:
            lbl_cursor = qtable.cellAt(row_idx, 0).firstCursorPosition()
            bf = lbl_cursor.blockFormat()
            bf.setAlignment(Qt.AlignHCenter)
            lbl_cursor.setBlockFormat(bf)
            lbl_fmt = QTextCharFormat()
            lbl_fmt.setForeground(QColor(p["table_caption_fg"]))
            f = lbl_fmt.font(); f.setPointSize(9); lbl_fmt.setFont(f)
            lbl_cursor.insertText(f"Label: {figure.label}", lbl_fmt)
        cursor.movePosition(QTextCursor.End)
        cursor.endEditBlock()

    def _figure_display_size(self, width_spec: str,
                             img: QImage) -> tuple[float, float]:
        """On-screen size of a figure image from its LaTeX width
        (0.6\\textwidth, 8cm, 3in...), so the page shows it as wide as the
        PDF will. The old fixed 400x300 box ignored the width entirely."""
        text_w = self._edit.text_width_px()
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        spec = (width_spec or "").strip()
        m = _re.match(r"([\d.]*)\s*\\(textwidth|linewidth|columnwidth|hsize)",
                      spec)
        u = _re.match(r"([\d.]+)\s*(cm|mm|in|pt|bp|px)$", spec)
        if m:
            w = float(m.group(1) or 1) * text_w
        elif u:
            per = {"cm": 96 / 2.54, "mm": 96 / 25.4, "in": 96.0,
                   "pt": 96 / 72.27, "bp": 96 / 72, "px": 1.0}[u.group(2)]
            w = float(u.group(1)) * per * zoom
        else:
            w = 0.8 * text_w
        w = max(16.0, min(w, text_w))
        aspect = img.height() / img.width() if img.width() else 0.75
        return w, w * aspect

    def _resize_figure_images(self) -> None:
        """Re-fit figure images to their LaTeX width after zoom, page
        size or column changes."""
        doc = self._edit.document()
        was_building = self._building
        self._building = True
        edit = QTextCursor(doc)
        edit.joinPreviousEditBlock()
        try:
            for frame in doc.rootFrame().childFrames():
                if not isinstance(frame, QTextTable):
                    continue
                spec = frame.format().property(_P_FIGURE_WIDTH)
                if spec is None:
                    continue
                c = frame.cellAt(0, 0).firstCursorPosition()
                c.movePosition(QTextCursor.NextCharacter,
                               QTextCursor.KeepAnchor)
                fmt = c.charFormat()
                if not fmt.isImageFormat():
                    continue
                img_fmt = fmt.toImageFormat()
                img = doc.resource(2, QUrl(img_fmt.name()))
                if not isinstance(img, QImage) or img.isNull():
                    continue
                w, h = self._figure_display_size(spec, img)
                if abs(img_fmt.width() - w) > 0.5:
                    img_fmt.setWidth(w)
                    img_fmt.setHeight(h)
                    c.setCharFormat(img_fmt)
        finally:
            edit.endEditBlock()
            self._building = was_building

    def _figure_table_at_image(self, fmt) -> "QTextTable | None":
        name = fmt.toImageFormat().name()
        for frame in self._edit.document().rootFrame().childFrames():
            if isinstance(frame, QTextTable) and frame.format().property(
                    _P_FIGURE_PATH) is not None:
                c = frame.cellAt(0, 0).firstCursorPosition()
                c.movePosition(QTextCursor.NextCharacter,
                               QTextCursor.KeepAnchor)
                if c.charFormat().isImageFormat() and \
                        c.charFormat().toImageFormat().name() == name:
                    return frame
        return None

    def _on_image_resized(self, pos: int, w: float, h: float) -> None:
        """Mouse resize finished: record the new width on the figure as a
        fraction of the text width, which the LaTeX output then uses."""
        cur = QTextCursor(self._edit.document())
        cur.setPosition(pos)
        table = cur.currentTable()
        if table is None or table.format().property(_P_FIGURE_PATH) is None:
            return
        text_w = self._edit.text_width_px()
        frac = max(0.05, min(1.0, w / text_w)) if text_w > 0 else 0.8
        tfmt = table.format()
        tfmt.setProperty(_P_FIGURE_WIDTH, f"{frac:.2f}\\textwidth")
        table.setFormat(tfmt)
        self._on_text_changed()

    def _figure_from_qtexttable(self, qtable: QTextTable) -> Figure:
        """Read a Figure model back from its QTextTable representation."""
        tfmt = qtable.format()
        path = tfmt.property(_P_FIGURE_PATH) or ""
        label = tfmt.property(_P_FIGURE_LABEL) or None
        width = tfmt.property(_P_FIGURE_WIDTH) or "0.8\\textwidth"
        source = tfmt.property(_P_FIGURE_SOURCE) or ""
        caption = ""
        # Caption is in a row after the image row; look for "Figure: " prefix.
        for r in range(1, qtable.rows()):
            cell_text = qtable.cellAt(r, 0).firstCursorPosition().block().text()
            if cell_text.startswith("Figure: "):
                caption = cell_text[len("Figure: "):]
                break
        return Figure(path=path, caption=caption, label=label or None,
                      width=width, source=source)

    def _resolve_image_path(self, img_path: str) -> Path | None:
        """Resolve a figure path to an absolute file, checking common bases."""
        if not img_path:
            return None
        p = Path(img_path)
        if p.is_absolute() and p.exists():
            return p
        # Try relative to source dir.
        if self._source_dir:
            candidate = self._source_dir / p
            if candidate.exists():
                return candidate
        # Try relative to images scratch dir.
        candidate = self._images_dir / p
        if candidate.exists():
            return candidate
        return None

    # ---------- inline rendering ----------

    def _insert_inline(self, cursor: QTextCursor, node,
                       base_format: QTextCharFormat | None = None) -> None:
        if isinstance(node, Text):
            fmt = QTextCharFormat(base_format) if base_format else QTextCharFormat()
            f = fmt.font()
            if "bold" in node.marks: f.setBold(True)
            if "italic" in node.marks: f.setItalic(True)
            if "underline" in node.marks: f.setUnderline(True)
            if "strikethrough" in node.marks: f.setStrikeOut(True)
            if "smallcaps" in node.marks: f.setCapitalization(QFont.SmallCaps)
            if "code" in node.marks:
                f.setFamily("Consolas"); f.setStyleHint(QFont.Monospace)
            fmt.setFont(f)
            if "subscript" in node.marks:
                fmt.setVerticalAlignment(QTextCharFormat.AlignSubScript)
            elif "superscript" in node.marks:
                fmt.setVerticalAlignment(QTextCharFormat.AlignSuperScript)
            cursor.insertText(node.text, fmt)
        elif isinstance(node, MathInline):
            # Complex inline math (fractions, multi-line, etc.) gets a
            # rendered image like MathBlock; simple expressions stay as
            # styled text so they flow naturally with the paragraph.
            shown = self._insert_math_image(cursor, node.latex, inline=True)
            cursor.insertText(node.latex,
                              _math_hidden_format(node.latex) if shown
                              else _math_inline_format(node.latex))
        elif isinstance(node, Link):
            text = "".join(c.text for c in node.children if isinstance(c, Text)) or node.url
            cursor.insertText(text, _link_format(node.url))
        elif isinstance(node, Footnote):
            text = "".join(c.text for c in node.children if isinstance(c, Text)) or "footnote"
            cursor.insertText(text, _footnote_format(text))
        elif isinstance(node, Citation):
            payload = f"{','.join(node.keys)}|{node.style}"
            display = self._resolver.cite_text(node.keys, node.style)
            cursor.insertText(display, _citation_format(payload))
        elif isinstance(node, CrossRef):
            payload = f"{node.label}|{node.kind}"
            display = self._resolver.ref_text(node.label, node.kind)
            cursor.insertText(display, _crossref_format(payload))
        elif isinstance(node, InlineRaw):
            # A \\ break should LOOK like a break (titles imported with
            # "...Editor\\with..." showed literal backslashes mid-line).
            # U+2028 breaks the line inside the same QTextBlock while the
            # format property still carries "\\", so the round-trip
            # re-emits the LaTeX break unchanged.
            display = "\u2028" if node.latex == "\\\\" else node.latex
            cursor.insertText(display, _raw_inline_format(node.latex))
        elif isinstance(node, Highlight):
            fmt = _highlight_format(node.color)
            for child in node.children:
                if isinstance(child, Text):
                    child_fmt = QTextCharFormat(fmt)
                    f = child_fmt.font()
                    if "bold" in child.marks: f.setBold(True)
                    if "italic" in child.marks: f.setItalic(True)
                    if "underline" in child.marks: f.setUnderline(True)
                    if "strikethrough" in child.marks: f.setStrikeOut(True)
                    if "smallcaps" in child.marks: f.setCapitalization(QFont.SmallCaps)
                    if "code" in child.marks:
                        f.setFamily("Consolas"); f.setStyleHint(QFont.Monospace)
                    child_fmt.setFont(f)
                    cursor.insertText(child.text, child_fmt)
                else:
                    self._insert_inline(cursor, child, fmt)
        elif isinstance(node, Comment):
            fmt = _comment_format(node.note, node.author,
                                  node.timestamp, node.resolved)
            for child in node.children:
                if isinstance(child, Text):
                    child_fmt = QTextCharFormat(fmt)
                    f = child_fmt.font()
                    if "bold" in child.marks: f.setBold(True)
                    if "italic" in child.marks: f.setItalic(True)
                    child_fmt.setFont(f)
                    cursor.insertText(child.text, child_fmt)
                else:
                    self._insert_inline(cursor, child, fmt)

    # ---------- model rebuilding ----------

    def _inlines_from_block(self, block) -> list:
        out: list = []
        it = block.begin()
        # A complex inline MathInline is three fragments: the rendered
        # preview image, a U+2028 separator, then the LaTeX text. Only the
        # last carries the content — emitting the other two would leak
        # U+FFFC and U+2028 straight into the serialized LaTeX.
        after_math_image = False
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                fmt = frag.charFormat()
                text = frag.text()
                if fmt.isImageFormat() and fmt.property(_P_MATH):
                    after_math_image = True
                    it += 1
                    continue
                if after_math_image and text in (_LINE_SEP, _MATH_SEP):
                    after_math_image = False
                    it += 1
                    continue
                after_math_image = False
                if fmt.property(_P_MATH):
                    out.append(MathInline(latex=text))
                elif fmt.property(_P_LINK):
                    out.append(Link(url=fmt.property(_P_LINK), children=[Text(text=text)]))
                elif fmt.property(_P_FOOTNOTE):
                    out.append(Footnote(children=[Text(text=fmt.property(_P_FOOTNOTE))]))
                elif fmt.property(_P_CITATION):
                    raw = fmt.property(_P_CITATION)
                    keys, _, style = raw.partition("|")
                    out.append(Citation(keys=[k for k in keys.split(",") if k],
                                        style=style or "cite"))
                elif fmt.property(_P_CROSSREF):
                    raw = fmt.property(_P_CROSSREF)
                    label, _, kind = raw.partition("|")
                    out.append(CrossRef(label=label, kind=kind or "ref"))
                elif fmt.property(_P_RAW):
                    out.append(InlineRaw(latex=fmt.property(_P_RAW)))
                elif fmt.property(_P_HIGHLIGHT):
                    color = fmt.property(_P_HIGHLIGHT)
                    marks: list = []
                    f = fmt.font()
                    if f.bold(): marks.append("bold")
                    if f.italic(): marks.append("italic")
                    if f.underline(): marks.append("underline")
                    if f.strikeOut(): marks.append("strikethrough")
                    if f.capitalization() == QFont.SmallCaps: marks.append("smallcaps")
                    if f.styleHint() == QFont.Monospace and f.family().lower() == "consolas":
                        marks.append("code")
                    out.append(Highlight(
                        children=[Text(text=text, marks=marks)],
                        color=color,
                    ))
                elif fmt.property(_P_COMMENT):
                    raw = fmt.property(_P_COMMENT)
                    parts = raw.split("|")
                    note = parts[0] if len(parts) > 0 else ""
                    author = parts[1] if len(parts) > 1 else ""
                    timestamp = parts[2] if len(parts) > 2 else ""
                    resolved = (parts[3] == "1") if len(parts) > 3 else False
                    out.append(Comment(
                        children=[Text(text=text)],
                        note=note,
                        author=author,
                        timestamp=timestamp,
                        resolved=resolved,
                    ))
                else:
                    marks: list = []
                    f = fmt.font()
                    if f.bold(): marks.append("bold")
                    if f.italic(): marks.append("italic")
                    if f.underline(): marks.append("underline")
                    if f.strikeOut(): marks.append("strikethrough")
                    if f.capitalization() == QFont.SmallCaps: marks.append("smallcaps")
                    if f.styleHint() == QFont.Monospace and f.family().lower() == "consolas":
                        marks.append("code")
                    va = fmt.verticalAlignment()
                    if va == QTextCharFormat.AlignSubScript: marks.append("subscript")
                    elif va == QTextCharFormat.AlignSuperScript: marks.append("superscript")
                    out.append(Text(text=text, marks=marks))
            it += 1
        return out

    @staticmethod
    def _strip_implicit_marks(children: list, marks: list[str]) -> list:
        """Remove marks that are *implied* by the surrounding paragraph
        style (e.g. Headings are bold by definition, so a Heading's child
        Text shouldn't also carry a "bold" mark — otherwise the serializer
        would wrap it in `\\textbf{...}` and the next reparse would see
        literal LaTeX text).
        """
        for c in children:
            if isinstance(c, Text) and c.marks:
                c.marks = [m for m in c.marks if m not in marks]
        return children

    def _classify_text_block(self, block):
        """Build the right Block model for `block` based on what it LOOKS
        like in the editor right now: alignment, font weight, font size,
        italic. The stored userState is used as a tie-breaker only.

        Heuristics tuned to the styles applied by apply_heading():
          * Title      = centered, bold, ≥ ~24pt (base size, pre-zoom)
          * Author     = centered, italic, ~14pt
          * Heading N  = bold, point size within ~3pt of the canonical size
          * Paragraph  = anything else, alignment preserved
        """
        state = block.userState()
        align_flag = block.blockFormat().alignment() & Qt.AlignHorizontal_Mask
        align_name = _ALIGNMENT_FROM_QT.get(align_flag, "justify")
        children = self._inlines_from_block(block)

        # State-driven dispatch for paragraph styles that aren't visually
        # distinguishable from Body (Abstract / Keywords share the body
        # font and only differ by indentation/italic).
        if state == _STATE_TITLE:
            return Title(children=children)
        if state == _STATE_AUTHOR:
            return Author(children=children)
        if state == _STATE_AFFILIATION:
            return Affiliation(
                children=self._strip_implicit_marks(children, ["italic"]))
        if state == _STATE_CORRESPONDENCE:
            return Correspondence(children=children)
        if state == _STATE_ABSTRACT:
            return Abstract(children=children)
        if state == _STATE_KEYWORDS:
            # Italic is implied by the Keywords style.
            return Keywords(children=self._strip_implicit_marks(children, ["italic"]))
        if state == _STATE_CHAPTER:
            return Section(level=0, children=self._strip_implicit_marks(children, ["bold"]))
        if state == _STATE_CHAPTER_STAR:
            return Section(level=0, numbered=False,
                           children=self._strip_implicit_marks(children, ["bold"]))
        if state == _STATE_FRAME:
            return Frame(children=self._strip_implicit_marks(children, ["bold"]))
        if _STATE_HEADING_STAR_BASE < state <= _STATE_HEADING_STAR_BASE + 5:
            level = state - _STATE_HEADING_STAR_BASE
            return Section(level=level, numbered=False,
                           children=self._strip_implicit_marks(children, ["bold"]))
        if 1 <= state <= 5:
            return Section(level=state,
                           children=self._strip_implicit_marks(children, ["bold"]))

        # Empty block: no fragments to inspect — fall back to state.
        it = block.begin()
        if it.atEnd():
            if state == _STATE_TITLE: return Title(children=children)
            if state == _STATE_AUTHOR: return Author(children=children)
            return Paragraph(children=children, alignment=align_name)

        # Note: bold/italic that come from the *style itself* are stripped
        # below; user-applied bold/italic ON TOP of the style is still kept
        # because it would have been recorded in the QTextCharFormat as
        # explicit weight / italic above the style's defaults.

        fmt = it.fragment().charFormat()
        f = fmt.font()
        size = f.pointSizeF()
        bold = f.bold()
        italic = f.italic()
        # Normalise by zoom so heading detection survives the user dragging
        # the zoom slider.
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        base = size / zoom if zoom > 0 else size

        # Title: large + bold + centered (with state hint relaxes the size threshold).
        body = float(self._body_font_pt)
        if align_flag == Qt.AlignHCenter and bold and (
                base >= body * 1.6 or state == _STATE_TITLE):
            return Title(children=self._strip_implicit_marks(children, ["bold"]))

        # Author: centered, italic, small-ish.
        if align_flag == Qt.AlignHCenter and italic and (base <= 17 or state == _STATE_AUTHOR):
            return Author(children=self._strip_implicit_marks(children, ["italic"]))

        # Heading guessed from size — only for blocks with no stored
        # style (pasted content), and only when visibly larger than body
        # text: a paragraph whose first word is bold must stay a
        # paragraph, not turn into a \subparagraph.
        if state == -1 and bold and base > body * 1.1:
            best_level: int | None = None
            best_diff = 99.0
            for level in (0, 1, 2):
                d = abs(base - body * _HEADING_SCALE[level])
                if d < best_diff:
                    best_diff = d; best_level = level
            if best_level is not None and best_diff < body * 0.25:
                return Section(level=best_level,
                               children=self._strip_implicit_marks(children, ["bold"]))

        return Paragraph(children=children, alignment=align_name)

    def _alignment_of(self, block) -> str:
        # QTextBlockFormat.alignment() returns a Qt.AlignmentFlag bitmask;
        # mask to the horizontal portion before looking up.
        horiz = block.blockFormat().alignment() & Qt.AlignHorizontal_Mask
        for flag, name in _ALIGNMENT_FROM_QT.items():
            if horiz == flag:
                return name
        return "left"

    def _figure_from_stub(self, text: str) -> Figure:
        # Strip the trailing image object char (U+FFFC) Qt inserts for
        # the thumbnail and any trailing newlines.
        body = text.rstrip("\n\ufffc")
        # Legacy format: "[FIGURE] path | caption | label | width".
        if body.startswith(_FIGURE_PREFIX):
            legacy = body[len(_FIGURE_PREFIX):]
            parts = legacy.split("|")
            while len(parts) < 4: parts.append("")
            return Figure(path=parts[0], caption=parts[1],
                          label=parts[2] or None,
                          width=parts[3] or "0.8\\textwidth")
        # New format: path on the first line, then Caption/Label/Width
        # meta lines. _split_stub_meta peels the meta lines off the end.
        lines, meta = _split_stub_meta(body)
        path = lines[0] if lines else ""
        return Figure(
            path=path,
            caption=meta.get("Caption", ""),
            label=(meta.get("Label", "") or None),
            width=meta.get("Width", "") or "0.8\\textwidth",
        )

    def _table_from_stub(self, text: str) -> Table:
        # Legacy format: "[TABLE] rows || cap | label | align".
        if text.startswith(_TABLE_PREFIX):
            legacy = text[len(_TABLE_PREFIX):]
            rows_str, sep, meta = legacy.partition("||")
            if rows_str:
                row_sources = rows_str.split(_LINE_SEP)
                if len(row_sources) == 1 and "\n" in rows_str:
                    row_sources = rows_str.split("\n")
                rows = [r.split("\t") for r in row_sources]
            else:
                rows = []
            parts = meta.split("|") if sep else []
            while len(parts) < 3: parts.append("")
            return Table(rows=rows, caption=parts[0],
                         label=parts[1] or None, alignment=parts[2])
        # New format: rows (TAB-separated cells, U+2028-separated rows)
        # followed by Caption/Label/Alignment meta lines.
        lines, meta = _split_stub_meta(text)
        rows = [r.split("\t") for r in lines] if lines else []
        return Table(
            rows=rows,
            caption=meta.get("Caption", ""),
            label=(meta.get("Label", "") or None),
            alignment=meta.get("Alignment", ""),
        )

    def _table_from_qtexttable(self, qtable: QTextTable) -> Table:
        """Extract a Table model node from a live QTextTable widget."""
        tfmt = qtable.format()
        caption = tfmt.property(_P_TABLE_CAPTION) or ""
        label = tfmt.property(_P_TABLE_LABEL) or None
        alignment = tfmt.property(_P_TABLE_ALIGNMENT) or ""
        style = tfmt.property(_P_TABLE_STYLE) or ""
        nrows = qtable.rows()
        ncols = qtable.columns()
        # If last row is a merged caption row, exclude it from data rows.
        has_caption_row = False
        if caption and nrows > 1:
            cell = qtable.cellAt(nrows - 1, 0)
            text = cell.firstCursorPosition().block().text()
            if cell.format().property(_P_CAPTION_ROW) \
                    or text.startswith("Caption: "):
                has_caption_row = True
        data_rows = nrows - (1 if has_caption_row else 0)
        rows: list[list[str]] = []
        for r in range(data_rows):
            row: list[str] = []
            for c in range(ncols):
                cell = qtable.cellAt(r, c)
                shown = cell.firstCursorPosition().block().text()
                raw = cell.format().property(_P_CELL_RAW)
                # Unchanged cell: return its original LaTeX, so \\textbf,
                # math and macros survive; an edited cell takes the new text.
                if raw is not None and _cell_display_text(raw) == shown.strip():
                    row.append(raw)
                else:
                    row.append(shown)
            rows.append(row)
        return Table(rows=rows, caption=caption, label=label,
                     alignment=alignment, style=style)

    # ---------- formatting actions (called by mainwindow) ----------

    def apply_heading(self, level: int, block=None) -> None:
        """Apply a paragraph style by level code:
            -1 = Title,  -2 = Author,  -3 = Abstract,  -4 = Keywords,
            -5 = Chapter (\\chapter — only valid in report/book/memoir),
            -6 = Frame (\\begin{frame} — only valid in beamer),
            -7 = Affiliation,  -8 = Correspondence,
             0 = Body,  1..5 = Heading 1..5.
        *block* defaults to the caret's line."""
        cursor = self._edit.textCursor()
        if block is None:
            block = cursor.block()
        block_cursor = QTextCursor(block)
        block_cursor.select(QTextCursor.BlockUnderCursor)
        block_cursor.beginEditBlock()
        if level == -1:
            block.setUserState(_STATE_TITLE)
            QTextCursor(block).setBlockFormat(_title_block_format())
            cfmt = self._title_fmt()
            block_cursor.mergeCharFormat(cfmt)
        elif level == -2:
            block.setUserState(_STATE_AUTHOR)
            QTextCursor(block).setBlockFormat(_author_block_format())
            cfmt = self._title_block_fmt(-2)
            block_cursor.mergeCharFormat(cfmt)
        elif level in (-7, -8):
            corr = level == -8
            block.setUserState(
                _STATE_CORRESPONDENCE if corr else _STATE_AFFILIATION)
            QTextCursor(block).setBlockFormat(_affiliation_block_format())
            cfmt = self._title_block_fmt(level)
            block_cursor.setCharFormat(cfmt)
        elif level == -3:
            block.setUserState(_STATE_ABSTRACT)
            QTextCursor(block).setBlockFormat(_abstract_block_format())
            cfmt = _abstract_char_format()
            block_cursor.setCharFormat(cfmt)
        elif level == -4:
            block.setUserState(_STATE_KEYWORDS)
            QTextCursor(block).setBlockFormat(_keywords_block_format())
            cfmt = _keywords_char_format()
            block_cursor.setCharFormat(cfmt)
        elif level == -5:
            block.setUserState(_STATE_CHAPTER)
            QTextCursor(block).setBlockFormat(QTextBlockFormat())
            cfmt = self._heading_fmt(0)
            block_cursor.mergeCharFormat(cfmt)
        elif level == -6:
            block.setUserState(_STATE_FRAME)
            QTextCursor(block).setBlockFormat(QTextBlockFormat())
            cfmt = _frame_char_format()
            block_cursor.mergeCharFormat(cfmt)
        elif level >= 1:
            block.setUserState(level)
            QTextCursor(block).setBlockFormat(QTextBlockFormat())
            cfmt = self._heading_fmt(level)
            block_cursor.mergeCharFormat(cfmt)
        else:
            block.setUserState(_STATE_PARAGRAPH)
            QTextCursor(block).setBlockFormat(QTextBlockFormat())
            fmt = QTextCharFormat()
            f = QFont(self._visual_font_family)
            f.setPointSizeF(self._body_font_pt * (self._zoom_percent / 100))
            fmt.setFont(f)
            cfmt = fmt
            block_cursor.setCharFormat(fmt)
        # An empty line has no characters to restyle, so the style must go
        # on the block and the caret too, or the text typed next is body.
        QTextCursor(block).mergeBlockCharFormat(cfmt)
        if cursor.block() == block and block.length() <= 1 \
                and not self._in_key_edit:
            self._edit.mergeCurrentCharFormat(cfmt)
        block_cursor.endEditBlock()
        self._apply_page_layout()
        self._on_text_changed()

    def toggle_heading_numbered(self, numbered: bool) -> None:
        """Toggle the numbered/starred state of the current heading block."""
        block = self._edit.textCursor().block()
        state = block.userState()
        if numbered:
            if state == _STATE_CHAPTER_STAR:
                block.setUserState(_STATE_CHAPTER)
            elif _STATE_HEADING_STAR_BASE < state <= _STATE_HEADING_STAR_BASE + 5:
                block.setUserState(state - _STATE_HEADING_STAR_BASE)
        else:
            if state == _STATE_CHAPTER:
                block.setUserState(_STATE_CHAPTER_STAR)
            elif 1 <= state <= 5:
                block.setUserState(_STATE_HEADING_STAR_BASE + state)
        self._on_text_changed()

    def is_heading_numbered(self) -> bool:
        """Return True if the current block is a numbered heading."""
        state = self._edit.textCursor().block().userState()
        if state == _STATE_CHAPTER_STAR:
            return False
        if _STATE_HEADING_STAR_BASE < state <= _STATE_HEADING_STAR_BASE + 5:
            return False
        return True

    def apply_alignment(self, name: str) -> None:
        """name ∈ {"left", "center", "right", "justify"}."""
        flag = _QT_ALIGNMENT.get(name, Qt.AlignLeft)
        cursor = self._edit.textCursor()
        bfmt = cursor.blockFormat()
        bfmt.setAlignment(flag)
        cursor.setBlockFormat(bfmt)
        self._on_text_changed()

    def current_alignment(self) -> str:
        return self._alignment_of(self._edit.textCursor().block())

    # ----- zoom -----

    def body_font_pt(self) -> int:
        return self._body_font_pt

    def is_dark(self) -> bool:
        return self._dark

    def set_dark(self, dark: bool) -> None:
        """Switch the colour theme used by table / figure block
        widgets. Rebuilds the document so existing tables and
        figures get re-rendered with the new palette — their cell
        backgrounds and text colours otherwise remain stuck on the
        theme they were created under, which is what made tables
        invisible in dark mode (light text on light-orange cells).

        Preserves cursor position and scroll offset across the
        rebuild so the user isn't bounced to the top of the
        document when they toggle the theme."""
        dark = bool(dark)
        if dark == self._dark:
            return
        self._dark = dark
        # Snapshot, rebuild, restore.
        cursor_pos = self._edit.textCursor().position()
        scroll_y = self._edit.verticalScrollBar().value()
        doc = self.get_document()
        self.set_document(doc)
        # Restore cursor + scroll.
        new_cursor = self._edit.textCursor()
        new_cursor.setPosition(min(cursor_pos,
                                   self._edit.document().characterCount() - 1))
        self._edit.setTextCursor(new_cursor)
        self._edit.verticalScrollBar().setValue(scroll_y)

    def is_spell_check_enabled(self) -> bool:
        return self._spell_highlighter.is_enabled()

    def set_spell_check_enabled(self, enabled: bool) -> None:
        self._spell_highlighter.set_enabled(enabled)

    def _body_char_format(self) -> QTextCharFormat:
        """The baseline char format every body Text fragment uses on
        render. Carrying it explicitly (instead of letting Qt inherit
        from the cursor) keeps fonts consistent when the user starts a
        new paragraph after a heading or a code span. Honours the
        current zoom so scaled-up text on screen still matches the
        body when the user presses Enter and types."""
        fmt = QTextCharFormat()
        f = QFont(self._visual_font_family)
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        f.setPointSizeF(self._body_font_pt * zoom)
        fmt.setFont(f)
        return fmt

    def set_body_font_pt(self, pt: int) -> None:
        """Change the default body text size and re-apply it to every
        Paragraph block, so existing body text grows/shrinks with the
        new default. Headings keep their own sizes."""
        pt = max(6, min(72, int(pt)))
        if pt == self._body_font_pt:
            return
        self._body_font_pt = pt
        # Sync the document meta so the serialized LaTeX preamble
        # matches what the editor actually shows. Without this, the
        # toolbar font-size combo changed the on-screen size but the
        # exported / previewed .tex kept the dialog's old size.
        self._meta.body_font_pt = pt
        self._building = True
        try:
            doc = self._edit.document()
            block = doc.firstBlock()
            zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
            while block.isValid():
                state = block.userState()
                if state in (0, -1):    # Paragraph or uninitialised
                    bc = QTextCursor(block)
                    bc.select(QTextCursor.BlockUnderCursor)
                    fmt = QTextCharFormat()
                    f = QFont(self._visual_font_family)
                    f.setPointSizeF(pt * zoom)
                    fmt.setFont(f)
                    bc.setCharFormat(fmt)
                block = block.next()
        finally:
            self._building = False
        self._resize_math_images()
        self._apply_page_layout()
        self._on_text_changed()

    def _heading_fmt(self, level: int) -> QTextCharFormat:
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        return _heading_char_format(level, self._body_font_pt * zoom,
                                    self._visual_font_family)

    def _title_block_fmt(self, code: int) -> QTextCharFormat:
        """Author (-2), Affiliation (-7) or Correspondence (-8) format at
        the current zoom and visual font, like every other style."""
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        body = self._body_font_pt * zoom
        if code == -2:
            return _author_char_format(body, self._visual_font_family)
        return _affiliation_char_format(code == -8, body,
                                        self._visual_font_family)

    def _title_fmt(self) -> QTextCharFormat:
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        return _title_char_format(self._body_font_pt * zoom,
                                  self._visual_font_family)

    def _apply_page_layout(self) -> None:
        """Mirror the PDF's geometry on screen: per-side margins from the
        document settings, plus line spacing and paragraph indentation.
        Must be re-run after zoom, meta or content changes because the
        pixel values scale with zoom."""
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        m = self._meta
        doc = self._edit.document()
        root = doc.rootFrame()
        ff = root.frameFormat()
        ff.setTopMargin(m.margin_top_cm * _PX_PER_CM * zoom)
        ff.setBottomMargin(m.margin_bottom_cm * _PX_PER_CM * zoom)
        cols = max(1, int(getattr(m, "column_count", 1) or 1))
        left_px = m.margin_left_cm * _PX_PER_CM * zoom
        right_px = m.margin_right_cm * _PX_PER_CM * zoom
        # In columns each layout page IS one column, so the side margins
        # move out of the layout and into the column placement.
        ff.setLeftMargin(0 if cols > 1 else left_px)
        ff.setRightMargin(0 if cols > 1 else right_px)
        # LaTeX's \columnsep is 10pt.
        self._edit.set_columns(cols, 10 * 96 / 72 * zoom, left_px, right_px)
        # Only write what changed: every format write counts as a document
        # edit, and this runs after each edit, so an unconditional write
        # re-triggered the compile forever.
        if ff != root.frameFormat():
            root.setFrameFormat(ff)

        em_px = self._body_font_pt * 96 / 72 * zoom
        spacing = max(0.5, float(m.line_spacing or 1.0))
        from .latex_fonts import baselineskip_pt
        # Body lines sit exactly LaTeX's \baselineskip apart, so a page
        # holds as many lines on screen as in the PDF.
        body_line_px = baselineskip_pt(self._body_font_pt, spacing) \
            * 96 / 72 * zoom
        was_building = self._building
        self._building = True
        # Fold the layout pass into the previous undo step so Ctrl+Z
        # undoes the user's edit, not an invisible reformat.
        edit = QTextCursor(doc)
        edit.joinPreviousEditBlock()
        try:
            prev_state = None
            # PDF page starts mean a new sheet; with columns a forced break
            # would only start a new column, so leave paging to the layout.
            pdf_breaks = (self._pdf_page_start_blocks()
                          if self._edit.columns() <= 1 else set())
            offset = self._heading_offset
            has_chapters = self._has_chapter_blocks() or offset[0] > 0
            counters = list(offset)
            block = doc.firstBlock()
            while block.isValid():
                if QTextCursor(block).currentTable() is not None:
                    # Table / figure cells keep their own layout.
                    block = block.next()
                    continue
                state = block.userState()
                bfmt = block.blockFormat()
                # Start a new sheet exactly where the compiled PDF does.
                bfmt.setPageBreakPolicy(
                    QTextFormat.PageBreak_AlwaysBefore
                    if block.blockNumber() in pdf_breaks
                    else QTextFormat.PageBreak_Auto)
                number = ""
                level = 0 if state == _STATE_CHAPTER else (
                    state if 1 <= state <= 5 else None)
                if level is not None:
                    counters[level] += 1
                    for i in range(level + 1, len(counters)):
                        counters[i] = 0
                    if level in _NUMBERED_HEADING_LEVELS:
                        start = 0 if has_chapters else 1
                        number = ".".join(
                            str(c) for c in counters[start:level + 1])
                any_level = level
                if _STATE_HEADING_STAR_BASE < state <= _STATE_HEADING_STAR_BASE + 5:
                    any_level = state - _STATE_HEADING_STAR_BASE
                elif state == _STATE_CHAPTER_STAR:
                    any_level = 0
                if state == _STATE_MATH_BLOCK:
                    # \abovedisplayskip / \belowdisplayskip: 12pt at 12pt.
                    bfmt.setTopMargin(0.8 * em_px)
                    bfmt.setBottomMargin(0.8 * em_px)
                if any_level is not None:
                    above, below = _HEADING_SPACING.get(any_level, (1.4, 0.65))
                    bfmt.setTopMargin(above * em_px)
                    bfmt.setBottomMargin(below * em_px)
                old_number = bfmt.property(_P_HEADING_NUMBER) or ""
                if number:
                    bfmt.setProperty(_P_HEADING_NUMBER, number)
                    it = block.begin()
                    font = (it.fragment().charFormat().font()
                            if not it.atEnd() else self._heading_fmt(
                                level).font())
                    fm = QFontMetricsF(font)
                    # LaTeX leaves 1em between the number and the title.
                    bfmt.setTextIndent(fm.horizontalAdvance(number)
                                       + fm.height() * 0.8)
                elif old_number:
                    bfmt.clearProperty(_P_HEADING_NUMBER)
                    bfmt.setTextIndent(0)
                if state in (_STATE_PARAGRAPH, -1):
                    bfmt.setLineHeight(body_line_px, 2)   # FixedHeight
                elif abs(spacing - 1.0) > 0.01:
                    bfmt.setLineHeight(spacing * 100, 1)  # ProportionalHeight
                else:
                    bfmt.setLineHeight(0, 0)              # SingleHeight
                if state in (_STATE_PARAGRAPH, -1) and block.textList() is None:
                    # LaTeX never indents the first paragraph after a
                    # heading, title or display block.
                    follows_para = prev_state in (_STATE_PARAGRAPH, -1)
                    if m.paragraph_indent:
                        bfmt.setTextIndent(1.5 * em_px if follows_para else 0)
                        bfmt.setBottomMargin(0)
                    else:
                        bfmt.setTextIndent(0)
                        bfmt.setBottomMargin(0.8 * em_px)
                if bfmt != block.blockFormat():
                    QTextCursor(block).setBlockFormat(bfmt)
                if block.text().strip() or state not in (_STATE_PARAGRAPH, -1):
                    prev_state = state
                block = block.next()
        finally:
            edit.endEditBlock()
            self._building = was_building

    def zoom_percent(self) -> int:
        return self._zoom_percent

    def set_zoom_percent(self, percent: int) -> None:
        percent = max(25, min(400, int(percent)))
        if percent == self._zoom_percent:
            return
        # QTextEdit.zoomIn only scales the WIDGET's default font, which has
        # no effect on text that carries an explicit character-format point
        # size (every heading, every Title, every formatted run). To make
        # zoom actually grow the text on screen we walk every fragment and
        # rescale its point size by the ratio of new-to-old zoom.
        prev_factor = self._zoom_percent / 100 if self._zoom_percent else 1.0
        new_factor = percent / 100
        ratio = new_factor / prev_factor

        self._building = True   # suppress textChanged → debounced recompile
        try:
            doc = self._edit.document()
            block = doc.firstBlock()
            while block.isValid():
                it = block.begin()
                while not it.atEnd():
                    frag = it.fragment()
                    if frag.isValid():
                        fmt = frag.charFormat()
                        f = fmt.font()
                        size = f.pointSizeF()
                        if size > 0:
                            f.setPointSizeF(size * ratio)
                            fmt.setFont(f)
                            c = QTextCursor(doc)
                            c.setPosition(frag.position())
                            c.setPosition(frag.position() + frag.length(),
                                          QTextCursor.KeepAnchor)
                            c.mergeCharFormat(fmt)
                    it += 1
                block = block.next()
            # Scale the widget's default font too so freshly-typed text uses
            # the same scale as the surrounding content.
            wf = self._edit.font()
            if wf.pointSizeF() > 0:
                wf.setPointSizeF(wf.pointSizeF() * ratio)
                self._edit.setFont(wf)
        finally:
            self._building = False

        self._zoom_percent = percent
        # Page card grows/shrinks proportionally so paper proportions are
        # preserved. The document margin also scales so the number of
        # characters per line stays constant — zoom should make everything
        # bigger uniformly, not reflow the text.
        page = page_sizes.by_code(self._meta.page_size)
        scaled_w = round(page.width_px * percent / 100)
        scaled_h = round(page.height_px * percent / 100)
        self._page.setFixedWidth(scaled_w)
        self._edit.set_page_size_px(scaled_w, scaled_h)
        self._apply_page_layout()
        self._resize_math_images()
        self._resize_figure_images()
        self._resize_to_document()

    def set_fit_to_width(self, enabled: bool) -> None:
        self._fit_to_width = enabled
        if enabled:
            self._apply_fit_to_width()

    def fit_to_width(self) -> bool:
        return self._fit_to_width

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._fit_to_width:
            self._fit_debounce.start()

    def _apply_fit_to_width(self) -> None:
        if not self._fit_to_width:
            return
        page = page_sizes.by_code(self._meta.page_size)
        viewport_w = self._scroll.viewport().width()
        # Leave 48px padding on each side for the desk margins.
        available = viewport_w - 48
        if available < 100:
            return
        target_pct = max(25, min(300, round(available / page.width_px * 100)))
        # Snap to 5% grid to match slider granularity.
        target_pct = 5 * round(target_pct / 5)
        if target_pct == self._zoom_percent:
            return
        self.set_zoom_percent(target_pct)
        self.zoomChanged.emit(target_pct)

    def toggle_mark(self, mark: str) -> None:
        fmt = QTextCharFormat()
        f = self._edit.currentFont()
        if mark == "bold":
            fmt.setFontWeight(QFont.Normal if f.bold() else QFont.Bold)
        elif mark == "italic":
            fmt.setFontItalic(not f.italic())
        elif mark == "underline":
            fmt.setFontUnderline(not f.underline())
        elif mark == "strikethrough":
            fmt.setFontStrikeOut(not f.strikeOut())
        elif mark == "code":
            f2 = QFont("Consolas") if f.family().lower() != "consolas" else QFont()
            if f2.family() == "": f2.setPointSize(12)
            f2.setStyleHint(QFont.Monospace if f.family().lower() != "consolas" else QFont.AnyStyle)
            fmt.setFont(f2)
        elif mark == "smallcaps":
            new_cap = (QFont.MixedCase if f.capitalization() == QFont.SmallCaps else QFont.SmallCaps)
            f3 = QFont(f); f3.setCapitalization(new_cap); fmt.setFont(f3)
        elif mark == "subscript":
            current = self._edit.currentCharFormat().verticalAlignment()
            fmt.setVerticalAlignment(
                QTextCharFormat.AlignNormal if current == QTextCharFormat.AlignSubScript
                else QTextCharFormat.AlignSubScript)
        elif mark == "superscript":
            current = self._edit.currentCharFormat().verticalAlignment()
            fmt.setVerticalAlignment(
                QTextCharFormat.AlignNormal if current == QTextCharFormat.AlignSuperScript
                else QTextCharFormat.AlignSuperScript)
        self._merge_format(fmt)

    def clear_formatting(self) -> None:
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        fmt = QTextCharFormat()
        f = QFont(); f.setPointSize(12); fmt.setFont(f)
        cursor.setCharFormat(fmt)

    def insert_inline_math(self) -> None:
        latex, ok = QInputDialog.getText(self, "Insert inline math", "LaTeX:")
        if ok and latex:
            self.insert_inline_math_with(latex)

    def insert_inline_math_with(self, latex: str) -> None:
        """Insert the given LaTeX as inline math without prompting. Used
        by the symbol picker so a click on a glyph drops the symbol in
        immediately."""
        if not latex:
            return
        self._insert_inline(self._edit.textCursor(), MathInline(latex=latex))

    def insert_raw_inline_with(self, latex: str) -> None:
        """Insert the given LaTeX verbatim at the cursor (no $...$ wrap).
        Used for text-mode macros like \\Kstroke that wouldn't render
        correctly inside an inline math span and for round-tripping
        unknown commands captured from imported .tex files."""
        if not latex:
            return
        self._edit.textCursor().insertText(latex, _raw_inline_format(latex))

    def insert_math_block(self) -> None:
        latex, ok = QInputDialog.getMultiLineText(self, "Insert math block", "LaTeX:")
        if ok and latex.strip():
            # The in-app help promises a *numbered* display equation.
            self.insert_math_block_with(latex, numbered=True)

    def insert_math_block_with(self, latex: str, numbered: bool = False) -> None:
        """Insert a display math block at the cursor without prompting.
        Used by the equation builder so multi-line templates drop in
        directly. `numbered` makes it a \\begin{equation} (not equation*)
        on serialization."""
        if not latex.strip():
            return
        c = self._edit.textCursor()
        c.beginEditBlock()
        c.insertBlock()
        c.block().setUserState(_STATE_MATH_BLOCK)
        bfmt = QTextBlockFormat()
        bfmt.setProperty(_P_MATH_NUMBERED, numbered)
        bfmt.setAlignment(Qt.AlignHCenter)
        c.setBlockFormat(bfmt)
        shown = self._insert_math_image(c, latex)
        c.insertText(latex.replace("\n", _LINE_SEP),
                     _math_hidden_format() if shown
                     else _math_block_char_format())
        c.insertBlock(); c.block().setUserState(_STATE_PARAGRAPH)
        c.endEditBlock()

    def insert_raw_block_with(self, latex: str) -> None:
        """Insert *latex* as a RawLatex block without prompting. Used by the
        chemfig editor, whose \\chemfig{}/\\schemestart output is text-mode
        (not math) and must reach the document verbatim."""
        if not latex.strip():
            return
        self._insert_raw_block(latex)

    def insert_bullet_list(self) -> None:
        self._edit.textCursor().createList(QTextListFormat.ListDisc)

    def insert_numbered_list(self) -> None:
        self._edit.textCursor().createList(QTextListFormat.ListDecimal)

    def insert_link(self) -> None:
        url, ok = QInputDialog.getText(self, "Insert link", "URL:")
        if not ok or not url: return
        text, ok = QInputDialog.getText(self, "Link text", "Display text:", text=url)
        if not ok: return
        self._edit.textCursor().insertText(text or url, _link_format(url))

    def insert_footnote(self) -> None:
        note, ok = QInputDialog.getMultiLineText(self, "Insert footnote", "Note text:")
        if ok and note.strip():
            self._edit.textCursor().insertText(note, _footnote_format(note))

    def insert_citation(self) -> None:
        keys, ok = QInputDialog.getText(self, "Insert citation",
                                        "BibTeX key(s), comma-separated:")
        if not ok or not keys.strip(): return
        style, ok = QInputDialog.getItem(self, "Citation style", "Command:",
                                         ["cite", "citep", "citet"], 0, False)
        if not ok: return
        payload = f"{keys.strip()}|{style}"
        display = f"[{keys.strip()}]"
        self._edit.textCursor().insertText(display, _citation_format(payload))

    def insert_crossref(self) -> None:
        label, ok = QInputDialog.getText(self, "Cross-reference", "Label:")
        if not ok or not label: return
        kind, ok = QInputDialog.getItem(self, "Reference type", "Command:",
                                        ["ref", "eqref", "pageref"], 0, False)
        if not ok: return
        self._edit.textCursor().insertText(
            f"<{kind}:{label}>", _crossref_format(f"{label}|{kind}"))

    # ---- review: highlight & comments ----

    def insert_highlight(self, color: str = "yellow") -> None:
        """Apply a highlight to the current selection."""
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = _highlight_format(color)
        cursor.mergeCharFormat(fmt)
        self._edit.setTextCursor(cursor)

    def remove_highlight(self) -> None:
        """Remove highlight from the current selection."""
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(Qt.transparent))
        fmt.setProperty(_P_HIGHLIGHT, "")
        cursor.mergeCharFormat(fmt)
        self._edit.setTextCursor(cursor)

    def insert_comment(self, author: str = "") -> None:
        """Insert a reviewer comment on the selected text."""
        from datetime import datetime
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            return
        note, ok = QInputDialog.getMultiLineText(
            self, "New comment", "Comment:")
        if not ok or not note.strip():
            return
        ts = datetime.now().isoformat(timespec="seconds")
        fmt = _comment_format(note.strip(), author, ts, False)
        cursor.mergeCharFormat(fmt)
        self._edit.setTextCursor(cursor)

    def accept_comment(self) -> None:
        """Accept (resolve) the comment at cursor — remove comment
        formatting but keep the text."""
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        # Walk the selection and clear comment properties
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(Qt.transparent))
        fmt.setProperty(_P_COMMENT, "")
        fmt.setUnderlineStyle(QTextCharFormat.NoUnderline)
        fmt.setToolTip("")
        cursor.mergeCharFormat(fmt)
        self._edit.setTextCursor(cursor)

    def reject_comment(self) -> None:
        """Reject the comment at cursor — delete the commented text."""
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.removeSelectedText()

    def _find_comment_span(self, forward: bool = True) -> bool:
        """Move cursor to the next/previous comment span. Returns True
        if a comment was found."""
        doc = self._edit.document()
        cursor = self._edit.textCursor()
        pos = cursor.position()
        block = doc.begin() if forward else doc.end().previous()
        found_pos = -1
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid() and frag.charFormat().property(_P_COMMENT):
                    frag_start = frag.position()
                    frag_end = frag_start + frag.length()
                    if forward and frag_start > pos:
                        found_pos = frag_start
                        break
                    elif not forward and frag_end < pos:
                        found_pos = frag_start
                it += 1
            if found_pos >= 0:
                break
            block = block.next() if forward else block.previous()
        if found_pos >= 0:
            cursor.setPosition(found_pos)
            cursor.movePosition(QTextCursor.NextCharacter,
                                QTextCursor.KeepAnchor, 1)
            # Extend to cover the full comment span
            while (cursor.position() < doc.characterCount() - 1):
                test = QTextCursor(cursor)
                test.movePosition(QTextCursor.NextCharacter)
                fmt = test.charFormat()
                if not fmt.property(_P_COMMENT):
                    break
                cursor.movePosition(QTextCursor.NextCharacter,
                                    QTextCursor.KeepAnchor)
            self._edit.setTextCursor(cursor)
            return True
        return False

    def next_comment(self) -> None:
        self._find_comment_span(forward=True)

    def prev_comment(self) -> None:
        self._find_comment_span(forward=False)

    def _on_image_received(self, path: str) -> None:
        """Slot for PagedTextEdit.imageReceived. Drops a Figure block at
        the cursor pointing at the freshly-saved image."""
        c = self._edit.textCursor()
        fig = Figure(path=path, caption="", label=None, width="0.6\\textwidth")
        self._insert_figure_widget(c, fig)
        self._on_text_changed()

    def drop_image_file(self, src: Path) -> None:
        """Copy *src* into the images directory and insert a Figure block."""
        import shutil
        dest_dir = self._images_dir
        if dest_dir is None:
            return
        dest = dest_dir / src.name
        if dest.exists():
            stem, suffix = src.stem, src.suffix
            n = 1
            while dest.exists():
                dest = dest_dir / f"{stem}_{n}{suffix}"
                n += 1
        try:
            shutil.copy2(src, dest)
        except OSError:
            return
        self._on_image_received(str(dest))

    def insert_figure(self) -> None:
        dlg = _InsertFigureDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        path = dlg.path()
        if not path:
            return
        c = self._edit.textCursor()
        from .serializer import escape_text
        fig = Figure(path=path, caption=escape_text(dlg.caption()),
                     label=dlg.label() or None,
                     width="0.8\\textwidth")
        self._insert_figure_widget(c, fig)

    def insert_drawing(self) -> None:
        """Open the freehand drawing dialog. On OK, ask for caption/label
        via combined dialog, then insert as a Figure block."""
        from .drawing_dialog import DrawingDialog
        dlg = DrawingDialog(self._images_dir, self)
        if dlg.exec() != QDialog.Accepted:
            return
        path = dlg.saved_path()
        if path is None:
            return
        cdlg = _InsertFigureDialog(self, path_value=str(path),
                                   path_readonly=True,
                                   title="Drawing details")
        if cdlg.exec() != QDialog.Accepted:
            return
        from .serializer import escape_text
        c = self._edit.textCursor()
        fig = Figure(path=str(path), caption=escape_text(cdlg.caption()),
                     label=cdlg.label() or None, width="0.7\\textwidth",
                     source="drawing")
        self._insert_figure_widget(c, fig)
        self._on_text_changed()
        if dlg.handoff_to_khervepaint:
            self.edit_in_khervepaint(path)

    # ----- KhervePaint hand-off -----------------------------------------

    def khervepaint_link(self):
        if getattr(self, "_kp_link", None) is None:
            from .khervepaint_link import KhervePaintLink
            self._kp_link = KhervePaintLink(self)
            self._kp_link.drawingUpdated.connect(self.refresh_figure_image)
        return self._kp_link

    def edit_in_khervepaint(self, png_path, interactive: bool = True
                            ) -> tuple[bool, str]:
        """Open a drawing figure in KhervePaint; its saves flow back into
        the figure. Interactively, a missing KhervePaint offers to locate
        it."""
        from . import khervepaint_link as kpl
        ok, msg = self.khervepaint_link().open(png_path)
        if ok or not interactive:
            return ok, msg
        if msg != kpl.NOT_FOUND_MESSAGE:
            QMessageBox.warning(self, "KhervePaint", msg)
            return ok, msg
        box = QMessageBox(QMessageBox.Information, "KhervePaint", msg,
                          QMessageBox.Cancel, self)
        locate = box.addButton("Locate KhervePaint…",
                               QMessageBox.AcceptRole)
        box.exec()
        if box.clickedButton() is not locate:
            return ok, msg
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Locate KhervePaint", "",
            "KhervePaint (KhervePaint* *.app *.exe *.py);;All files (*)")
        if not path:
            return ok, msg
        if not kpl.set_custom_path(path):
            QMessageBox.warning(self, "KhervePaint",
                                f"{path} cannot be run as KhervePaint.")
            return ok, msg
        return self.khervepaint_link().open(png_path)

    def _figure_tables(self):
        for frame in self._edit.document().rootFrame().childFrames():
            if isinstance(frame, QTextTable) and frame.format().property(
                    _P_FIGURE_PATH) is not None:
                yield frame

    def refresh_figure_image(self, img_path) -> int:
        """Redraw every figure showing *img_path* after the file changed on
        disk. Returns how many figures were refreshed."""
        target = Path(img_path).resolve()
        n = 0
        for qtable in list(self._figure_tables()):
            resolved = self._resolve_image_path(
                qtable.format().property(_P_FIGURE_PATH) or "")
            if resolved is not None and resolved.resolve() == target:
                self._refresh_figure_image(qtable, resolved)
                n += 1
        return n

    # ----- double-click-to-re-edit drawings ---------------------------

    def eventFilter(self, obj, event):
        # Qt can still deliver events while this widget is being torn down,
        # after _edit has gone; guard rather than raise from the override.
        edit = getattr(self, "_edit", None)
        if (edit is not None and obj is edit
                and event.type() == QEvent.Type.KeyPress
                and self._keep_styles_across_key(event)):
            return True
        if (edit is not None and (obj is edit or obj is edit.viewport())
                and event.type() == QEvent.Type.MouseButtonDblClick):
            cursor = self._edit.cursorForPosition(event.position().toPoint())
            qtable = cursor.currentTable()
            if qtable is not None:
                tfmt = qtable.format()
                if tfmt.property(_P_IS_FIGURE):
                    self._edit_existing_figure(qtable)
                    return True
            if self._edit_math_at(cursor):
                return True
        return super().eventFilter(obj, event)

    # ----- Enter / Backspace / Delete keep block styles ----------------

    def _keep_styles_across_key(self, event) -> bool:
        """Run the key ourselves when it splits or joins text blocks, so
        every line keeps a real style. Left to Qt, both produce a block
        with no style (-1) whose font then decides, on save, whether it
        is a heading — so Visual and LaTeX disagree.

        Returns True if the key was handled."""
        key = event.key()
        if key not in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Backspace,
                       Qt.Key_Delete):
            return False
        cursor = self._edit.textCursor()
        block = cursor.block()
        if _style_code(block.userState()) is None:
            return False
        self._in_key_edit = True
        try:
            return self._run_block_key(event, key, cursor, block)
        finally:
            self._in_key_edit = False

    def _run_block_key(self, event, key, cursor, block) -> bool:
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                return False        # line break inside the block
            state = block.userState()
            at_end = (not cursor.hasSelection()
                      and cursor.position() == block.position() + block.length() - 1)
            cursor.beginEditBlock()
            cursor.insertBlock()
            # Word: Enter at the end of a heading starts body text; Enter
            # inside one splits it into two lines of the same style.
            self._restyle_block(cursor.block(),
                                _STATE_PARAGRAPH if at_end else state)
            self._restyle_block(cursor.block().previous(), state)
            cursor.endEditBlock()
            self._place_caret(cursor)
        else:
            if cursor.hasSelection():
                first = self._edit.document().findBlock(cursor.selectionStart())
                last = self._edit.document().findBlock(cursor.selectionEnd())
                if first == last:
                    return False
                keep = first
            elif block.length() == 2 and (
                    (key == Qt.Key_Backspace and cursor.position() > block.position())
                    or (key == Qt.Key_Delete and cursor.position() == block.position())):
                # Emptying the line: Qt drops the caret's font with the
                # last character, so retyped text would lose the style.
                keep = block
            elif key == Qt.Key_Backspace:
                if cursor.position() != block.position():
                    return False
                keep = block.previous()
            else:
                if cursor.position() != block.position() + block.length() - 1:
                    return False
                keep = block
            if not keep.isValid() or _style_code(keep.userState()) is None:
                return False
            state = keep.userState()
            cursor.beginEditBlock()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            elif key == Qt.Key_Backspace:
                cursor.deletePreviousChar()
            else:
                cursor.deleteChar()
            # Like Word, the joined line takes the first line's style.
            self._restyle_block(cursor.block(), state)
            cursor.endEditBlock()
            self._place_caret(cursor)
        self._on_text_changed()
        return True

    def _restyle_block(self, block, state: int) -> None:
        """Give *block* the style *state* and the matching fonts."""
        code = _style_code(state)
        if code is None or not block.isValid():
            return
        if code == 0:
            self._restyle_as_body(block)
            return
        self.apply_heading(code, block)
        block.setUserState(state)       # keeps a heading's starred form

    def _place_caret(self, cursor: QTextCursor) -> None:
        """Put the caret at *cursor*, typing in its line's style. Only
        after the edit block closes: moving the caret inside one crashes
        Qt."""
        self._edit.setTextCursor(cursor)
        block = cursor.block()
        code = _style_code(block.userState())
        if code is None:
            return
        if block.length() <= 1:
            self._edit.setCurrentCharFormat(block.charFormat())
        elif code != 0 and cursor.position() == block.position():
            # Qt takes the caret's font from the character before it,
            # which at the start of a line belongs to the previous line.
            nxt = QTextCursor(cursor)
            nxt.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            self._edit.setCurrentCharFormat(nxt.charFormat())

    def _restyle_unstyled(self, pos: int, _removed: int, added: int) -> None:
        """Undo, redo and paste bring lines back with no stored style
        (Qt's undo does not record it). Give each such line the style the
        LaTeX would get for it, so the two never disagree."""
        if self._building or self._in_key_edit:
            return
        doc = self._edit.document()
        block = doc.findBlock(pos)
        end = doc.findBlock(min(pos + added, doc.characterCount() - 1))
        while block.isValid():
            if (block.userState() == -1 and block.textList() is None
                    and QTextCursor(block).currentTable() is None
                    and block.text().strip("\ufffc\u2028 ")):
                node = self._classify_text_block(block)
                state = _STATE_PARAGRAPH
                if isinstance(node, Section):
                    state = (_STATE_CHAPTER if node.level == 0
                             else node.level)
                elif isinstance(node, Title):
                    state = _STATE_TITLE
                elif isinstance(node, Author):
                    state = _STATE_AUTHOR
                block.setUserState(state)
            self._conform_fonts(block)
            if block == end:
                break
            block = block.next()

    def _conform_fonts(self, block) -> None:
        """Text typed or restored into a line takes that line's size:
        Qt otherwise hands it whatever font the caret last held (another
        line's heading size, or none at all after an undo)."""
        code = _style_code(block.userState())
        if code in _TITLE_BLOCK_SCALE:
            self._conform_title_block(block, code)
            return
        if code is None or code < 0:
            return
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        body_pt = self._body_font_pt * zoom
        want = body_pt if code == 0 else self._heading_fmt(code).fontPointSize()
        spans = []
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            cf = frag.charFormat() if frag.isValid() else None
            if (cf is not None and not cf.isImageFormat()
                    and cf.property(_P_MATH) is None
                    and abs(cf.fontPointSize() - want) > 0.01):
                spans.append((frag.position(), frag.length(),
                              cf.fontPointSize() > body_pt * 1.1))
            it += 1
        for pos, n, was_heading in spans:
            fix = QTextCharFormat()
            fix.setFontPointSize(want)
            if code != 0:
                fix.setFontWeight(QFont.Bold)
            elif was_heading:
                fix.setFontWeight(QFont.Normal)
            fix.setFontFamilies([self._visual_font_family])
            c = QTextCursor(self._edit.document())
            c.setPosition(pos)
            c.setPosition(pos + n, QTextCursor.KeepAnchor)
            c.mergeCharFormat(fix)

    def _conform_title_block(self, block, code: int) -> None:
        """Author / affiliation lines keep their style's size, family and
        italic whatever font the caret carried in from elsewhere."""
        want = self._title_block_fmt(code)
        want_pt = want.fontPointSize()
        spans = []
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            cf = frag.charFormat() if frag.isValid() else None
            if (cf is not None and not cf.isImageFormat()
                    and cf.property(_P_MATH) is None
                    and (abs(cf.fontPointSize() - want_pt) > 0.01
                         or cf.fontFamilies() != want.fontFamilies())):
                spans.append((frag.position(), frag.length()))
            it += 1
        for pos, n in spans:
            fix = QTextCharFormat()
            fix.setFontPointSize(want_pt)
            fix.setFontFamilies(want.fontFamilies())
            fix.setFontItalic(want.fontItalic())
            c = QTextCursor(self._edit.document())
            c.setPosition(pos)
            c.setPosition(pos + n, QTextCursor.KeepAnchor)
            c.mergeCharFormat(fix)

    def _restyle_as_body(self, block) -> None:
        """Body style without flattening the paragraph: only text still
        in another style's font (a heading's, say) is reset, so bold or
        italic words the user set survive."""
        block.setUserState(_STATE_PARAGRAPH)
        QTextCursor(block).setBlockFormat(QTextBlockFormat())
        zoom = self._zoom_percent / 100 if self._zoom_percent else 1.0
        body_pt = self._body_font_pt * zoom
        fmt = QTextCharFormat()
        f = QFont(self._visual_font_family)
        f.setPointSizeF(body_pt)
        fmt.setFont(f)

        def foreign(cf) -> bool:
            return abs(cf.fontPointSize() - body_pt) > 0.01

        it = block.begin()
        spans = []
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid() and not frag.charFormat().isImageFormat() \
                    and foreign(frag.charFormat()):
                spans.append((frag.position(), frag.length()))
            it += 1
        for pos, n in spans:
            c = QTextCursor(self._edit.document())
            c.setPosition(pos)
            c.setPosition(pos + n, QTextCursor.KeepAnchor)
            c.setCharFormat(fmt)
        if foreign(block.charFormat()):
            QTextCursor(block).setBlockCharFormat(fmt)

    # ----- double-click-to-re-edit equations --------------------------

    def _ask_math(self, latex: str) -> str | None:
        """Reopen the editor that built *latex*, seeded with it. Returns the
        new LaTeX, or None if cancelled or unchanged.

        A \\ce{} formula goes back to the chemistry editor — sending it to the
        equation builder would show the user a wrapper they never typed."""
        from . import chemistry
        from .equation_editor import ChemistryEditorDialog, EquationEditorDialog

        body = chemistry.unwrap_ce(latex)
        if body is not None:
            dlg = ChemistryEditorDialog(self, initial_latex=body)
        else:
            dlg = EquationEditorDialog(self, initial_latex=latex)
        if dlg.exec() != QDialog.Accepted:
            return None
        new = dlg.latex()
        return new if new and new != latex else None

    def _has_math_at(self, cursor: QTextCursor) -> bool:
        block = cursor.block()
        if block.userState() == _STATE_MATH_BLOCK:
            return bool(block.text().replace("\ufffc", "").replace(
                _MATH_SEP, "").strip(_LINE_SEP).strip())
        return self._inline_math_span(block, cursor.position()) is not None

    def _math_cursor_for_menu(self, pos) -> QTextCursor | None:
        """The math the right-click refers to: the click point, else the
        current selection (right-clicking beside a selected equation)."""
        c = self._edit.cursorForPosition(pos)
        if self._has_math_at(c):
            return c
        sel = self._edit.textCursor()
        if sel.hasSelection():
            for p in (sel.selectionStart(), sel.selectionStart() + 1):
                c = QTextCursor(self._edit.document())
                c.setPosition(min(p, self._edit.document().characterCount() - 1))
                if self._has_math_at(c):
                    return c
        return None

    def _edit_math_at(self, cursor: QTextCursor) -> bool:
        """Re-open the equation builder for the math under *cursor*.

        Returns True if a math node was found (whether or not it changed),
        so the caller can swallow the double-click."""
        block = cursor.block()
        if block.userState() == _STATE_MATH_BLOCK:
            raw = block.text().replace("\ufffc", "").replace(_MATH_SEP, "").strip(_LINE_SEP).strip()
            latex = raw.replace(_LINE_SEP, "\n")
            if not latex:
                return False
            new = self._ask_math(latex)
            if new:
                self._replace_math_block(block, new)
            return True

        span = self._inline_math_span(block, cursor.position())
        if span is None:
            return False
        start, end, latex = span
        new = self._ask_math(latex)
        if new:
            self._replace_inline_math(start, end, new)
        return True

    def _inline_math_span(self, block, pos: int):
        """(start, end, latex) of the MathInline under *pos*, else None.

        Inline math is laid out as either ``[text]`` (simple) or
        ``[image][U+2028][text]`` (complex); a click can land on any of the
        three, and all three must be replaced together."""
        frags = []
        it = block.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid():
                frags.append(f)
            it += 1

        def math_of(i):
            if 0 <= i < len(frags):
                return frags[i].charFormat().property(_P_MATH)
            return None

        hit = None
        for i, f in enumerate(frags):
            if f.position() <= pos <= f.position() + f.length():
                if math_of(i):
                    hit = i
                    break
        if hit is None:
            return None

        latex = math_of(hit)
        # The U+2028 separator inherits the image's char format, so a click
        # can resolve to any of the three fragments. Normalise to the LaTeX
        # text one, then widen back over the preview image if there is one.
        if frags[hit].charFormat().isImageFormat():
            text_i = hit + 2
        elif frags[hit].text() in (_LINE_SEP, _MATH_SEP):
            text_i = hit + 1
        else:
            text_i = hit
        if text_i >= len(frags) or math_of(text_i) != latex:
            return None

        img_i = text_i - 2
        has_image = (img_i >= 0
                     and math_of(img_i) == latex
                     and frags[img_i].charFormat().isImageFormat()
                     and frags[text_i - 1].text() in (_LINE_SEP, _MATH_SEP))
        lo = img_i if has_image else text_i
        return (frags[lo].position(),
                frags[text_i].position() + frags[text_i].length(),
                latex)

    def _replace_math_block(self, block, latex: str) -> None:
        c = QTextCursor(block)
        c.beginEditBlock()
        c.setPosition(block.position())
        c.setPosition(block.position() + block.length() - 1,
                      QTextCursor.KeepAnchor)
        c.removeSelectedText()
        c.block().setUserState(_STATE_MATH_BLOCK)
        shown = self._insert_math_image(c, latex)
        c.insertText(latex.replace("\n", _LINE_SEP),
                     _math_hidden_format() if shown
                     else _math_block_char_format())
        c.endEditBlock()
        self._on_text_changed()

    def _replace_inline_math(self, start: int, end: int, latex: str) -> None:
        c = QTextCursor(self._edit.document())
        c.beginEditBlock()
        c.setPosition(start)
        c.setPosition(end, QTextCursor.KeepAnchor)
        c.removeSelectedText()
        self._insert_inline(c, MathInline(latex=latex))
        c.endEditBlock()
        self._on_text_changed()

    def _edit_existing_figure(self, qtable: QTextTable) -> None:
        """Re-open the drawing dialog for a figure made with it (an SVG
        source beside the PNG, or a legacy JSON sidecar)."""
        from .drawing_dialog import DrawingDialog, drawing_source_for

        tfmt = qtable.format()
        img_path_str = tfmt.property(_P_FIGURE_PATH) or ""
        resolved = self._resolve_image_path(img_path_str)
        if resolved is None:
            return

        if drawing_source_for(resolved) is None:
            QMessageBox.information(
                self, "Cannot re-edit",
                "This figure was not created with the drawing tool, "
                "or its drawing data is missing.")
            return

        dlg = DrawingDialog(self._images_dir, self, existing_path=resolved)
        if dlg.exec() != QDialog.Accepted:
            return
        # A legacy drawing now has its SVG/PDF too, so LaTeX gets vectors.
        tfmt.setProperty(_P_FIGURE_SOURCE, "drawing")
        qtable.setFormat(tfmt)
        self._refresh_figure_image(qtable, resolved)
        if dlg.handoff_to_khervepaint:
            self.edit_in_khervepaint(resolved)

    def _refresh_figure_image(self, qtable: QTextTable,
                              img_path: Path) -> None:
        """Replace the image in row 0 of a figure table with the updated PNG."""
        cell = qtable.cellAt(0, 0)
        cursor = cell.firstCursorPosition()
        cursor.beginEditBlock()
        end = cell.lastCursorPosition()
        cursor.setPosition(end.position(), QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        bf = cursor.blockFormat()
        bf.setAlignment(Qt.AlignHCenter)
        cursor.setBlockFormat(bf)
        img = QImage(str(img_path))
        if not img.isNull():
            w, h = self._figure_display_size(
                qtable.format().property(_P_FIGURE_WIDTH)
                or "0.8\\textwidth", img)
            # Cache-buster so Qt doesn't show the stale version.
            url = QUrl(f"figure:{img_path}?v={time.time()}")
            self._edit.document().addResource(2, url, img)
            img_fmt = QTextImageFormat()
            img_fmt.setName(url.toString())
            img_fmt.setWidth(w)
            img_fmt.setHeight(h)
            cursor.insertImage(img_fmt)
        cursor.endEditBlock()
        self._on_text_changed()

    def insert_table(self) -> None:
        dlg = _InsertTableDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        from .serializer import escape_text
        r, co = dlg.dimensions()
        c = self._edit.textCursor()
        table = Table(rows=[["cell"] * co for _ in range(r)],
                      caption=escape_text(dlg.caption()),
                      label=dlg.label() or None,
                      alignment="")
        self._insert_table_widget(c, table)

    # ---- table context menu & manipulation ----

    def _current_table(self) -> QTextTable | None:
        """Return the QTextTable under the cursor, or None."""
        return self._edit.textCursor().currentTable()

    def _show_context_menu(self, pos) -> None:
        menu = self._edit.createStandardContextMenu()
        # Spell-check suggestions for the word at the right-click. The
        # word boundary is found via Qt's WordUnderCursor selection;
        # if the cursor is in whitespace this just produces an empty
        # selection and we skip the suggestion block entirely.
        word_cursor = self._edit.cursorForPosition(pos)
        word_cursor.select(QTextCursor.WordUnderCursor)
        word = word_cursor.selectedText().strip()
        if word and self._spell_highlighter.is_misspelled(word):
            self._prepend_spell_suggestions(menu, word_cursor, word)
        math_cursor = self._math_cursor_for_menu(pos)
        if math_cursor is not None:
            first = menu.actions()[0] if menu.actions() else None
            act = QAction("Open in equation editor…", menu)
            act.triggered.connect(
                lambda _=False, c=math_cursor: self._edit_math_at(c))
            menu.insertAction(first, act)
            if first is not None:
                menu.insertSeparator(first)
        fig_table = self._edit.cursorForPosition(pos).currentTable()
        if fig_table is not None and fig_table.format().property(
                _P_FIGURE_PATH) is not None:
            from .drawing_dialog import drawing_source_for
            resolved = self._resolve_image_path(
                fig_table.format().property(_P_FIGURE_PATH) or "")
            if resolved is not None and drawing_source_for(resolved) \
                    and resolved.with_suffix(".svg").exists():
                menu.addSeparator()
                menu.addAction(
                    "Edit drawing…",
                    lambda t=fig_table: self._edit_existing_figure(t))
                menu.addAction(
                    "Edit in KhervePaint",
                    lambda p=resolved: self.edit_in_khervepaint(p))
        qtable = self._current_table()
        if qtable is not None:
            menu.addSeparator()
            cursor = self._edit.textCursor()
            cell = qtable.cellAt(cursor)
            row, col = cell.row(), cell.column()

            menu.addAction("Insert row above",
                           lambda: self._table_insert_row(qtable, row))
            menu.addAction("Insert row below",
                           lambda: self._table_insert_row(qtable, row + 1))
            menu.addAction("Insert column left",
                           lambda: self._table_insert_col(qtable, col))
            menu.addAction("Insert column right",
                           lambda: self._table_insert_col(qtable, col + 1))
            menu.addSeparator()
            if qtable.rows() > 1:
                menu.addAction("Delete row",
                               lambda: self._table_delete_row(qtable, row))
            if qtable.columns() > 1:
                menu.addAction("Delete column",
                               lambda: self._table_delete_col(qtable, col))
        if self._extra_context_actions:
            menu.addSeparator()
            for label, callback in self._extra_context_actions:
                menu.addAction(label, callback)
        menu.exec(self._edit.viewport().mapToGlobal(pos))

    def _prepend_spell_suggestions(self, menu, word_cursor, word: str) -> None:
        """Insert spell-check suggestions at the top of the context
        menu for a misspelled `word`. Selecting a suggestion replaces
        the word in place; the "Add to dictionary" entry stops
        flagging it for the rest of the session."""
        suggestions = self._spell_highlighter.suggestions(word)
        # Capture the start/end of the word so the action callbacks
        # can replace it even if the user clicks elsewhere first.
        start = word_cursor.selectionStart()
        end = word_cursor.selectionEnd()
        existing_actions = menu.actions()
        first = existing_actions[0] if existing_actions else None

        def _replace_with(new_word: str):
            c = QTextCursor(self._edit.document())
            c.setPosition(start)
            c.setPosition(end, QTextCursor.KeepAnchor)
            # Preserve the existing char format of the word — bold,
            # italic, font — so the correction inherits the same
            # styling instead of falling back to a plain insert.
            fmt = c.charFormat()
            c.insertText(new_word, fmt)

        if suggestions:
            for s in suggestions:
                act = QAction(s, menu)
                act.triggered.connect(lambda checked=False, w=s: _replace_with(w))
                menu.insertAction(first, act)
        else:
            no_sug = QAction("(no suggestions)", menu)
            no_sug.setEnabled(False)
            menu.insertAction(first, no_sug)

        menu.insertSeparator(first)
        add_act = QAction(f"Add “{word}” to dictionary", menu)
        add_act.triggered.connect(
            lambda checked=False, w=word: self._spell_highlighter.add_to_dictionary(w))
        menu.insertAction(first, add_act)
        menu.insertSeparator(first)

    def _table_insert_row(self, qtable: QTextTable, at: int) -> None:
        qtable.insertRows(at, 1)
        self._apply_table_rules(qtable)

    def _table_columns_changed(self, qtable: QTextTable) -> None:
        # The stored column spec no longer matches the column count;
        # drop it so the serializer derives a fresh one.
        tfmt = qtable.format()
        tfmt.setProperty(_P_TABLE_ALIGNMENT, "")
        qtable.setFormat(tfmt)
        self._apply_table_rules(qtable)

    def _table_insert_col(self, qtable: QTextTable, at: int) -> None:
        qtable.insertColumns(at, 1)
        self._table_columns_changed(qtable)

    def _table_delete_row(self, qtable: QTextTable, at: int) -> None:
        qtable.removeRows(at, 1)
        self._apply_table_rules(qtable)

    def _table_delete_col(self, qtable: QTextTable, at: int) -> None:
        qtable.removeColumns(at, 1)
        self._table_columns_changed(qtable)

    def insert_raw_latex(self) -> None:
        text, ok = QInputDialog.getMultiLineText(self, "Insert raw LaTeX",
                                                 "LaTeX (verbatim):")
        if not ok or not text.strip(): return
        self._insert_raw_block(text)

    def insert_code_block(self) -> None:
        """Insert a syntax-highlighted code listing (lstlisting) at the
        cursor. Wraps the user's content in \\begin{lstlisting}...
        \\end{lstlisting}; relies on the listings package + user's
        \\lstset configuration for frame / line numbers / colours."""
        text, ok = QInputDialog.getMultiLineText(
            self, "Insert code block", "Code:")
        if not ok or not text.strip(): return
        body = text.rstrip("\n")
        wrapped = f"\\begin{{lstlisting}}\n{body}\n\\end{{lstlisting}}"
        self._insert_raw_block(wrapped)

    def _insert_raw_block(self, latex: str) -> None:
        """Shared helper: drop a RawLatex block at the cursor with the
        right per-type colour based on the content. No "[RAW] " /
        "[CODE] " label is prepended — the coloured background and
        the userState already mark this as a raw block."""
        c = self._edit.textCursor()
        c.beginEditBlock()
        c.insertBlock()
        c.block().setUserState(_STATE_RAW)
        if "\\begin{lstlisting}" in latex or "\\begin{verbatim}" in latex:
            c.setBlockFormat(_code_block_format())
            color = "#1a3a8c"
        elif "\\begin{thebibliography}" in latex:
            c.setBlockFormat(_bibliography_block_format())
            color = "#6a1b9a"
        else:
            c.setBlockFormat(_raw_block_format())
            color = "#b71c1c"
        visible = latex.replace("\n", _LINE_SEP)
        c.insertText(visible, _typed_stub_char_format(color))
        c.insertBlock(QTextBlockFormat(), QTextCharFormat())
        c.block().setUserState(_STATE_PARAGRAPH)
        c.endEditBlock()

    def insert_compile_marker(self, marker_type: str) -> None:
        """Insert a compile-range or not-compile marker at the cursor."""
        from .compiler import (_COMPILE_START, _COMPILE_END,
                               _NOT_COMPILE_START, _NOT_COMPILE_END)
        mapping = {
            "start": _COMPILE_START,
            "end": _COMPILE_END,
            "not_start": _NOT_COMPILE_START,
            "not_end": _NOT_COMPILE_END,
        }
        self._insert_raw_block(mapping[marker_type])

    def insert_page_break(self) -> None:
        self._insert_raw_block(r"\newpage")

    def insert_multicol_region(self) -> None:
        """Insert a 2-column \\begin{multicols}{2}...\\end{multicols} block
        with placeholder text. Only the content inside the environment
        flows in two columns; the rest of the document stays one-column.
        For a whole-document two-column layout, use
        File > Document settings > Layout > Two-column document."""
        self._insert_raw_block(
            "\\begin{multicols}{2}\n"
            "Replace this paragraph with the content that should flow "
            "across two columns. Add as many paragraphs as you like — "
            "everything between \\begin{multicols} and \\end{multicols} "
            "is balanced into the two columns automatically.\n"
            "\\end{multicols}")

    def insert_horizontal_rule(self) -> None:
        self._insert_raw_block(r"\hrulefill")

    def current_heading_level(self) -> int:
        """Returns -1 = Title, -2 = Author, -3 = Abstract, -4 = Keywords,
        -5 = Chapter, -6 = Frame, 0 = Body, 1..5 = Heading,
        -99 = non-text block.
        Starred (unnumbered) headings return the same code as their
        numbered counterparts — use is_heading_numbered() to distinguish."""
        state = self._edit.textCursor().block().userState()
        if state == _STATE_TITLE: return -1
        if state == _STATE_AUTHOR: return -2
        if state == _STATE_ABSTRACT: return -3
        if state == _STATE_KEYWORDS: return -4
        if state in (_STATE_CHAPTER, _STATE_CHAPTER_STAR): return -5
        if state == _STATE_FRAME: return -6
        if state == _STATE_AFFILIATION: return -7
        if state == _STATE_CORRESPONDENCE: return -8
        if 1 <= state <= 5: return state
        if _STATE_HEADING_STAR_BASE < state <= _STATE_HEADING_STAR_BASE + 5:
            return state - _STATE_HEADING_STAR_BASE
        if state == _STATE_PARAGRAPH: return 0
        return -99

    def is_mark_active(self, mark: str) -> bool:
        f = self._edit.currentFont()
        fmt = self._edit.currentCharFormat()
        if mark == "bold": return f.bold()
        if mark == "italic": return f.italic()
        if mark == "underline": return f.underline()
        if mark == "strikethrough": return f.strikeOut()
        if mark == "smallcaps": return f.capitalization() == QFont.SmallCaps
        if mark == "code": return f.family().lower() == "consolas"
        if mark == "subscript": return fmt.verticalAlignment() == QTextCharFormat.AlignSubScript
        if mark == "superscript": return fmt.verticalAlignment() == QTextCharFormat.AlignSuperScript
        return False

    # ---------- internals ----------

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self._edit.mergeCurrentCharFormat(fmt)

    def _on_text_changed(self) -> None:
        if self._building: return
        self._debounce.start()
        block = self._edit.textCursor().block()
        if block.userState() == _STATE_MATH_BLOCK:
            self._math_refresh.start()

    def set_heading_offset(self, counters: list[int] | None) -> None:
        """Numbered headings already used by earlier documents of a
        project, per level (index 0 = chapter). LaTeX keeps counting
        across \\include, so this document's first section continues
        from there instead of restarting at 1."""
        counters = list(counters or [0] * 6)[:6]
        counters += [0] * (6 - len(counters))
        if counters != self._heading_offset:
            self._heading_offset = counters
            self._apply_page_layout()

    def sync_pages_to_pdf(self) -> None:
        """Re-paginate after a compile so sheets start where the PDF's
        pages start."""
        self._apply_page_layout()
        self._resize_to_document()

    def _pdf_page_start_blocks(self) -> set[int]:
        """Blocks the last compiled PDF starts a page with.

        Only pages that begin at the start of a block (a heading, a new
        paragraph) are forced; a page that starts mid-paragraph is left
        to the layout, which breaks inside that paragraph on its own.
        Anchors are matched in order, each search starting after the
        previous hit, so a phrase that also occurs earlier can't steal
        the break."""
        from .paged_edit import _normalize_for_match, anchor_offset
        anchors = getattr(self._edit, "_page_anchors", None) or []
        out: set[int] = set()
        block = self._edit.document().firstBlock()
        for _page, snippet in anchors:
            key = _normalize_for_match(snippet)[:16]
            if len(key) < 3:
                continue
            probe = block
            while probe.isValid():
                if QTextCursor(probe).currentTable() is None:
                    at = anchor_offset(probe.text().replace("\ufffc", ""),
                                       key)
                    if at == 0:
                        out.add(probe.blockNumber())
                        block = probe.next()
                        break
                    if at > 0:             # page starts mid-paragraph
                        block = probe
                        break
                probe = probe.next()
        return out

    def _has_chapter_blocks(self) -> bool:
        block = self._edit.document().firstBlock()
        while block.isValid():
            if block.userState() == _STATE_CHAPTER:
                return True
            block = block.next()
        return False

    def _refresh_reference_labels(self) -> None:
        """Re-resolve citation numbers and \\ref targets after an edit —
        adding a citation or a section renumbers the ones after it."""
        if self._building:
            return
        self._resolver = ReferenceResolver(self.get_document(), self._doc_dir)
        self._apply_page_layout()   # heading numbers shift as users edit
        doc = self._edit.document()
        updates = []
        block = doc.begin()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    fmt = frag.charFormat()
                    cite = fmt.property(_P_CITATION)
                    ref = fmt.property(_P_CROSSREF)
                    want = None
                    if cite:
                        keys, _, style = cite.partition("|")
                        want = self._resolver.cite_text(
                            [k for k in keys.split(",") if k], style or "cite")
                    elif ref:
                        label, _, kind = ref.partition("|")
                        want = self._resolver.ref_text(label, kind or "ref")
                    if want is not None and want != frag.text():
                        updates.append((frag.position(), frag.length(),
                                        want, fmt))
                it += 1
            block = block.next()
        if not updates:
            return
        self._building = True
        edit = QTextCursor(doc)
        edit.joinPreviousEditBlock()
        try:
            # Back to front so earlier positions stay valid.
            for pos, length, text, fmt in reversed(updates):
                c = QTextCursor(doc)
                c.setPosition(pos)
                c.setPosition(pos + length, QTextCursor.KeepAnchor)
                c.insertText(text, fmt)
        finally:
            edit.endEditBlock()
            self._building = False

    def _resize_math_images(self) -> None:
        """Re-fit every equation image after a zoom or body-size change."""
        doc = self._edit.document()
        was_building = self._building
        self._building = True
        edit = QTextCursor(doc)
        edit.joinPreviousEditBlock()
        try:
            block = doc.begin()
            while block.isValid():
                it = block.begin()
                while not it.atEnd():
                    frag = it.fragment()
                    fmt = frag.charFormat() if frag.isValid() else None
                    if fmt is not None and fmt.isImageFormat() \
                            and fmt.property(_P_MATH):
                        img_fmt = fmt.toImageFormat()
                        img = self._math_sources.get(img_fmt.name())
                        if img is not None:
                            w, h = self._add_math_resource(
                                QUrl(img_fmt.name()), img)
                            img_fmt.setWidth(w)
                            img_fmt.setHeight(h)
                            c = QTextCursor(doc)
                            c.setPosition(frag.position())
                            c.setPosition(frag.position() + frag.length(),
                                          QTextCursor.KeepAnchor)
                            c.setCharFormat(img_fmt)
                    it += 1
                block = block.next()
        finally:
            edit.endEditBlock()
            self._building = was_building

    def _refresh_math_images(self) -> None:
        """Re-render math preview images for any math block whose LaTeX
        source has changed since the image was last generated."""
        if self._building:
            return
        doc = self._edit.document()
        block = doc.begin()
        while block.isValid():
            if block.userState() == _STATE_MATH_BLOCK:
                text = block.text()
                raw = text.replace("\ufffc", "").replace(_MATH_SEP, "").strip(_LINE_SEP).strip()
                latex = raw.replace(_LINE_SEP, "\n")
                if latex:
                    self._update_math_image_in_block(block, latex)
                else:
                    self._remove_math_image_from_block(block)
            block = block.next()

    def _update_math_image_in_block(self, block, latex: str) -> None:
        """Replace the existing math preview image in *block* with a
        freshly rendered one for *latex*."""
        png_path = self._math_png(latex)
        if png_path is None or not png_path.exists():
            return
        img = QImage(str(png_path))
        if img.isNull():
            return
        url = QUrl.fromLocalFile(str(png_path))
        # Walk fragments to find the existing image char (\ufffc) and
        # update its QTextImageFormat to point at the new PNG.
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid() and frag.text() == "\ufffc":
                fmt = frag.charFormat()
                if fmt.isImageFormat():
                    img_fmt = fmt.toImageFormat()
                    if img_fmt.name() == url.toString():
                        return  # already up to date
                    w, h = self._add_math_resource(url, img)
                    img_fmt.setName(url.toString())
                    img_fmt.setWidth(w)
                    img_fmt.setHeight(h)
                    img_fmt.setProperty(_P_MATH, latex)
                    cursor = QTextCursor(block)
                    cursor.setPosition(frag.position())
                    cursor.setPosition(frag.position() + frag.length(),
                                       QTextCursor.KeepAnchor)
                    self._building = True
                    cursor.setCharFormat(img_fmt)
                    self._building = False
                    return
            it += 1

    def _remove_math_image_from_block(self, block) -> None:
        """Delete the image character from a math block whose LaTeX was
        removed, so the orphaned preview picture disappears."""
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid() and frag.text() == "\ufffc":
                cursor = QTextCursor(block)
                cursor.setPosition(frag.position())
                cursor.setPosition(frag.position() + frag.length(),
                                   QTextCursor.KeepAnchor)
                self._building = True
                cursor.removeSelectedText()
                self._building = False
                return
            it += 1


def _stub_char_format() -> QTextCharFormat:
    fmt = QTextCharFormat()
    f = QFont("Consolas"); f.setStyleHint(QFont.Monospace); f.setPointSize(10)
    fmt.setFont(f); fmt.setForeground(QColor("#444"))
    return fmt
