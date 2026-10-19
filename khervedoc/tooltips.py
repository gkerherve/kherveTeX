"""Long hover help for every toolbar button, written for people coming
from Microsoft Word: what the button does, what it inserts, and what it
becomes in the LaTeX / PDF."""
from __future__ import annotations

from html import escape

# name -> (title, what it does, what it becomes in the PDF / LaTeX)
TIPS: dict[str, tuple[str, str, str]] = {
    # ----- file -----
    "act_new": ("New document",
        "Opens a blank document in this window. Choose a document type "
        "(article, report, thesis…) from the page-preview button later.",
        "Starts a fresh .ktex file with its own version history."),
    "act_open": ("Open",
        "Opens a KherveTeX document (.ktex / .ktexz), a LaTeX file (.tex) "
        "or a Word file (.docx) for editing.",
        "Word and LaTeX files are converted into editable paragraphs, "
        "headings, equations, figures and tables."),
    "act_save": ("Save",
        "Saves the document. Every save is also recorded in the version "
        "history, so you can go back to any earlier state.",
        "Writes the .ktex file and the LaTeX source next to it."),
    "act_export_pdf": ("Export PDF",
        "Compiles the document and saves the finished PDF where you "
        "choose, ready to send or submit.",
        "Typeset by LaTeX, exactly as shown in the preview panel."),
    "act_print": ("Print",
        "Prints the compiled PDF, with a preview of the pages first.",
        "Prints the typeset pages, not the editing view."),
    "act_open_project": ("Open project",
        "Opens a multi-chapter project: a folder of chapter documents "
        "compiled together into one book or thesis.",
        "Each chapter becomes an \\include{} in one master document."),
    "act_undo": ("Undo",
        "Reverses your last change. Press again to keep stepping back.",
        "Only affects the editor; saved versions stay in the history."),
    "act_redo": ("Redo",
        "Puts back the change you just undid.", ""),
    "act_cut": ("Cut",
        "Removes the selection and keeps it on the clipboard to paste "
        "elsewhere.", ""),
    "act_copy": ("Copy",
        "Copies the selection to the clipboard.", ""),
    "act_paste": ("Paste",
        "Inserts what is on the clipboard. A copied picture, screenshot or "
        "Word / PowerPoint figure becomes a figure in the document.",
        "Pictures become a figure float with \\includegraphics."),
    # ----- font -----
    "act_bold": ("Bold",
        "Makes the selected text bold, or turns bold on for what you "
        "type next.", "Becomes \\textbf{…}."),
    "act_italic": ("Italic",
        "Makes the selected text italic — for emphasis, titles of works, "
        "Latin terms and species names.", "Becomes \\textit{…}."),
    "act_underline": ("Underline",
        "Underlines the selected text. In printed science writing, "
        "italic is usually preferred for emphasis.",
        "Becomes \\underline{…}."),
    "act_strike": ("Strikethrough",
        "Draws a line through the selected text, e.g. to show deleted "
        "wording.", "Becomes \\sout{…} (ulem package)."),
    "act_sub": ("Subscript",
        "Lowers the selected text and makes it smaller, as in H₂O. For "
        "maths use the equation buttons instead.",
        "Becomes \\textsubscript{…}."),
    "act_super": ("Superscript",
        "Raises the selected text and makes it smaller, as in 10³ or 1st.",
        "Becomes \\textsuperscript{…}."),
    "act_smallcaps": ("Small capitals",
        "Shows lowercase letters as small capitals — used for acronyms "
        "and author names in some styles.", "Becomes \\textsc{…}."),
    "act_code": ("Code (monospace)",
        "Sets the selection in a typewriter font, for code, file names "
        "and commands.", "Becomes \\texttt{…}."),
    "act_highlight": ("Highlight",
        "Marks the selected text with a coloured background, like a "
        "highlighter pen — handy for review notes to yourself or "
        "co-authors.", "Becomes \\colorbox{…}{…} in the PDF."),
    # ----- paragraph -----
    "act_bullet": ("Bullet list",
        "Turns the current paragraph into a bulleted list. Press Enter "
        "for the next item; Enter on an empty item ends the list.",
        "Becomes \\begin{itemize} … \\item … \\end{itemize}."),
    "act_numbered": ("Numbered list",
        "Turns the current paragraph into a numbered list (1, 2, 3…). "
        "Numbers update by themselves when you add or move items.",
        "Becomes \\begin{enumerate} … \\end{enumerate}."),
    "act_align_left": ("Align left",
        "Lines the paragraph up on the left margin with a ragged right "
        "edge.", "Becomes a flushleft environment."),
    "act_align_center": ("Centre",
        "Centres the paragraph between the margins.",
        "Becomes a center environment."),
    "act_align_right": ("Align right",
        "Lines the paragraph up on the right margin.",
        "Becomes a flushright environment."),
    "act_align_justify": ("Justify",
        "Spreads each line to touch both margins — the normal look of "
        "books and journal articles.", "LaTeX's default; no extra code."),
    "act_show_marks": ("Show formatting marks",
        "Shows spaces as dots and the end of each paragraph as ¶, like "
        "Word's ¶ button — useful to spot double spaces and empty lines.",
        "Display only; nothing changes in the PDF."),
    # ----- review -----
    "act_spell_check": ("Spelling",
        "Underlines misspelled English words in red as you type. "
        "Right-click a word for suggestions.",
        "Display only; nothing changes in the PDF."),
    "act_comment": ("New comment",
        "Attaches a comment to the selected text, like Word's Review ▸ "
        "New Comment. Co-authors see it in the margin.",
        "Shown as a margin note (todonotes) in the PDF while reviewing."),
    "act_accept_comment": ("Accept",
        "Accepts the comment or highlight at the cursor: the note is "
        "removed and the text is kept.", ""),
    "act_reject_comment": ("Reject",
        "Rejects the comment or highlight at the cursor and removes it.",
        ""),
    "act_commit_now": ("Save snapshot and upload",
        "Records the current state as a named version in the history "
        "and uploads it to your online backup (GitHub), if one is set up.",
        "Nothing changes in the document itself."),
    "act_history": ("Version history",
        "Shows every saved version with what changed, and lets you open "
        "or restore any of them — like Word's Version History.", ""),
    # ----- compile -----
    "act_compile_range": ("Compile range",
        "When on, only the part between your compile markers is "
        "typeset, so a long thesis previews in seconds.",
        "The final export always uses the whole document."),
    "act_skip_images": ("Skip images",
        "When on, pictures are left out of the preview to make it "
        "faster. Turn it off to see them again.",
        "Export PDF still includes every image."),
    "act_compile_now": ("Compile PDF",
        "Typesets the document now and refreshes the PDF preview.",
        "Runs LaTeX (tectonic) on the generated source."),
    "act_auto_compile": ("Auto-compile",
        "When on, the PDF preview refreshes by itself a moment after "
        "you stop typing.", ""),
    # ----- insert (side toolbar) -----
    "act_math_inline": ("Inline equation",
        "Inserts a small equation inside the line of text, such as "
        "E = mc². Type LaTeX maths or use the symbol palette.",
        "Becomes $…$."),
    "act_math_block": ("Display equation",
        "Inserts an equation on its own centred line, numbered so you "
        "can refer to it — like Word's Insert ▸ Equation.",
        "Becomes \\begin{equation} … \\end{equation}."),
    "act_symbol": ("Symbol",
        "Opens a palette of Greek letters, arrows, operators and other "
        "symbols to insert at the cursor.",
        "Each symbol becomes its LaTeX command, e.g. \\alpha."),
    "act_equation_builder": ("Equation builder",
        "Builds an equation with buttons for fractions, roots, sums, "
        "integrals and matrices, with a live preview — no LaTeX needed.",
        "Inserted as LaTeX maths."),
    "act_chemistry": ("Chemical reaction",
        "Writes chemical formulas and reactions with correct subscripts, "
        "charges and arrows, e.g. 2H₂ + O₂ → 2H₂O.",
        "Becomes \\ce{…} (mhchem package)."),
    "act_chemfig": ("Chemical structure",
        "Draws a skeletal structure of a molecule (bonds, rings, atoms) "
        "to place in the text.", "Becomes a \\chemfig{…} drawing."),
    "act_link": ("Hyperlink",
        "Turns the selected text into a clickable link to a web page or "
        "e-mail address.", "Becomes \\href{url}{text}; clickable in the PDF."),
    "act_footnote": ("Footnote",
        "Adds a numbered note at the bottom of the page, with the number "
        "placed at the cursor.", "Becomes \\footnote{…}."),
    "act_citation": ("Citation",
        "Cites a reference from your KherveRef library at the cursor. "
        "The reference list at the end is built automatically.",
        "Becomes \\cite{key} (or \\citep / \\citet); the reference list uses the document's bibliography style."),
    "act_crossref": ("Cross-reference",
        "Refers to a numbered figure, table, equation or section, e.g. "
        "\"see Figure 3\". The number updates if things move.",
        "Becomes \\ref{label}."),
    "act_figure": ("Figure",
        "Inserts a picture from a file, with a caption and a label so "
        "you can cross-reference it. You can also paste or drag a "
        "picture straight into the page.",
        "Becomes a numbered figure float with \\includegraphics and "
        "\\caption; LaTeX places it at the best position."),
    "act_table": ("Table",
        "Inserts a table with the rows and columns you choose, plus a "
        "caption. Type in the cells like in Word.",
        "Becomes a numbered table float with a tabular inside."),
    "act_drawing": ("Drawing",
        "Opens a drawing canvas for diagrams, sketches and schematics "
        "that stay editable later.",
        "Inserted as a vector figure in the PDF."),
    "act_flowchart": ("Flowchart builder",
        "Builds a flowchart from boxes and arrows, laid out for you.",
        "Inserted as a figure drawn with TikZ."),
    "act_cols_1": ("One column",
        "Sets the page to a single column of text.", ""),
    "act_cols_2": ("Two columns",
        "Sets the page to two columns, as in most journals.",
        "Uses the class's twocolumn option."),
    "act_cols_3": ("Three columns",
        "Sets the page to three columns, as in newsletters and posters.",
        "Wraps the text in a multicols environment."),
    "act_pagebreak": ("Page break",
        "Starts a new page at the cursor, like Ctrl+Enter in Word.",
        "Becomes \\newpage."),
    "act_hrule": ("Horizontal line",
        "Inserts a thin line across the page to separate sections.",
        "Becomes \\hrulefill."),
    # ----- view tab -----
    "act_page_visual": ("Visual",
        "The page as it will print, where you write — like Word's Print "
        "Layout view.", ""),
    "act_page_code": ("Code",
        "The LaTeX source KherveTeX generates from your document. Edits "
        "there flow back into the page.", ""),
    "act_page_console": ("Console",
        "The compiler's log: warnings and errors from the last PDF build.",
        ""),
    "act_pdf_panel": ("PDF preview",
        "Shows the compiled PDF beside the page, refreshed as you type. "
        "Turn it off to write with the page alone.", ""),
    "act_pdf_detach": ("Detach PDF",
        "Moves the PDF preview into its own window, e.g. for a second "
        "screen. Release it to put it back beside the page.", ""),
    # ----- table tab -----
    "act_tbl_row_above": ("Insert row above",
        "Adds an empty row above the row the cursor is in.", ""),
    "act_tbl_row_below": ("Insert row below",
        "Adds an empty row below the row the cursor is in.", ""),
    "act_tbl_col_left": ("Insert column left",
        "Adds an empty column to the left of the cursor's column.", ""),
    "act_tbl_col_right": ("Insert column right",
        "Adds an empty column to the right of the cursor's column.", ""),
    "act_tbl_del_row": ("Delete row",
        "Removes the row the cursor is in. Deleting the last row "
        "removes the table.", ""),
    "act_tbl_del_col": ("Delete column",
        "Removes the column the cursor is in. Deleting the last column "
        "removes the table.", ""),
    "act_tbl_delete": ("Delete table",
        "Removes the whole table, with its caption.", ""),
    "act_tbl_plain": ("Grid lines",
        "Classic look: a rule above, below and under the header row.",
        "Uses \\hline rules."),
    "act_tbl_booktabs": ("Journal style",
        "The look most journals ask for: heavier top and bottom rules, "
        "a thin one under the header, no vertical lines.",
        "Uses \\toprule, \\midrule and \\bottomrule (booktabs)."),
    # ----- picture tab -----
    "act_fig_left": ("Align picture left",
        "Places the picture against the left margin. The paragraph align "
        "buttons on Home do the same while a picture is selected.",
        "Becomes \\raggedright in the figure."),
    "act_fig_center": ("Centre picture",
        "Centres the picture between the margins (the usual choice).",
        "Becomes \\centering in the figure."),
    "act_fig_right": ("Align picture right",
        "Places the picture against the right margin.",
        "Becomes \\raggedleft in the figure."),
    "act_fig_w25": ("Quarter width",
        "Makes the picture a quarter of the text width. You can also drag "
        "any of the eight handles around the picture.",
        "width=0.25\\textwidth"),
    "act_fig_w50": ("Half width", "Makes the picture half the text width.",
        "width=0.50\\textwidth"),
    "act_fig_w75": ("Three-quarter width",
        "Makes the picture three quarters of the text width.",
        "width=0.75\\textwidth"),
    "act_fig_w100": ("Full width",
        "Makes the picture as wide as the text.", "width=1.00\\textwidth"),
    "act_fig_edit": ("Edit drawing",
        "Re-opens the drawing or flowchart this picture was made with.", ""),
    "act_fig_delete": ("Delete picture",
        "Removes the picture and its caption from the document.", ""),
    # ----- equation tab -----
    "act_eq_edit": ("Edit equation",
        "Opens the equation under the cursor in the equation editor.", ""),
    "act_eq_numbered": ("Numbered equation",
        "Pressed: the equation gets a number such as (1) at the right "
        "margin, so you can cross-reference it.",
        "Switches between equation and equation*."),
    "act_eq_delete": ("Delete equation",
        "Removes the display equation the cursor is in.", ""),
}

# Toolbar widgets that are not QActions.
WIDGET_TIPS: dict[str, tuple[str, str, str]] = {
    "style": ("Styles",
        "Click a style to apply it to the current paragraph — Normal for "
        "body text, Title, Heading 1–3. Styles ▾ lists every style, "
        "including Author, Affiliation, Abstract, Keywords and Chapter. "
        "Headings build the table of contents and are numbered "
        "automatically.",
        "Headings become \\section, \\subsection…; Title and Author feed "
        "\\maketitle."),
    "numbered": ("Numbered heading",
        "Pressed: the current heading gets a number (1, 1.1, 1.1.1) and "
        "appears in the table of contents. Released: it is unnumbered, "
        "e.g. for Acknowledgements.",
        "Unnumbered headings become \\section*{…}."),
    "class": ("Document type",
        "Chooses the overall design of the document — an article, "
        "report, book, thesis, slides, letter, CV, poster, or a "
        "journal's own template (IEEE, Elsevier, ACS, Springer…). Your "
        "text is kept; only the layout changes.",
        "Sets the LaTeX \\documentclass."),
    "fontsize": ("Font size",
        "Size of the body text in points. Headings scale with it.",
        "Most classes accept 10, 11 or 12 pt."),
    "pagesize": ("Size",
        "Paper size of the document: A4, US Letter or Legal, shown with "
        "its dimensions, as in Word's Layout > Size.",
        "Sets the geometry package's paper option."),
    "margins": ("Margins",
        "Word's margin presets (Normal, Narrow, Moderate, Wide), or "
        "Custom Margins… to type your own.",
        "Sets the geometry package's top / bottom / left / right."),
}


def html(title: str, what: str, latex: str = "", shortcut: str = "",
         state: str = "") -> str:
    head = f"<b>{escape(title)}</b>"
    if shortcut:
        head += f"&nbsp;&nbsp;<span style='color:#777'>({escape(shortcut)})</span>"
    parts = [head]
    if state:
        parts.append(f"<i>{escape(state)}</i>")
    parts.append(escape(what))
    if latex:
        parts.append(f"<span style='color:#777'>In the PDF: "
                     f"{escape(latex)}</span>")
    return ("<p style='white-space:normal; width:300px'>"
            + "<br><br>".join(parts) + "</p>")


def action_tip(name: str, action=None, state: str = "") -> str:
    title, what, latex = TIPS[name]
    shortcut = action.shortcut().toString() if action is not None else ""
    return html(title, what, latex, shortcut, state)


def widget_tip(key: str) -> str:
    return html(*WIDGET_TIPS[key])


def apply(window) -> None:
    """Give every toolbar button of *window* its long hover help."""
    for name in TIPS:
        act = getattr(window, name, None)
        if act is None:
            continue
        state = ""
        if name == "act_spell_check" and not act.isEnabled():
            state = "Install pyspellchecker to enable spell checking."
        act.setToolTip(action_tip(name, act, state))
    for btn in getattr(window, "_style_buttons", {}).values():
        btn.setToolTip(widget_tip("style"))
    for attr, key in (("_numbered_cb", "numbered"), ("_class_button", "class"),
                      ("_fontsize_combo", "fontsize"),
                      ("_size_button", "pagesize"),
                      ("_margins_button", "margins")):
        w = getattr(window, attr, None)
        if w is not None:
            w.setToolTip(widget_tip(key))
