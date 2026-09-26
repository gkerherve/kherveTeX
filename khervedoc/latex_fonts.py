"""Load LaTeX's own body font (Latin Modern) for the visual editor.

With the real Computer Modern metrics on screen, lines wrap on the same
words as in the PDF, so pages end where LaTeX's pages end. The fonts
come from tectonic's cache (the installer ships it; any compile fills
it), so nothing extra is bundled. All Latin Modern design sizes share
the family name "Latin Modern Roman", so only one size is loaded at a
time: the 12pt cut for 12pt documents, the 10pt cut otherwise — the
same choice LaTeX makes between cmr12 and cmr10.
"""
from __future__ import annotations

from pathlib import Path

FAMILY = "Latin Modern Roman"
_STYLES = ("regular", "bold", "italic", "bolditalic")

_loaded_design: int | None = None
_font_ids: list[int] = []
_font_dir: Path | None | bool = False   # False = not looked up yet


def _find_font_dir() -> Path | None:
    global _font_dir
    if _font_dir is not False:
        return _font_dir
    from .compiler import (_find_tectonic, default_tectonic_cache_dir,
                           query_tectonic_cache_dir)
    roots = []
    tec = _find_tectonic()
    if tec:
        d = query_tectonic_cache_dir(tec)
        if d is not None:
            roots.append(d)
    roots.append(default_tectonic_cache_dir())
    _font_dir = None
    for root in roots:
        hits = sorted(Path(root).glob("data/*/lmroman12-regular.otf"))
        if hits:
            _font_dir = hits[0].parent
            break
    return _font_dir


def design_size(body_pt: float) -> int:
    return 12 if body_pt >= 12 else 10


def ensure_loaded(body_pt: float) -> bool:
    """Make "Latin Modern Roman" available at the design size matching
    *body_pt*. Returns False when the fonts aren't in the cache yet."""
    global _loaded_design
    from PySide6.QtGui import QFontDatabase
    want = design_size(body_pt)
    if _loaded_design == want:
        return True
    font_dir = _find_font_dir()
    if font_dir is None:
        return False
    for fid in _font_ids:
        QFontDatabase.removeApplicationFont(fid)
    _font_ids.clear()
    for style in _STYLES:
        f = font_dir / f"lmroman{want}-{style}.otf"
        if f.exists():
            fid = QFontDatabase.addApplicationFont(str(f))
            if fid >= 0:
                _font_ids.append(fid)
    _loaded_design = want if _font_ids else None
    return bool(_font_ids)


# LaTeX's \baselineskip for the standard class sizes, in pt.
_BASELINESKIP = {10: 12.0, 11: 13.6, 12: 14.5}
# setspace's \onehalfspacing / \doublespacing stretch per class size.
_ONEHALF = {10: 1.25, 11: 1.213, 12: 1.241}
_DOUBLE = {10: 1.667, 11: 1.618, 12: 1.655}


def baselineskip_pt(body_pt: int, line_spacing: float) -> float:
    """Distance between body lines in the PDF, as LaTeX sets it."""
    size = min(_BASELINESKIP, key=lambda s: abs(s - body_pt))
    skip = _BASELINESKIP[size] * body_pt / size
    if abs(line_spacing - 1.5) < 0.01:
        stretch = _ONEHALF[size]
    elif abs(line_spacing - 2.0) < 0.01:
        stretch = _DOUBLE[size]
    else:
        stretch = line_spacing or 1.0
    return skip * stretch
