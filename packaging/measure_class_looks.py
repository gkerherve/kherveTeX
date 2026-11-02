"""Measure how every document class really typesets each style and write
the result to khervedoc/class_looks.py, which the visual tab draws from.

For each class this compiles a probe document through the real serializer
and reads the PDF back: font, size, colour, alignment, numbering and the
baseline distances around the title block, headings and body text. Run it
after adding a document class or changing how the serializer sets one up:

    python packaging/measure_class_looks.py [class ...]
"""
from __future__ import annotations

import json
import os
import pprint
import re
import statistics
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz  # noqa: E402

from khervedoc.compiler import compile_tex  # noqa: E402
from khervedoc.editor import TEMPLATE_CHOICES  # noqa: E402
from khervedoc.model import (  # noqa: E402
    Abstract, Affiliation, Author, Correspondence, DocMeta, Document, Frame,
    Keywords, Paragraph, Section, Text, Title,
)
from khervedoc.serializer import (  # noqa: E402
    _STANDARD_SERIALIZER_CLASSES, serialize_document,
)
from khervedoc.model import class_supports_chapter  # noqa: E402

OUT = ROOT / "khervedoc" / "class_looks.py"

FILL = ("Bodyfill words run along here so that this paragraph is long enough "
        "to wrap across several lines of the page and show the baseline "
        "distance and the justification of the class in use, whichever "
        "column width it may choose. ")
MARKS = {
    "title": "Titlemark", "author": "Authormark", "affiliation": "Affilmark",
    "correspondence": "Corrmark", "abstract": "Abstractmark",
    "keywords": "Keywordmark", "frame": "Framemark",
    "h1": "Hoenmark", "h2": "Htwomark", "h3": "Hthreemark",
    "h4": "Hfourmark", "h5": "Hfivemark",
}
_FILL_WORDS = set(re.findall(r"[a-z]+", FILL.lower()))
AGAIN = ("Haonemark", "Hatwomark", "Hathreemark", "Hafourmark", "Hafivemark")
MONTHS = ("January|February|March|April|May|June|July|August|September|"
          "October|November|December")


def probe(cls: str, pt: int, correspondence: bool = True, levels: int = 5,
          **meta) -> Document:
    def para(tag, n=2):
        return Paragraph(children=[Text(f"{tag} " + FILL * n)])
    kids = [
        Title(children=[Text("Titlemark Words")]),
        Author(children=[Text("Authormark Person")]),
        Affiliation(children=[Text("Affilmark University")]),
        *([Correspondence(children=[Text("Corrmark Address")])]
          if correspondence else []),
        Abstract(children=[Text("Abstractmark " + FILL)]),
        Keywords(children=[Text("Keywordmark, words")]),
    ]
    if cls == "beamer":
        kids.append(Frame(children=[Text("Framemark Slide")]))
    kids += [
        Section(level=1, children=[Text("Hoenmark Heading")]),
        para("Paraonemark"), para("Paratwomark"),
        Section(level=2, children=[Text("Htwomark Heading")]), para("Parathree"),
        Section(level=3, children=[Text("Hthreemark Heading")]), para("Parafour"),
        Section(level=4, children=[Text("Hfourmark Heading")]), para("Parafive"),
        Section(level=5, children=[Text("Hfivemark Heading")]), para("Parasix"),
    ]
    # Every level again after ordinary text, where the first round's h1 sits
    # under the keywords and any of them may land at the top of a page.
    for n, mark in enumerate(AGAIN, 1):
        kids += [Section(level=n, children=[Text(f"{mark} Heading")]),
                 para("Parathen")]
    # Enough text to fill a whole page, so the text height can be read.
    kids += [para("Tailmark") for _ in range(30)]
    kids = [k for k in kids if not (isinstance(k, Section) and k.level > levels)]
    return Document(meta=DocMeta(
        title="Titlemark Words", author="Authormark Person",
        documentclass=cls, body_font_pt=pt, **meta), children=kids)


def _text(s: str) -> str:
    return (s.replace("ﬀ", "ff").replace("ﬁ", "fi")
            .replace("ﬂ", "fl").replace("ﬃ", "ffi"))


def read_rules(pdf: Path) -> list[dict]:
    """Thin horizontal lines on each page: a header's or footer's rule."""
    d = fitz.open(pdf)
    out = []
    for n, page in enumerate(d):
        for g in page.get_drawings():
            r = g["rect"]
            if r.width > 40 and r.height < 1.6:
                out.append(dict(page=n, x0=r.x0, x1=r.x1, y=(r.y0 + r.y1) / 2,
                                width=max(r.height, g.get("width") or 0.4)))
    d.close()
    return out


def read_words(pdf: Path) -> dict:
    """Word boxes per page: what a run-in heading ends with, and how far the
    paragraph on its line starts from it."""
    d = fitz.open(pdf)
    out = {n: page.get_text("words") for n, page in enumerate(d)}
    d.close()
    return out


def run_in_end(words, line) -> dict:
    """Punctuation after a run-in heading and the gap before the text."""
    on = sorted((w for w in words.get(line["page"], [])
                 if w[1] - 1 <= line["y"] <= w[3] + 1), key=lambda w: w[0])
    for prev, word in zip(on, on[1:]):
        if re.match(r"Para|Tailmark", word[4]):
            m = re.search(r"Heading(.*)$", prev[4])
            return dict(suffix=m.group(1) if m else "",
                        run_gap=round(word[0] - prev[2], 1))
    return {}


def read_lines(pdf: Path) -> tuple[list[dict], float, float, int]:
    d = fitz.open(pdf)
    out = []
    for n, page in enumerate(d):
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                sp = [s for s in l["spans"] if s["text"].strip()]
                if not sp:
                    continue
                out.append(dict(
                    page=n, x0=l["bbox"][0], x1=l["bbox"][2],
                    y=sp[0]["origin"][1],
                    text=_text("".join(s["text"] for s in l["spans"])),
                    spans=[dict(t=_text(s["text"]), font=s["font"],
                                size=round(s["size"], 2), color=s["color"],
                                x0=s["bbox"][0], x1=s["bbox"][2])
                           for s in sp]))
    r = d[0].rect
    pages = d.page_count
    d.close()
    # Reading order within a page: columns stay in the order TeX wrote them.
    return out, r.width, r.height, pages


def _hex(c: int) -> str:
    return f"#{c:06x}"


def body_area(lines) -> dict:
    tail = [l for l in lines if "Bodyfill" in l["text"] or
            re.search(r"\b(wrap|baseline|justification|column)\b", l["text"])]
    if not tail:
        return {}
    # Full lines only: the short last line of a paragraph says nothing
    # about the right edge.
    left = statistics.median(sorted(l["x0"] for l in tail)[:max(1, len(tail) // 3)])
    span_font = statistics.mode(l["spans"][0]["font"] for l in tail)
    size = statistics.mode(l["spans"][0]["size"] for l in tail)
    gaps = []
    for a, b in zip(lines, lines[1:]):
        if a["page"] == b["page"] and a in tail and b in tail \
                and 0 < b["y"] - a["y"] < size * 3:
            gaps.append(round(b["y"] - a["y"], 1))
    leading = statistics.mode(gaps) if gaps else round(size * 1.2, 1)
    width = statistics.median(l["x1"] - l["x0"] for l in tail)
    right = max(l["x1"] for l in tail)
    second = [l for l in tail if l["x0"] > left + width * 0.7]
    cols = 2 if second else 1
    colsep = 0.0
    if second:
        col_w = max(l["x1"] for l in tail if l["x0"] < left + width * 0.7) - left
        colsep = min(l["x0"] for l in second) - (left + col_w)
    return dict(left=left, right=right, font=span_font, size=size,
                leading=leading, cols=cols, colsep=round(max(colsep, 0), 1))


def find(lines, mark) -> dict | None:
    low = mark.lower()
    for l in lines:
        if low in l["text"].lower():
            return l
    return None


def style_of(lines, mark, area, W, words=None) -> dict | None:
    line = find(lines, mark)
    if line is None:
        return None
    i = lines.index(line)
    low = mark.lower()
    # The mark's own span: a run-in "Keywords:" in front is not the style.
    span = next((s for s in line["spans"] if low in s["t"].lower()),
                line["spans"][-1])
    at = line["text"].lower().index(low)
    prefix = line["text"][:at].strip()
    # A number can come out as a line of its own at the same height.
    x0 = line["x0"]
    num_gap = None
    if not prefix:
        same = [l for l in lines if l is not line and l["page"] == line["page"]
                and abs(l["y"] - line["y"]) < 1 and l["x1"] <= line["x0"] + 1]
        if same:
            prefix = same[-1]["text"].strip()
            x0 = same[-1]["x0"]
            num_gap = round(line["x0"] - same[-1]["x1"], 1)
    elif span["t"].lower().startswith(low):
        before = [p for p in line["spans"] if p["x1"] <= span["x0"] + 0.5]
        if before:
            num_gap = round(span["x0"] - before[-1]["x1"], 1)
    prev = next((l for l in reversed(lines[:i]) if l["page"] == line["page"]
                 and abs(l["y"] - line["y"]) > 1), None)
    nxt = next((l for l in lines[i + 1:] if l["page"] == line["page"]
                and abs(l["y"] - line["y"]) > 1), None)
    # Centred about the text block or about its column.
    left, right = area["left"], area["right"]
    col_w = (right - left - area["colsep"]) / 2 if area["cols"] == 2 else None
    centres = [(left + right) / 2]
    if col_w:
        centres += [left + col_w / 2, right - col_w / 2]
    mid = (x0 + line["x1"]) / 2
    centred = x0 > left + 3 and any(abs(mid - c) < 2.5 for c in centres)
    # Set across both columns: wider than one, or centred on the whole page.
    fills = col_w and (line["x1"] - x0 > col_w * 1.1
                       or abs(mid - (left + right) / 2) < 2.5)
    letters = re.sub(r"[^A-Za-z]", "", mark + "")
    src = line["text"][at:at + len(mark)]
    out = dict(
        font=span["font"], size=span["size"], color=_hex(span["color"]),
        align="center" if centred else "left",
        # From its own column's edge: a heading can land in the second one.
        indent=0.0 if centred else round(max(0, x0 - (
            right - col_w if col_w and x0 >= right - col_w - 2 else left)), 1),
        upper=src == src.upper() and letters != letters.upper(),
        prefix=prefix, num_gap=num_gap, page=line["page"],
        run_in=bool(re.search(r"Para\w+|Tailmark", line["text"])) or any(
            l["page"] == line["page"] and abs(l["y"] - line["y"]) < 1
            and l["x0"] >= line["x1"] - 1 and re.match(r"Para", l["text"])
            for l in lines),
        above=round(line["y"] - prev["y"], 1) if prev else None,
        below=round(nxt["y"] - line["y"], 1) if nxt else None,
        top=round(line["y"], 1),
        wide=bool(fills),
    )
    if out["run_in"] and words:
        out.update(run_in_end(words, line))
    return out


def measure_block(lines, mark, area, W) -> dict:
    """Side insets and leading of a multi-line block (the abstract)."""
    line = find(lines, mark)
    if line is None:
        return {}
    i = lines.index(line)
    rest = []
    for l in lines[i + 1:i + 4]:
        if l["page"] == line["page"] and l["spans"][0]["size"] == \
                line["spans"][-1]["size"]:
            rest.append(l)
    if not rest:
        return {}
    x0 = rest[0]["x0"]
    x1 = max(l["x1"] for l in rest)
    # Insets from the block's own column, not the whole text block.
    left, right = area["left"], area["right"]
    if area["cols"] == 2:
        col_w = (right - left - area["colsep"]) / 2
        if x1 <= left + col_w + 2:
            right = left + col_w
        elif x0 >= right - col_w - 2:
            left = right - col_w
    return dict(
        inset_left=round(max(0, x0 - left), 1),
        inset_right=round(max(0, right - x1), 1),
        first_indent=round(line["x0"] - x0, 1),
        leading=round(rest[0]["y"] - line["y"], 1),
    )


def label_above(lines, mark, word) -> dict | None:
    """A line of its own above a block ("Abstract")."""
    line = find(lines, mark)
    if line is None:
        return None
    i = lines.index(line)
    for l in reversed(lines[max(0, i - 3):i]):
        if l["text"].strip().rstrip(".:").lower() == word.lower():
            s = l["spans"][0]
            k = lines.index(l)
            prev = lines[k - 1] if k and lines[k - 1]["page"] == l["page"] \
                else None
            return dict(text=l["text"].strip(), font=s["font"], size=s["size"],
                        color=_hex(s["color"]),
                        gap=round(line["y"] - l["y"], 1),
                        gap_prev=round(l["y"] - prev["y"], 1) if prev else 0.0,
                        centred=abs((l["x0"] + l["x1"]) / 2 -
                                    (line["x0"] + line["x1"]) / 2) < 30)
    return None


def run_in_label(lines, mark) -> dict | None:
    """The word set in front of a block's text ("Abstract.", "Keywords:")."""
    line = find(lines, mark)
    if line is None:
        return None
    low = mark.lower()
    at = line["text"].lower().index(low)
    prefix = line["text"][:at]
    if not prefix.strip():
        return None
    s = line["spans"][0]
    return dict(text=prefix.rstrip(), font=s["font"], size=s["size"],
                color=_hex(s["color"]))


def date_line(lines, area_mid) -> dict | None:
    for l in lines[:12]:
        if re.fullmatch(rf"({MONTHS}) \d+, \d{{4}}|\d+ ({MONTHS}) \d{{4}}|"
                        rf"({MONTHS}) \d{{4}}", l["text"].strip()):
            s = l["spans"][0]
            i = lines.index(l)
            prev = lines[i - 1] if i else None
            return dict(font=s["font"], size=s["size"], color=_hex(s["color"]),
                        gap=round(l["y"] - prev["y"], 1) if prev else 0.0,
                        page=l["page"],
                        day_first=l["text"].strip()[0].isdigit(),
                        centred=abs((l["x0"] + l["x1"]) / 2 - area_mid) < 6)
    return None


def chapter_label(lines, mark, area) -> dict | None:
    """report's "Chapter 1" on a line of its own above the title."""
    line = find(lines, mark)
    if line is None:
        return None
    i = lines.index(line)
    for l in reversed(lines[max(0, i - 2):i]):
        if l["page"] != line["page"] or abs(l["y"] - line["y"]) < 1:
            continue
        t = l["text"].strip()
        if re.fullmatch(r"(Chapter|CHAPTER)\s*\S+|\d+", t):
            s = l["spans"][0]
            return dict(text=re.sub(r"\S+$", "", t).strip(), font=s["font"],
                        size=s["size"], color=_hex(s["color"]),
                        gap=round(line["y"] - l["y"], 1),
                        centred=(l["x0"] > area["left"] + 3))
    return None


_BODY_WORDS = re.compile(
    r"Bodyfill|wrap across|paragraph is|baseline|justification|column width")


def _anchor(x0, x1, area) -> dict:
    """Where a header item sits: against the text block's edges or centre
    (which follow the margins), else at its measured distance."""
    if abs((x0 + x1) / 2 - (area["left"] + area["right"]) / 2) < 6:
        return dict(anchor="center", x=0.0)
    if abs(x1 - area["right"]) < 6:
        return dict(anchor="right", x=0.0)
    if abs(x0 - area["left"]) < 6:
        return dict(anchor="left", x=0.0)
    return dict(anchor="at", x=round(x0, 1))


_NAMES = (("Titlemark Words", "{title}"), ("Authormark Person", "{author}"),
          ("Affilmark University", "{affil}"),
          ("Haonemark Heading", "{h1}"), ("Hoenmark Heading", "{h1}"),
          ("Hatwomark Heading", "{h2}"), ("Htwomark Heading", "{h2}"),
          ("Hathreemark Heading", "{h3}"), ("Hthreemark Heading", "{h3}"),
          ("Hafourmark Heading", "{h3}"), ("Hfourmark Heading", "{h3}"),
          ("Hafivemark Heading", "{h3}"), ("Hfivemark Heading", "{h3}"))


def _template(text: str, page_no: int, pages: int) -> tuple[str, bool]:
    """A header line with the document's own words swapped for fields, and
    whether the class set them in capitals."""
    letters = re.sub(r"[^A-Za-z]", "", text)
    upper = bool(letters) and letters == letters.upper()
    out = text.strip()
    has_name = False
    for phrase, field in _NAMES:
        new = re.sub(re.escape(phrase), field, out, flags=re.I)
        has_name = has_name or new != out
        out = new
    out = re.sub(rf"({MONTHS}) \d+, \d{{4}}", "{date}", out)
    out = re.sub(rf"\d+ ({MONTHS}) \d{{4}}", "{date_uk}", out)
    # The counters around a name: "Chapter 2. {h1}", "2.1 {h2}".
    out = re.sub(r"(?<![\d.])\d+(?:\.\d+)*\.?(?=\s*\{h2\})", "{num2}", out)
    out = re.sub(r"(?<![\d.])\d+(?:\.\d+)*\.?(?=\s*\{h1\})", "{num1}", out)
    out = re.sub(r"(?i)((?:chapter|capitolo)\s+)\d+", r"\g<1>{num1}", out)
    out = re.sub(r"(?<=/)\s*\d+\b", "{pages}", out)
    # A lone number or letter is the page, whatever the front matter did to
    # the count; elsewhere only the page's own number qualifies.
    if re.fullmatch(r"\d+|[A-Z]", out):
        return "{page}", False
    out = re.sub(rf"(?<![\d.{{]){page_no}(?![\d.}}])", "{page}", out)
    return out, upper


def _is_fill(text: str) -> bool:
    """A line of the probe's own body text, however short."""
    words = re.findall(r"[a-z]+", text.lower())
    # "Page 3" uses a word from the fill, but no fill line has a digit.
    return bool(words) and not re.search(r"\d", text) and all(
        w in _FILL_WORDS or w.startswith(("para", "tail", "bodyfill"))
        for w in words)


def furniture(lines, rules, W, H, area, pages, top, bottom, chapter_page):
    """Every header and footer the class prints: what, where, in what font,
    on the first page, on even and odd pages, and on a chapter's first page."""
    def items(n, kind):
        on = [l for l in lines if l["page"] == n]
        text = [l for l in on if _BODY_WORDS.search(l["text"])]
        first_y = min((l["y"] for l in text), default=None)
        last_y = max((l["y"] for l in text), default=None)
        hi = top if top is not None else first_y
        lo = bottom if bottom is not None else last_y
        if kind == "first":
            # The title may stand above where body text starts on later pages.
            marks = [l["y"] for l in on if re.search(
                r"Titlemark|Authormark|Affilmark|Abstractmark", l["text"], re.I)]
            if marks:
                hi = min([hi] + marks) if hi is not None else min(marks)
        if hi is None and lo is None:
            return []
        out = []
        for l in on:
            if not ((hi is not None and l["y"] < hi - 2)
                    or (lo is not None and l["y"] > lo + 2)):
                continue
            if re.search(r"Corrmark|Keywordmark", l["text"]) \
                    or _is_fill(l["text"]) or l["text"].startswith("/"):
                continue
            t, upper = _template(l["text"], n + 1, pages)
            s = l["spans"][0]
            out.append(dict(text=t, upper=upper, font=s["font"], size=s["size"],
                            color=_hex(s["color"]), y=round(l["y"], 1),
                            **_anchor(l["x0"], l["x1"], area)))
        # A class's page furniture is a few items; dozens are slide
        # navigation dots or a poster's drawing, not a header.
        if len(out) > 8:
            return []
        for r in rules:
            # On a first page a low rule belongs to the footnotes.
            if r["page"] == n and kind != "first" and hi is not None \
                    and (r["y"] < hi - 2 or (lo is not None and r["y"] > lo + 2))\
                    and r["x1"] - r["x0"] > (area["right"] - area["left"]) * 0.9:
                out.append(dict(rule=True, y=round(r["y"], 1),
                                width=round(r["width"], 2)))
        return out

    # Pages after the last heading hold only text, so anything above that
    # text is a real header, not a heading that landed at the top of a page.
    last = find(lines, AGAIN[-1]) or find(lines, "Hthreemark")
    after = last["page"] if last else 0
    plain = [n for n in range(after + 1, pages)
             if sum(1 for l in lines if l["page"] == n
                    and _BODY_WORDS.search(l["text"])) > 3]
    if not plain:
        plain = [n for n in range(1, pages) if n != chapter_page]
    # Not the last page: a short one could look like a different page style.
    pick = lambda odd_index: next(
        (n for n in reversed(plain) if n % 2 == odd_index and n != pages - 1),
        next((n for n in reversed(plain) if n % 2 == odd_index), None))
    even, odd = pick(1), pick(0)   # PDF index 1 is page 2
    out = {"first": items(0, "first")}
    if even is not None:
        out["even"] = items(even, "plain")
    if odd is not None:
        out["odd"] = items(odd, "plain")
    if even is None and odd is not None:
        out["even"] = out["odd"]
    if odd is None and even is not None:
        out["odd"] = out["even"]
    if chapter_page:
        out["chapter"] = items(chapter_page, "chapter")
    return out


def page_geometry(lines, W, H, area, pages) -> dict:
    # A page wholly of body text gives the top and bottom of the text block.
    tops, bottoms = [], []
    for n in range(1, pages - 1):
        on = [l for l in lines if l["page"] == n and _BODY_WORDS.search(l["text"])]
        if on:
            tops.append(min(l["y"] for l in on))
            bottoms.append(max(l["y"] for l in on))
    top = statistics.median(tops) if tops else None
    bottom = statistics.median(bottoms) if bottoms else None
    return dict(
        text_top=top, text_bottom=bottom,
        page_w=round(W, 1), page_h=round(H, 1),
        left=round(area["left"], 1), right=round(W - area["right"], 1),
        top=round(top - area["size"] * 0.75, 1) if top else None,
        bottom=round(H - bottom, 1) if bottom else None,
        cols=area["cols"], colsep=area["colsep"],
    )


def measure(cls: str, pt: int, work: Path) -> dict:
    wd = work / f"{cls}_{pt}"
    wd.mkdir(parents=True, exist_ok=True)
    r = compile_tex(serialize_document(probe(cls, pt)), wd)
    if not r.ok:
        # A class can choke on the footnote that carries the address alone.
        r = compile_tex(serialize_document(
            probe(cls, pt, correspondence=False)), wd)
    if not r.ok:
        # Or on the deepest headings, which not every class defines.
        r = compile_tex(serialize_document(
            probe(cls, pt, correspondence=False, levels=3)), wd)
    pdf = wd / "document.pdf"
    if not r.ok or not pdf.exists():
        print((r.log or "")[-400:], flush=True)
        return {"broken": "does not compile"}
    lines, W, H, pages = read_lines(pdf)
    area = body_area(lines)
    if not area:
        return {"broken": "no body text found"}
    look: dict = dict(body=dict(font=area["font"], size=area["size"],
                                leading=area["leading"]))
    look["geometry"] = page_geometry(lines, W, H, area, pages)
    words = read_words(pdf)
    for key, mark in MARKS.items():
        s = style_of(lines, mark, area, W, words)
        if s:
            look[key] = s
    if area["cols"] == 2:
        # Whatever stands above where the second column starts spans both,
        # however short the line (mnras sets its title flush left).
        right_col = area["right"] - (area["right"] - area["left"]
                                     - area["colsep"]) / 2 - 2
        tops = [l["y"] for l in lines if l["page"] == 0 and l["x0"] >= right_col
                and l["y"] > H * 0.06 and _BODY_WORDS.search(l["text"])
                or l["page"] == 0 and l["x0"] >= right_col
                and re.search(r"(?i)h[a-z]*mark", l["text"])]
        if tops:
            for key in ("title", "author", "affiliation", "abstract", "keywords"):
                if key in look and look[key]["page"] == 0:
                    look[key]["wide"] = look[key]["top"] < min(tops) - 1
    for n, mark in enumerate(AGAIN, 1):
        again = style_of(lines, mark, area, W)
        key = f"h{n}"
        if again and key in look and again["above"] is not None:
            look[key]["above"] = again["above"]
    p1, p2 = find(lines, "Paraonemark"), find(lines, "Paratwomark")
    if p1 and p2:
        look["body"]["parindent"] = round(max(0, p2["x0"] - area["left"]), 1)
        look["body"]["indent_first"] = p1["x0"] > area["left"] + 2
        i = lines.index(p2)
        look["body"]["parskip"] = round(
            max(0, p2["y"] - lines[i - 1]["y"] - area["leading"]), 1) \
            if lines[i - 1]["page"] == p2["page"] else 0.0
    for key in ("abstract", "keywords"):
        extra = measure_block(lines, MARKS[key], area, W)
        if key in look:
            look[key].update(extra)
    if "abstract" in look:
        look["abstract"]["label_above"] = label_above(
            lines, "Abstractmark", "Abstract")
        look["abstract"]["label"] = run_in_label(lines, "Abstractmark")
    if "keywords" in look:
        look["keywords"]["label"] = run_in_label(lines, "Keywordmark")
    look["date"] = date_line(lines, (area["left"] + area["right"]) / 2)
    look["chapter_label"] = chapter_label(lines, "Hoenmark", area)
    g = look["geometry"]
    h1_page = look.get("h1", {}).get("page", 0)
    look["furniture"] = furniture(
        lines, read_rules(pdf), W, H, area, pages, g.pop("text_top"),
        g.pop("text_bottom"),
        h1_page if class_supports_chapter(cls) else 0)
    return look


def follows_settings(cls: str, work: Path) -> tuple[bool, bool]:
    """Does this class obey the document's margins and paper size?"""
    if cls not in _STANDARD_SERIALIZER_CLASSES:
        return False, False
    wd = work / f"{cls}_geom"
    wd.mkdir(parents=True, exist_ok=True)
    base = compile_tex(serialize_document(probe(cls, 12)), wd)
    a = read_lines(wd / "document.pdf") if base.ok else None
    r = compile_tex(serialize_document(probe(
        cls, 12, margin_left_cm=5.0, page_size="Letter")), wd)
    b = read_lines(wd / "document.pdf") if r.ok else None
    if not a or not b:
        return False, False
    # The first body line of a recto: twoside classes swap margins on verso.
    pa, pb = find(a[0], "Paraonemark"), find(b[0], "Paraonemark")
    return abs(pa["x0"] - pb["x0"]) > 5, abs(a[1] - b[1]) > 1


def main() -> None:
    classes = sys.argv[1:] or TEMPLATE_CHOICES
    work = Path(tempfile.mkdtemp(prefix="khervetex-looks-"))
    table: dict = {}
    if OUT.exists() and sys.argv[1:]:
        ns: dict = {}
        exec(OUT.read_text(encoding="utf-8"), ns)
        table = {c: v for c, v in ns["LOOKS"].items() if c in TEMPLATE_CHOICES}
    for cls in classes:
        sizes = (10, 11, 12) if cls in _STANDARD_SERIALIZER_CLASSES else (12,)
        margins, page = follows_settings(cls, work)
        entry = {}
        for pt in sizes:
            look = measure(cls, pt, work)
            look.setdefault("geometry", {}).update(
                follows_margins=margins, follows_page=page)
            entry[pt] = look
            print(cls, pt, look.get("broken", "ok"), flush=True)
        table[cls] = entry
    # Another run may have refreshed other classes meanwhile: keep those.
    if OUT.exists() and sys.argv[1:]:
        ns = {}
        exec(OUT.read_text(encoding="utf-8"), ns)
        table = {**ns["LOOKS"], **{c: table[c] for c in classes}}
    body = pprint.pformat(table, width=78, sort_dicts=False)
    OUT.write_text(
        '"""How each document class really typesets its styles, in points.\n\n'
        "Generated by packaging/measure_class_looks.py from compiled PDFs: do "
        'not edit by hand.\n"""\n'
        f"LOOKS = {body}\n", encoding="utf-8")
    json.dumps(table)  # the table must stay plain data
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
