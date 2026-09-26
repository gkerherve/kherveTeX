# kherveDOC

A WYSIWYG document editor that produces beautiful PDFs via LaTeX, with Git-based version history.

The title bar shows `kherveDOC v<major>.<minor>.<commits>+<sha7>`.

## Features

**Editor**
- Word-style page card sized to real A4 / Letter / Legal paper at 96 DPI; switchable from the toolbar.
- Single editable surface with visible dashed page-break lines at every layout pagination.
- Paragraph-style picker: Body text · Title · Heading 1-5.
- Inline marks: bold, italic, underline, strikethrough, code, smallcaps, subscript, superscript.
- Inserts: inline math, math block (LaTeX-typed), bullet / numbered lists, hyperlinks, footnotes, citations (cite / citep / citet), cross-references (ref / eqref / pageref), figures (with caption + label), tables, page break, horizontal rule, raw LaTeX escape hatch.
- Three tabs: **Formatted** (WYSIWYG), **LaTeX** (live read-only syntax-highlighted source), **PDF** (live preview).

**File**
- Native format: `.ktex.json` (a JSON serialisation of the document model) plus a sibling `.tex`. Bundled format: `.ktexz` (ZIP archive with images).
- Import: `.tex` (regex-based subset parser, falls back to RawLatex), `.docx` (uses python-docx, **embedded images are extracted** into a sibling folder and inserted as Figure nodes).
- Export: `.tex`, `.pdf`.
- Document properties dialog: title, author, document class, package list.

**Git**
- Each document gets its own git repo via `pygit2`.
- Saving auto-commits and pushes to `origin` (best-effort).
- History viewer under the History menu.

## Setup

```powershell
pip install -r requirements.txt
winget install TectonicTypesetting.Tectonic  # or download from https://tectonic-typesetting.github.io/
python -m khervedoc
```

Optional for `.docx` import:
```powershell
pip install python-docx
```

Run the test suite:
```powershell
python -m pytest tests/
```

## Working with Claude (MCP)

KherveTeX can be driven by Claude Desktop or Claude Code through MCP.
Open **AI ▸ Connect to Claude…**, tick *Let assistants connect*, and
press *Connect* for your client (it writes the client's config for you),
then restart the client and mention "KherveTeX" in the chat. Claude
works on the document open in the window: it can read the outline and
LaTeX, insert or rewrite sections, fix text, change settings, compile
and look at rendered PDF pages. Each change is one Ctrl+Z step. The
access level (read / edit / full) is chosen in the same dialog; the
connection is local-only and token-protected.

## Project layout

```
khervedoc/
  model.py        # typed document tree (dataclasses)
  serializer.py   # model -> LaTeX
  importers.py    # .tex and .docx -> model
  compiler.py     # tectonic subprocess + PyMuPDF rasteriser
  git_backend.py  # pygit2 auto-commit + push
  editor.py       # WYSIWYG editor widget
  paged_edit.py   # PagedTextEdit with page-break overlay
  page_sizes.py   # A4 / Letter / Legal constants
  latex_view.py   # syntax-highlighted .tex view
  preview.py      # PDF page renderer
  mainwindow.py   # app shell, menus, toolbar
  icons.py        # toolbar icons drawn at runtime with QPainter
  __main__.py     # entry point (forces light Fusion palette)
tests/
  test_model.py
  test_serializer.py
  test_importers.py
examples/
  demo.ktex.json
```

## Architecture in one paragraph

The **document model** is the single source of truth. The **editor** (a Word-style PagedTextEdit) reads and writes it. On every edit, the model is re-serialised to `.tex` and `tectonic` compiles it to PDF; **PyMuPDF** rasterises pages into the preview pane. **pygit2** auto-commits the `.tex` (the human-readable artefact) on save and pushes to `origin`. No component edits LaTeX strings directly — they all go through the model.

## Known limitations

- Pages render as one continuous editable surface with break lines marked — not yet separate floating page cards (would need a custom QAbstractTextDocumentLayout).
- Math equations are typed as LaTeX in a dialog; no visual equation editor.
- LaTeX errors appear in the preview pane as the log tail; not mapped to editor positions.
- `.doc` (old binary Word format) is not supported — convert to `.docx` first.
