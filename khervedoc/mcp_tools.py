"""The tools KherveTeX exposes to Claude over MCP, and their implementation.

`TOOLS` is the schema table the stdio server advertises; `ToolExecutor`
runs one tool against a live `MainWindow` on the GUI thread (the bridge
calls it from Qt's event loop). Every tool returns a plain dict; a dict
with an "error" key is reported to the client as a failed call.

The document is addressed as a flat list of top-level *blocks*
(headings, paragraphs, equations, figures, tables, raw LaTeX...), the
same units the model and the visual editor use, so "replace blocks 4-6"
means the same thing to Claude as to the user looking at the page.
Content goes in as LaTeX body source and is parsed into real, editable
blocks — never pasted in as a raw string.
"""
from __future__ import annotations

import base64
import time
from dataclasses import asdict
from pathlib import Path

_INT = {"type": "integer"}
_STR = {"type": "string"}
_BOOL = {"type": "boolean"}


def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props,
            "required": required or [], "additionalProperties": False}


_SHAPES_DOC = (
    "Array of shape objects, all lengths in mm. Common optional keys: "
    "stroke (#rrggbb or null for none, default #1a1a1a), width (stroke "
    "mm, default 0.5), dash (solid|dash|dot|dashdot), fill (#rrggbb or "
    "null, default null), rotation (deg), opacity (0-1). "
    "rect / rounded_rect / ellipse: x, y (top-left), w, h, radius "
    "(rounded_rect, default 2.5), label (text centred inside), "
    "font_size (pt, default 11), text_color. circle: x, y (centre), r. "
    "line / arrow / double_arrow: points [[x1,y1],[x2,y2]]; arrow head "
    "filled|open|stealth. polygon (closed, fillable) / polyline (open "
    "path): points [[x,y],...]. text: text, x, y, anchor "
    "(center default | left | topleft), font_size, color, bold, italic. "
    "symbol: symbol \"library/name\" from list_drawing_symbols, x, y "
    "(centre), optional w / h (keeps aspect if only one), label "
    "(replaces a flowchart node's caption, else placed below). Later "
    "shapes draw on top. A readable figure is ~60-160 mm wide; text of "
    "9-12 pt; leave ~10 mm between boxes for arrows.")

TOOLS: list[dict] = [
    # ── reading ──────────────────────────────────────────────────
    {"name": "get_document_info",
     "description": "Title, author, file path, document class, page and "
                    "font settings, packages, block count, word count, "
                    "whether there are unsaved changes, and the last "
                    "compile status. Call this first.",
     "input_schema": _obj({})},
    {"name": "get_outline",
     "description": "Every top-level block with its index, type and a "
                    "short text preview; headings show their level and "
                    "number. Use the indices with read_blocks, "
                    "replace_blocks, delete_blocks and insert_latex.",
     "input_schema": _obj({})},
    {"name": "read_blocks",
     "description": "Full LaTeX (and the structured model) of blocks "
                    "start..end inclusive. Read before you rewrite.",
     "input_schema": _obj({"start": _INT, "end": _INT}, ["start"])},
    {"name": "get_latex",
     "description": "The complete .tex source the document compiles "
                    "from (preamble + body), as the Code tab shows it.",
     "input_schema": _obj({"max_chars": _INT})},
    {"name": "search_text",
     "description": "Find text in the document (case-insensitive). "
                    "Returns the block index and context of each match.",
     "input_schema": _obj({"query": _STR, "max_results": _INT},
                          ["query"])},
    {"name": "list_references",
     "description": "Citation keys (from the .bib / thebibliography) "
                    "and \\label names with the number each resolves to "
                    "— use these rather than inventing keys.",
     "input_schema": _obj({})},
    {"name": "get_compile_log",
     "description": "Result of the last compile: ok flag, error summary "
                    "and the tail of the LaTeX log.",
     "input_schema": _obj({"lines": _INT})},
    {"name": "render_page",
     "description": "An image of one page of the last compiled PDF "
                    "(1-based). Use it to check layout, equations, "
                    "tables and figures the way the reader will see "
                    "them.",
     "input_schema": _obj({"page": _INT, "dpi": _INT}, ["page"])},
    # ── editing ──────────────────────────────────────────────────
    {"name": "insert_latex",
     "description": "Insert LaTeX BODY source (no preamble) as new "
                    "blocks: after block index `after` (-1 = at the "
                    "very start), or at the end when `after` is omitted. "
                    "Sections, equations, lists, tables, figures, "
                    "\\cite and \\ref all become real editable content. "
                    "One Ctrl+Z undoes it.",
     "input_schema": _obj({"latex": _STR, "after": _INT}, ["latex"])},
    {"name": "replace_blocks",
     "description": "Replace blocks start..end inclusive with new LaTeX "
                    "body source. Read them first with read_blocks and "
                    "keep what you were not asked to change.",
     "input_schema": _obj({"start": _INT, "end": _INT, "latex": _STR},
                          ["start", "end", "latex"])},
    {"name": "delete_blocks",
     "description": "Delete blocks start..end inclusive.",
     "input_schema": _obj({"start": _INT, "end": _INT},
                          ["start", "end"])},
    {"name": "replace_text",
     "description": "Find and replace plain text in the visual document, "
                    "keeping the surrounding formatting. Replaces every "
                    "occurrence unless all=false.",
     "input_schema": _obj({"find": _STR, "replace": _STR,
                           "all": _BOOL, "case_sensitive": _BOOL},
                          ["find", "replace"])},
    {"name": "set_metadata",
     "description": "Change document settings: title, author, "
                    "documentclass, body_font_pt (10/11/12), "
                    "body_font_family (default, times, palatino, "
                    "helvetica, courier, charter, libertine), "
                    "page_size (a4, letter, ...), line_spacing, "
                    "paragraph_indent, margins in cm, add_packages, "
                    "remove_packages. Only the fields you pass change.",
     "input_schema": _obj({
         "title": _STR, "author": _STR, "documentclass": _STR,
         "body_font_pt": _INT, "body_font_family": _STR,
         "page_size": _STR, "line_spacing": {"type": "number"},
         "paragraph_indent": _BOOL,
         "margin_top_cm": {"type": "number"},
         "margin_bottom_cm": {"type": "number"},
         "margin_left_cm": {"type": "number"},
         "margin_right_cm": {"type": "number"},
         "add_packages": {"type": "array", "items": _STR},
         "remove_packages": {"type": "array", "items": _STR},
     })},
    {"name": "compile_document",
     "description": "Compile now and wait for the result (ok, error, "
                    "page count, log tail). The PDF panel updates too.",
     "input_schema": _obj({})},
    # ── files ────────────────────────────────────────────────────
    {"name": "save_document",
     "description": "Save the document. Without `path` it saves in "
                    "place (the document must already have a file). A "
                    "new `path` (.ktex or .ktex.json) needs Full "
                    "access.",
     "input_schema": _obj({"path": _STR})},
    {"name": "open_document",
     "description": "Open or import a file (.ktex, .ktex.json, .tex, "
                    ".md, .docx, .pdf). Refuses to discard unsaved "
                    "changes unless discard_unsaved_changes is true — "
                    "prefer saving first. Needs Full access.",
     "input_schema": _obj({"path": _STR,
                           "discard_unsaved_changes": _BOOL}, ["path"])},
    {"name": "new_document",
     "description": "Start a blank document. Refuses to discard unsaved "
                    "changes unless discard_unsaved_changes is true.",
     "input_schema": _obj({"discard_unsaved_changes": _BOOL})},
    # ── equations, chemistry and drawings ───────────────────────
    {"name": "insert_equation",
     "description": "Insert a LaTeX math equation (the math only, no $ "
                    "or \\[ \\]). display=true (default) makes a "
                    "display equation block (numbered/label optional); "
                    "display=false puts inline math in a new paragraph. "
                    "The result says whether the editor typesets it "
                    "natively or shows unknown commands as raw source.",
     "input_schema": _obj({"latex": _STR, "display": _BOOL,
                           "numbered": _BOOL, "label": _STR,
                           "after": _INT}, ["latex"])},
    {"name": "insert_chemistry",
     "description": "Insert a chemical formula or reaction in mhchem "
                    "syntax, e.g. \"2H2 + O2 -> 2H2O\" or \"SO4^2-\" — "
                    "just the body, it is wrapped in \\ce{...} and the "
                    "mhchem package is added. display=false (default) is "
                    "inline in a new paragraph; display=true is a "
                    "numbered equation block.",
     "input_schema": _obj({"formula": _STR, "display": _BOOL,
                           "numbered": _BOOL, "after": _INT},
                          ["formula"])},
    {"name": "list_drawing_symbols",
     "description": "Symbol libraries (flowchart, electrical, optics, "
                    "maths, labware, arrows) and the symbol names usable "
                    "as {\"type\": \"symbol\", \"symbol\": "
                    "\"library/name\"} in drawings, with default sizes "
                    "in mm.",
     "input_schema": _obj({"library": _STR})},
    {"name": "insert_drawing",
     "description": "Draw a vector figure (diagram, flowchart, setup "
                    "sketch) from JSON shapes and insert it as an "
                    "editable drawing figure the user can re-open. "
                    "Units are MILLIMETRES, origin top-left, y down; the "
                    "drawing is cropped to its content. See the "
                    "`shapes` schema.",
     "input_schema": _obj({
         "shapes": {"type": "array", "items": {"type": "object"},
                    "description": _SHAPES_DOC},
         "caption": _STR, "label": _STR,
         "width": {"type": "string",
                   "description": "LaTeX width, default 0.7\\textwidth"},
         "after": _INT}, ["shapes"])},
    {"name": "get_drawing",
     "description": "The shapes of the drawing figure at block `index`, "
                    "in the insert_drawing schema (mm). Items the schema "
                    "cannot express come back as type \"other\" with "
                    "their bounding box; include_raw adds the full "
                    "canvas item dicts.",
     "input_schema": _obj({"index": _INT, "include_raw": _BOOL},
                          ["index"])},
    {"name": "update_drawing",
     "description": "Rewrite the drawing figure at block `index`: "
                    "mode \"replace\" (default) redraws it from `shapes`; "
                    "\"append\" adds `shapes` to what is there (use "
                    "get_drawing coordinates). Caption and label are "
                    "kept.",
     "input_schema": _obj({"index": _INT,
                           "shapes": {"type": "array",
                                      "items": {"type": "object"}},
                           "mode": {"type": "string",
                                    "enum": ["replace", "append"]}},
                          ["index", "shapes"])},
    {"name": "open_in_khervepaint",
     "description": "Open the drawing figure at block `index` in the "
                    "KhervePaint app for full editing. Its saves update "
                    "the figure automatically.",
     "input_schema": _obj({"index": _INT}, ["index"])},
    {"name": "export_pdf",
     "description": "Compile and write the PDF to `path`. Needs Full "
                    "access.",
     "input_schema": _obj({"path": _STR}, ["path"])},
]

READ_ONLY_TOOLS = frozenset({
    "get_document_info", "get_outline", "read_blocks", "get_latex",
    "search_text", "list_references", "get_compile_log", "render_page",
    "list_drawing_symbols", "get_drawing",
})
#: Tools that manage files, the compile or the undo stack themselves;
#: wrapping them in an edit block would record an empty undo step.
NO_UNDO_BLOCK_TOOLS = READ_ONLY_TOOLS | {
    "compile_document", "save_document", "open_document",
    "new_document", "export_pdf", "set_metadata", "open_in_khervepaint",
}
#: Tools that touch a client-chosen filesystem path.
PATH_TOOLS = frozenset({"open_document", "export_pdf"})


class ToolError(Exception):
    """A tool failed in a way worth telling the model about."""


def _preview(block, n: int = 90) -> str:
    from .serializer import serialize_block
    try:
        text = serialize_block(block)
    except Exception:
        text = type(block).__name__
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n - 1] + "…"


class ToolExecutor:
    def __init__(self, mainwindow):
        self._mw = mainwindow

    # plumbing ------------------------------------------------------

    @property
    def _editor(self):
        return self._mw._editor

    def execute(self, name: str, tool_input: dict) -> dict:
        handler = getattr(self, f"_t_{name}", None)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            return handler(tool_input or {})
        except ToolError as exc:
            return {"error": str(exc)}

    def _doc(self):
        return self._editor.get_document()

    def _blocks(self) -> list:
        return list(self._doc().children)

    def _range(self, args: dict, n: int) -> tuple[int, int]:
        start = int(args.get("start", 0))
        end = int(args.get("end", start))
        if n == 0:
            raise ToolError("The document is empty.")
        if not (0 <= start < n) or not (start <= end < n):
            raise ToolError(f"Block range {start}..{end} is outside "
                            f"0..{n - 1}. Call get_outline again.")
        return start, end

    @staticmethod
    def _parse(latex: str) -> list:
        from .importers import import_body_fragment
        blocks = import_body_fragment(latex or "")
        if not blocks:
            raise ToolError("That LaTeX produced no content.")
        return blocks

    def _set_body(self, blocks: list) -> None:
        """Replace the body in one undo step, keeping Title / Author."""
        from .model import Author, Figure, Paragraph, Table, Title
        body = [b for b in blocks if not isinstance(b, (Title, Author))]

        def empty(b):
            return isinstance(b, Paragraph) and not any(
                getattr(c, "text", "x").strip() for c in b.children)

        def framed(b):
            return isinstance(b, (Figure, Table))
        # A figure/table is a frame in the editor, and Qt always puts a
        # block on each side of a frame; those read back as empty
        # paragraphs, so without this every call would add two more.
        body = [b for i, b in enumerate(body)
                if not (empty(b) and (
                    (i > 0 and framed(body[i - 1]))
                    or (i + 1 < len(body) and framed(body[i + 1]))))]
        self._editor.replace_body(body)

    def _unsaved(self) -> bool:
        return self._editor.text_edit.document().isModified()

    # reading -------------------------------------------------------

    def _t_get_document_info(self, args: dict) -> dict:
        doc = self._doc()
        m = doc.meta
        from .serializer import serialize_document
        words = len(" ".join(_preview(b, 10 ** 9)
                             for b in doc.children).split())
        last = getattr(self._mw, "_last_compile_result", None)
        path = self._mw._current_path
        return {
            "path": str(path) if path else None,
            "title": m.title, "author": m.author,
            "documentclass": m.documentclass,
            "page_size": m.page_size, "body_font_pt": m.body_font_pt,
            "body_font_family": m.body_font_family,
            "line_spacing": m.line_spacing,
            "margins_cm": [m.margin_top_cm, m.margin_right_cm,
                           m.margin_bottom_cm, m.margin_left_cm],
            "packages": list(m.packages),
            "blocks": len(doc.children), "approx_words": words,
            "unsaved_changes": self._unsaved(),
            "project_open": self._mw._project is not None,
            "last_compile": None if last is None else
                {"ok": last.ok, "error": last.error},
            "latex_chars": len(serialize_document(doc)),
        }

    def _t_get_outline(self, args: dict) -> dict:
        from .model import Section
        from .references import ReferenceResolver
        doc = self._doc()
        resolver = ReferenceResolver(doc)
        out = []
        counters = [0] * 6
        has_ch = any(isinstance(b, Section) and b.level == 0
                     for b in doc.children)
        for i, b in enumerate(doc.children):
            item = {"index": i, "type": type(b).__name__,
                    "preview": _preview(b)}
            if isinstance(b, Section):
                item["level"] = b.level
                if b.numbered:
                    counters[b.level] += 1
                    for k in range(b.level + 1, 6):
                        counters[k] = 0
                    item["number"] = ".".join(
                        str(c) for c in counters[0 if has_ch else 1:
                                                 b.level + 1])
            label = getattr(b, "label", None)
            if label:
                item["label"] = label
                item["ref"] = resolver.ref_text(label)
            out.append(item)
        return {"blocks": out}

    def _t_read_blocks(self, args: dict) -> dict:
        from .serializer import serialize_block
        blocks = self._blocks()
        start, end = self._range(args, len(blocks))
        return {"blocks": [
            {"index": i, "type": type(b).__name__,
             "latex": serialize_block(b), "model": asdict(b)}
            for i, b in enumerate(blocks[start:end + 1], start)]}

    def _t_get_latex(self, args: dict) -> dict:
        from .serializer import serialize_document
        src = serialize_document(self._doc())
        limit = int(args.get("max_chars") or 200_000)
        return {"latex": src[:limit], "truncated": len(src) > limit,
                "total_chars": len(src)}

    def _t_search_text(self, args: dict) -> dict:
        from .serializer import serialize_block
        q = (args.get("query") or "").lower()
        if not q:
            raise ToolError("query is empty.")
        cap = int(args.get("max_results") or 50)
        hits = []
        for i, b in enumerate(self._blocks()):
            text = serialize_block(b)
            low = text.lower()
            pos = low.find(q)
            while pos != -1 and len(hits) < cap:
                a, z = max(0, pos - 40), pos + len(q) + 40
                hits.append({"block": i, "context":
                             " ".join(text[a:z].split())})
                pos = low.find(q, pos + 1)
        return {"matches": hits, "count": len(hits)}

    def _t_list_references(self, args: dict) -> dict:
        from .references import ReferenceResolver
        r = ReferenceResolver(self._doc(), self._editor._doc_dir)
        cites = [{"key": k, "author": e.get("author", ""),
                  "year": e.get("year", ""), "title": e.get("title", "")}
                 for k, e in r.entries.items()]
        return {"citations": cites, "labels": r.labels}

    def _t_get_compile_log(self, args: dict) -> dict:
        last = getattr(self._mw, "_last_compile_result", None)
        if last is None:
            return {"compiled": False,
                    "note": "Nothing compiled yet — call compile_document."}
        n = int(args.get("lines") or 40)
        return {"ok": last.ok, "error": last.error,
                "pdf": str(last.pdf_path) if last.pdf_path else None,
                "log_tail": "\n".join((last.log or "").splitlines()[-n:])}

    def _t_render_page(self, args: dict) -> dict:
        last = getattr(self._mw, "_last_compile_result", None)
        if last is None or last.pdf_path is None or not last.pdf_path.exists():
            raise ToolError("No compiled PDF yet — call compile_document.")
        import pymupdf
        page_no = int(args.get("page", 1))
        dpi = max(36, min(200, int(args.get("dpi") or 110)))
        with pymupdf.open(last.pdf_path) as pdf:
            if not (1 <= page_no <= pdf.page_count):
                raise ToolError(f"Page {page_no} is outside 1..{pdf.page_count}.")
            pix = pdf[page_no - 1].get_pixmap(dpi=dpi, alpha=False)
            png = pix.tobytes("png")
            count = pdf.page_count
        return {"page": page_no, "page_count": count,
                "image_png_base64": base64.b64encode(png).decode("ascii")}

    # editing -------------------------------------------------------

    def _t_insert_latex(self, args: dict) -> dict:
        new = self._parse(args.get("latex", ""))
        blocks = self._blocks()
        after = args.get("after")
        at = len(blocks) if after is None else int(after) + 1
        if not (0 <= at <= len(blocks)):
            raise ToolError(f"`after` must be -1..{len(blocks) - 1}.")
        self._set_body(blocks[:at] + new + blocks[at:])
        return {"inserted_blocks": len(new), "at_index": at,
                "total_blocks": len(self._blocks())}

    def _t_replace_blocks(self, args: dict) -> dict:
        blocks = self._blocks()
        start, end = self._range(args, len(blocks))
        new = self._parse(args.get("latex", ""))
        self._set_body(blocks[:start] + new + blocks[end + 1:])
        return {"replaced": end - start + 1, "with_blocks": len(new),
                "total_blocks": len(self._blocks())}

    def _t_delete_blocks(self, args: dict) -> dict:
        blocks = self._blocks()
        start, end = self._range(args, len(blocks))
        self._set_body(blocks[:start] + blocks[end + 1:])
        return {"deleted": end - start + 1,
                "total_blocks": len(self._blocks())}

    def _t_replace_text(self, args: dict) -> dict:
        from PySide6.QtGui import QTextDocument
        find = args.get("find") or ""
        if not find:
            raise ToolError("`find` is empty.")
        repl = args.get("replace", "")
        replace_all = args.get("all", True)
        flags = QTextDocument.FindFlag(0)
        if args.get("case_sensitive"):
            flags |= QTextDocument.FindCaseSensitively
        qdoc = self._editor.text_edit.document()
        count = 0
        cursor = qdoc.find(find, 0, flags)
        while not cursor.isNull():
            cursor.insertText(repl)
            count += 1
            if not replace_all:
                break
            cursor = qdoc.find(find, cursor.position(), flags)
        return {"replacements": count}

    def _t_set_metadata(self, args: dict) -> dict:
        import copy
        meta = copy.deepcopy(self._editor.meta())
        changed = []
        for key in ("title", "author", "documentclass", "body_font_pt",
                    "body_font_family", "page_size", "line_spacing",
                    "paragraph_indent", "margin_top_cm", "margin_bottom_cm",
                    "margin_left_cm", "margin_right_cm"):
            if key in args:
                setattr(meta, key, args[key])
                changed.append(key)
        for pkg in args.get("add_packages") or []:
            if pkg not in meta.packages:
                meta.packages.append(pkg)
                changed.append(f"+{pkg}")
        for pkg in args.get("remove_packages") or []:
            if pkg in meta.packages:
                meta.packages.remove(pkg)
                changed.append(f"-{pkg}")
        if not changed:
            raise ToolError("No recognised fields to change.")
        self._editor.set_meta(meta)
        if hasattr(self._mw, "_sync_toolbar_state"):
            self._mw._sync_toolbar_state()
        return {"changed": changed}

    def _t_compile_document(self, args: dict) -> dict:
        from PySide6.QtCore import QEventLoop
        from PySide6.QtWidgets import QApplication
        mw = self._mw
        before = getattr(mw, "_last_compile_result", None)
        mw._last_failed_hash = None          # force a real compile
        mw._kick_compile()
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            QApplication.processEvents(QEventLoop.AllEvents, 50)
            worker = mw._compile_worker
            done = getattr(mw, "_last_compile_result", None)
            if (worker is None or not worker.isRunning()) \
                    and done is not before \
                    and not getattr(mw, "_pending_recompile", False):
                break
            time.sleep(0.02)
        result = getattr(mw, "_last_compile_result", None)
        if result is None or result is before:
            raise ToolError("The compile did not finish (is tectonic "
                            "installed?). Check get_compile_log.")
        pages = None
        if result.pdf_path is not None and result.pdf_path.exists():
            try:
                import pymupdf
                with pymupdf.open(result.pdf_path) as pdf:
                    pages = pdf.page_count
            except Exception:
                pass
        return {"ok": result.ok, "error": result.error, "pages": pages,
                "log_tail": "\n".join(
                    (result.log or "").splitlines()[-15:])}

    # files ---------------------------------------------------------

    def _t_save_document(self, args: dict) -> dict:
        mw = self._mw
        path = args.get("path")
        if path:
            p = Path(path).expanduser()
            if not mw._has_native_suffix(p):
                raise ToolError("Save as .ktex or .ktex.json; use "
                                "export_pdf for PDF output.")
            mw._current_path = p
            mw._editor.set_document_dir(p.parent)
            mw._update_title()
            mw._write_to(p)
        elif mw._project is not None:
            mw._save_project()
        elif mw._current_path is None:
            raise ToolError("This document has never been saved; pass a "
                            "`path` (needs Full access) or ask the user "
                            "to save it once.")
        else:
            mw._write_to(mw._current_path)
        return {"saved": str(mw._current_path or mw._project_path)}

    def _refuse_discard(self, args: dict) -> None:
        if self._unsaved() and not args.get("discard_unsaved_changes"):
            raise ToolError("The document has unsaved changes. Save it "
                            "first (save_document), or pass "
                            "discard_unsaved_changes=true only if the "
                            "user agreed to lose them.")

    def _t_open_document(self, args: dict) -> dict:
        p = Path(args.get("path", "")).expanduser()
        if not p.is_file():
            raise ToolError(f"No such file: {p}")
        self._refuse_discard(args)
        self._mw._open_path(p)
        return {"opened": str(p), "blocks": len(self._blocks())}

    def _t_new_document(self, args: dict) -> dict:
        self._refuse_discard(args)
        self._mw._new()
        return {"ok": True}

    # equations, chemistry, drawings -------------------------------

    def _insert_at(self, new: list, after) -> int:
        blocks = self._blocks()
        at = len(blocks) if after is None else int(after) + 1
        if not (0 <= at <= len(blocks)):
            raise ToolError(f"`after` must be -1..{len(blocks) - 1}.")
        self._set_body(blocks[:at] + new + blocks[at:])
        # The editor may pad figures with empty paragraphs, so the new
        # block's index is found rather than assumed.
        now = self._blocks()
        for i in range(at, len(now)):
            if type(now[i]) is type(new[0]) and now[i] == new[0]:
                return i
        for i in range(at, len(now)):
            if type(now[i]) is type(new[0]):
                return i
        return at

    @staticmethod
    def _math_node(latex: str, display: bool, numbered: bool,
                   label):
        from .model import MathBlock, MathInline, Paragraph
        if display:
            return MathBlock(latex=latex, numbered=numbered,
                             label=label or None)
        return Paragraph(children=[MathInline(latex=latex)])

    @staticmethod
    def _raw_math(latex: str) -> list[str]:
        from .mathbox import Raw, parse_latex
        found = []

        def walk(node):
            if isinstance(node, Raw):
                found.append(node.latex)
            for child in getattr(node, "children", None) or []:
                walk(child)
            for slot in node.slots() if hasattr(node, "slots") else []:
                walk(slot)
        walk(parse_latex(latex))
        return found

    def _t_insert_equation(self, args: dict) -> dict:
        latex = (args.get("latex") or "").strip()
        for a, b in (("$$", "$$"), ("\\[", "\\]"), ("$", "$")):
            if len(latex) > len(a) + len(b) and latex.startswith(a) \
                    and latex.endswith(b):
                latex = latex[len(a):-len(b)].strip()
                break
        if not latex:
            raise ToolError("`latex` is empty.")
        display = args.get("display", True) is not False
        if args.get("label") and not display:
            raise ToolError("Only a display equation can carry a label.")
        numbered = bool(args.get("numbered")) or bool(args.get("label"))
        at = self._insert_at([self._math_node(
            latex, display, numbered, args.get("label"))], args.get("after"))
        raw = self._raw_math(latex)
        res = {"at_index": at, "display": display, "numbered": numbered,
               "latex": latex, "typesets_natively": not raw,
               "total_blocks": len(self._blocks())}
        if raw:
            res["not_typeset_in_editor"] = raw[:10]
            res["note"] = ("The editor shows these parts as source; the "
                           "compiled PDF is unaffected if the LaTeX is "
                           "valid — compile_document to check.")
        return res

    def _t_insert_chemistry(self, args: dict) -> dict:
        from .chemistry import wrap_ce
        latex = wrap_ce(args.get("formula") or "")
        if not latex:
            raise ToolError("`formula` is empty.")
        meta = self._editor.meta()
        added = "mhchem" not in meta.packages
        if added:
            meta.packages.append("mhchem")
            self._editor.set_meta(meta)
        display = bool(args.get("display", False))
        numbered = display and args.get("numbered", True) is not False
        at = self._insert_at([self._math_node(latex, display, numbered,
                                              None)], args.get("after"))
        return {"at_index": at, "latex": latex, "display": display,
                "mhchem_package_added": added,
                "total_blocks": len(self._blocks())}

    def _t_list_drawing_symbols(self, args: dict) -> dict:
        from .paint.authoring import LIBRARIES, list_symbols
        libs = list_symbols()
        want = args.get("library")
        if want:
            if want not in libs:
                raise ToolError(f"Unknown library; use one of "
                                f"{', '.join(LIBRARIES)}.")
            libs = {want: libs[want]}
        return {"libraries": libs,
                "usage": "{\"type\": \"symbol\", \"symbol\": "
                         "\"optics/laser\", \"x\": 30, \"y\": 20}"}

    def _drawing_at(self, index) -> tuple[int, object, Path]:
        from .model import Figure
        blocks = self._blocks()
        if index is None:
            raise ToolError("`index` is required.")
        i = int(index)
        if not (0 <= i < len(blocks)):
            raise ToolError(f"Block {i} is outside 0..{len(blocks) - 1}.")
        fig = blocks[i]
        if not isinstance(fig, Figure):
            raise ToolError(f"Block {i} is a {type(fig).__name__}, not a "
                            f"figure. Call get_outline.")
        png = self._editor._resolve_image_path(fig.path)
        if png is None or not png.with_suffix(".svg").exists():
            raise ToolError(f"Figure {i} is not an editable drawing (no "
                            f".svg beside its image).")
        return i, fig, png

    @staticmethod
    def _shapes_into(scene, shapes) -> int:
        from .paint.authoring import ShapeError, add_shapes
        try:
            return add_shapes(scene, shapes)
        except ShapeError as exc:
            raise ToolError(str(exc)) from None

    @staticmethod
    def _save_scene(scene, png: Path) -> dict:
        from .paint import export
        if not export.save_drawing(scene, png):
            raise ToolError("The drawing is empty.")
        return {"png": str(png), "svg": str(png.with_suffix(".svg")),
                "pdf": str(png.with_suffix(".pdf"))}

    def _t_insert_drawing(self, args: dict) -> dict:
        from .drawing_dialog import next_drawing_path
        from .model import Figure
        from .paint.authoring import new_scene
        from .serializer import escape_text
        scene = new_scene()
        n = self._shapes_into(scene, args.get("shapes"))
        images = Path(self._editor._images_dir)
        images.mkdir(parents=True, exist_ok=True)
        png = next_drawing_path(images)
        files = self._save_scene(scene, png)
        fig = Figure(path=str(png),
                     caption=escape_text(args.get("caption") or ""),
                     label=args.get("label") or None,
                     width=args.get("width") or "0.7\\textwidth",
                     source="drawing")
        at = self._insert_at([fig], args.get("after"))
        return {"at_index": at, "items": n, "files": files,
                "total_blocks": len(self._blocks())}

    def _t_get_drawing(self, args: dict) -> dict:
        from .paint import document, export
        from .paint.authoring import new_scene, scene_to_shapes
        i, fig, png = self._drawing_at(args.get("index"))
        scene = new_scene()
        export.load_svg(scene, png.with_suffix(".svg"))
        res = {"index": i, "caption": fig.caption, "label": fig.label,
               "width": fig.width, "files": {
                   "png": str(png), "svg": str(png.with_suffix(".svg"))},
               "shapes": scene_to_shapes(scene)}
        if args.get("include_raw"):
            raw = []
            for it in scene.vector_items():
                try:
                    raw.append(document.item_to_dict(it))
                except ValueError:
                    raw.append({"type": type(it).__name__})
            res["raw_items"] = raw
        return res

    def _t_update_drawing(self, args: dict) -> dict:
        from .paint import export
        from .paint.authoring import new_scene
        i, _fig, png = self._drawing_at(args.get("index"))
        mode = args.get("mode") or "replace"
        if mode not in ("replace", "append"):
            raise ToolError("mode must be replace or append.")
        scene = new_scene()
        if mode == "append":
            export.load_svg(scene, png.with_suffix(".svg"))
        n = self._shapes_into(scene, args.get("shapes"))
        files = self._save_scene(scene, png)
        self._editor.refresh_figure_image(png)
        return {"index": i, "mode": mode, "items_added": n,
                "items_total": len(scene.vector_items()), "files": files}

    def _t_open_in_khervepaint(self, args: dict) -> dict:
        i, _fig, png = self._drawing_at(args.get("index"))
        ok, msg = self._editor.edit_in_khervepaint(png, interactive=False)
        if not ok:
            raise ToolError(msg)
        return {"index": i, "opened": str(png.with_suffix(".svg")),
                "message": msg}

    def _t_export_pdf(self, args: dict) -> dict:
        target = Path(args.get("path", "")).expanduser()
        if target.suffix.lower() != ".pdf":
            raise ToolError("`path` must end in .pdf")
        res = self._t_compile_document({})
        last = self._mw._last_compile_result
        if not res["ok"] or last.pdf_path is None:
            raise ToolError(f"Compile failed: {res['error']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(last.pdf_path.read_bytes())
        return {"exported": str(target), "pages": res["pages"]}
