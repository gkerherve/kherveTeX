"""What the visual tab draws for a document class: the table measured from
real PDFs (class_looks.py), and how heading numbers come out in that class."""
from __future__ import annotations

import re

from .class_looks import LOOKS

_LOWER = {k.lower(): k for k in LOOKS}


def _entry(cls: str) -> dict | None:
    name = (cls or "article").split(",")[0].strip().lower()
    key = _LOWER.get(name)
    return LOOKS.get(key) if key else None


def is_broken(cls: str) -> str:
    """Why this class has no usable PDF to copy, or "" when it has one."""
    entry = _entry(cls)
    if entry is None:
        return ""
    return next(iter(entry.values())).get("broken", "")


def look_for(cls: str, body_pt: float) -> dict:
    """The measured look of *cls* at *body_pt*. A class that cannot compile
    has nothing to match, so it is drawn as an article."""
    entry = _entry(cls)
    if entry is None or next(iter(entry.values())).get("broken"):
        entry = LOOKS["article"]
    return entry[min(entry, key=lambda pt: abs(pt - (body_pt or 12)))]


def _roman(n: int) -> str:
    out = ""
    for value, digits in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out += digits
            n -= value
    return out


def _alpha(n: int) -> str:
    return chr(ord("A") + (max(n, 1) - 1) % 26)


def number_label(prefix: str, dotted: str) -> str:
    """Heading number in the form this class printed: *prefix* is what the
    probe heading showed ("1.1.", "I.", "A.", "1)", "a)"), *dotted* the
    plain counters of this heading ("2.3"). No prefix means unnumbered."""
    prefix = (prefix or "").strip()
    if not prefix or not dotted:
        return ""
    n = int(dotted.split(".")[-1] or 0)
    m = re.fullmatch(r"([IVX]+|[A-Z]|[a-z]|[\d.]*\d)([.)]?)", prefix)
    if not m:
        return prefix if "Chapter" not in prefix else f"Chapter {n}"
    head, tail = m.group(1), m.group(2)
    if head == "I":
        return _roman(n) + tail
    if head.isupper():
        return _alpha(n) + tail
    if head.islower():
        return _alpha(n).lower() + tail
    if tail == ")":
        return f"{n}{tail}"
    return dotted + tail
