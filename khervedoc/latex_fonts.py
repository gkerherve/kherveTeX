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

import os
import re
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


# ----- the fonts a class really prints with -----
#
# Every Latin Modern design size calls itself "Latin Modern Roman", so one
# Qt family could hold only one cut. Each design size is registered under
# a family of its own (a renamed copy) so a 17pt title, 12pt body and 10pt
# abstract can share a page, and bold and italic still work by family.

_DESIGN_RE = re.compile(
    r"^(LMRomanCaps|LMRomanSlant|LMRomanDunh|LMRoman|LMSans|LMMono)(\d+)-(\w+)$")
# PDF fonts without an OpenType file of their own: the same design in a
# file that exists (Computer Modern is Latin Modern's source, Nimbus Roman
# is the Times clone TeX Gyre Termes also derives from).
_ALIASES = {
    "CMR": "LMRoman{}-Regular", "CMB": "LMRoman{}-Bold",
    "CMBX": "LMRoman{}-Bold", "CMTI": "LMRoman{}-Italic",
    "CMCSC": "LMRomanCaps{}-Regular", "CMSS": "LMSans{}-Regular",
}
_OTHER_FAMILIES = (
    # PDF name prefix, Qt family, {(bold, italic): file}
    ("LinBiolinumO", "Linux Biolinum O", {
        (0, 0): "LinBiolinum_R.otf", (1, 0): "LinBiolinum_RB.otf",
        (0, 1): "LinBiolinum_RI.otf"}),
    ("LinLibertineO", "Linux Libertine O", {
        (0, 0): "LinLibertine_R.otf", (1, 0): "LinLibertine_RB.otf",
        (0, 1): "LinLibertine_RI.otf", (1, 1): "LinLibertine_RBI.otf"}),
    ("TeXGyreHeros", "TeX Gyre Heros", {
        (0, 0): "texgyreheros-regular.otf", (1, 0): "texgyreheros-bold.otf",
        (0, 1): "texgyreheros-italic.otf",
        (1, 1): "texgyreheros-bolditalic.otf"}),
    ("TeXGyreTermesX", "TeX Gyre Termes", {
        (0, 0): "TeXGyreTermesX-Regular.otf",
        (1, 0): "TeXGyreTermesX-Bold.otf",
        (0, 1): "TeXGyreTermesX-Italic.otf",
        (1, 1): "TeXGyreTermesX-BoldItalic.otf"}),
    ("NimbusRomNo9L", "TeX Gyre Termes", {
        (0, 0): "TeXGyreTermesX-Regular.otf",
        (1, 0): "TeXGyreTermesX-Bold.otf",
        (0, 1): "TeXGyreTermesX-Italic.otf",
        (1, 1): "TeXGyreTermesX-BoldItalic.otf"}),
    ("DejaVuSerif", "DejaVu Serif", {
        (0, 0): "DejaVuSerif.ttf", (1, 0): "DejaVuSerif-Bold.ttf",
        (0, 1): "DejaVuSerif-Italic.ttf"}),
)
_FALLBACKS = {
    "serif": ["Latin Modern Roman", "CMU Serif", "Times New Roman", "Times"],
    "sans": ["Latin Modern Sans", "Helvetica", "Arial"],
}
_registered: dict[str, str] = {}


def weight_and_slant(name: str) -> tuple[bool, bool]:
    """Bold and italic as a PDF font name spells them."""
    style = name.split("-")[-1] if "-" in name else name
    bold = "Bold" in style or "Medi" in style or name.startswith("CMB") \
        or (name.startswith("Lin") and style[-2:] in ("OB", "BI"))
    italic = any(w in style for w in ("Italic", "Oblique", "Ital")) \
        or name.startswith("CMTI") or (name.startswith("Lin") and style.endswith("OI"))
    return bold, italic


def _rename_copy(src: Path, family: str, style: str) -> Path | None:
    """A copy of *src* whose name table says *family* / *style*, kept in a
    cache folder because rewriting a font takes a noticeable moment."""
    import tempfile
    cache = Path(tempfile.gettempdir()) / "khervetex-fonts"
    out = cache / f"{family.replace(' ', '')}-{style.replace(' ', '')}.otf"
    if out.exists():
        return out
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    font = TTFont(str(src))
    ps = f"{family.replace(' ', '')}-{style.replace(' ', '')}"
    names = font["name"]
    names.names = [n for n in names.names if n.nameID not in (16, 17, 21, 22)]
    for rec in list(names.names):
        if rec.nameID in (1, 2, 3, 4, 6):
            value = {1: family, 2: style, 3: ps, 4: f"{family} {style}",
                     6: ps}[rec.nameID]
            names.setName(value, rec.nameID, rec.platformID, rec.platEncID,
                          rec.langID)
    cache.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(f".{os.getpid()}.tmp")
    font.save(str(tmp))
    font.close()
    os.replace(tmp, out)
    return out


def _register_design(stem: str, size: str) -> str | None:
    """Register every weight of one Latin Modern design under one family."""
    family = f"KTeX {stem}{size}"
    if family in _registered:
        return _registered[family] or None
    from PySide6.QtGui import QFontDatabase
    font_dir = _find_font_dir()
    found = False
    if font_dir is not None:
        sans = stem == "LMSans"
        for style, fname in (
                ("Regular", "regular"), ("Bold", "bold"),
                ("Italic", "oblique" if sans else "italic"),
                ("Bold Italic", "boldoblique" if sans else "bolditalic")):
            src = font_dir / f"{stem.lower()}{size}-{fname}.otf"
            if not src.exists():
                continue
            copy = _rename_copy(src, family, style)
            if copy is not None and \
                    QFontDatabase.addApplicationFont(str(copy)) >= 0:
                found = True
    _registered[family] = family if found else ""
    return family if found else None


def pdf_font(name: str) -> tuple[str, bool, bool]:
    """The Qt family, bold and italic that draw a font named *name* in a
    PDF. Falls back to the closest installed family when the cache has
    no file for it yet."""
    from PySide6.QtGui import QFontDatabase
    m = re.match(r"^(CM[A-Z]+?)(\d+)$", name)
    if m and m.group(1) in _ALIASES:
        name = _ALIASES[m.group(1)].format(m.group(2))
    bold, italic = weight_and_slant(name)
    m = _DESIGN_RE.match(name)
    if m:
        family = _register_design(m.group(1), m.group(2))
        if family:
            return family, bold, italic
    else:
        font_dir = _find_font_dir()
        for prefix, family, files in _OTHER_FAMILIES:
            if name.startswith(prefix):
                if family not in _registered:
                    real = ""
                    if font_dir is not None:
                        for fname in files.values():
                            if not (font_dir / fname).exists():
                                continue
                            fid = QFontDatabase.addApplicationFont(
                                str(font_dir / fname))
                            names = (QFontDatabase.applicationFontFamilies(fid)
                                     if fid >= 0 else [])
                            # What the file calls itself decides, not us.
                            real = real or (names[0] if names else "")
                    _registered[family] = real
                if _registered[family]:
                    return _registered[family], bold, italic
                break
    installed = set(QFontDatabase.families())
    kind = "sans" if "Sans" in name or "Heros" in name else "serif"
    for family in _FALLBACKS[kind]:
        if family in installed:
            return family, bold, italic
    return ("Helvetica" if kind == "sans" else "Times"), bold, italic
