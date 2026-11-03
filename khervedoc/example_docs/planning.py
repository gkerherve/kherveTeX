"""Printable planners and calendar, and research admin documents."""
from __future__ import annotations

import calendar as _cal
import datetime as _dt

from ..example_helpers import _items, _meta, _ord_items, _p
from ..model import (
    Author, Citation, CrossRef, DEFAULT_PACKAGES, Document, Footnote,
    MathBlock, RawLatex, Section, Table, Text, Title,
)
from .science import _bib, _eq, _m, _paper_meta, _sec


_BOX = ""  # an empty narrow cell is the tick box; a glyph would show as code in the visual tab
_TINT = "#E6E6E6"

# Planner tables are blank forms: an empty caption must print nothing, rows
# are taller than text so there is room to write, and pages carry no folio.
_PLANNER_PREAMBLE = (
    "\\makeatletter\n"
    "\\long\\def\\@makecaption#1#2{\\def\\@tmpcap{#2}\\def\\@tmpign{\\ignorespaces}"
    "\\ifx\\@tmpcap\\@empty\\else\\ifx\\@tmpcap\\@tmpign\\else"
    "\\vskip 8pt\\centering #1: #2\\par\\fi\\fi}\n"
    "\\renewcommand{\\maketitle}{\\par\\noindent{\\LARGE\\bfseries\\@title}"
    "\\hfill{\\large\\@author}\\par\\vspace{3pt}\\hrule\\vspace{4pt}}\n"
    "\\makeatother\n"
    "\\date{}\\pagestyle{empty}\n"
    "\\setlength{\\parskip}{0pt}\\setlength{\\tabcolsep}{5pt}"
)


def _planner_meta(stretch: float, **kw):
    pre = _PLANNER_PREAMBLE + f"\n\\renewcommand{{\\arraystretch}}{{{stretch}}}"
    base = dict(
        title="", author="", body_font_pt=10, line_spacing=1.0,
        paragraph_indent=False, page_size="A4",
        packages=DEFAULT_PACKAGES + ["array", "booktabs", "xcolor"],
        preamble_extras=pre,
    )
    base.update(kw)
    return _meta(**base)


def _h(text: str, level: int = 2) -> Section:
    return Section(level=level, children=[Text(text=text)], numbered=False)


def _a(text_cm: float, *widths) -> str:
    """Column spec of p-columns that exactly fill the text width: a None
    entry takes whatever the fixed ones leave, and 'c' stays a centred
    column of natural width."""
    fixed = sum(w for w in widths if isinstance(w, float))
    n = len(widths)
    sep = n * 2 * 5 * 0.03515 + (n + 1) * 0.02
    flex = [w for w in widths if w is None]
    share = round((text_cm - fixed - sep) / max(len(flex), 1), 2)
    return "".join(f"p{{{share if w is None else w}cm}}" for w in widths)


def _blank_rows(n: int, first: str = _BOX) -> list[list[str]]:
    return [[first, ""] for _ in range(n)]


def _fmt_day(d: _dt.date) -> str:
    return f"{_cal.day_name[d.weekday()]} {d.day} {_cal.month_name[d.month]}"


def _week_start(today: _dt.date) -> _dt.date:
    return today - _dt.timedelta(days=today.weekday())


# --------------------------------------------------- daily journal

def daily_journal() -> Document:
    """Printable one-page daily planner for today: priorities, an hourly
    schedule from 07:00 to 19:00, a follow-up list and a short evening
    note. Built from the current date each time it is opened."""
    today = _dt.date.today()
    iso = today.isocalendar()
    hours = [[f"{h:02d}:00", "", ""] for h in range(7, 20)]
    return Document(
        meta=_planner_meta(
            1.95, margin_left_cm=1.6, margin_right_cm=1.6,
            margin_top_cm=1.3, margin_bottom_cm=1.0,
        ),
        children=[
            Title(children=[Text(text=_fmt_day(today))]),
            Author(children=[Text(
                text=f"{today.year} · week {iso[1]} · day "
                     f"{today.timetuple().tm_yday}")]),
            _h("Top priorities"),
            Table(rows=_blank_rows(3), alignment=_a(17.8, 0.7, None), style="grid"),
            _h("Schedule"),
            Table(rows=[["Time", "Plan", "Notes"]] + hours,
                  alignment=_a(17.8, 1.3, None, 4.6), style="grid", header=True),
            _h("To do and follow up"),
            Table(rows=_blank_rows(2), alignment=_a(17.8, 0.7, None),
                  style="grid"),
            _h("Evening review"),
            Table(rows=[["One win", ""], ["One lesson", ""],
                        ["First task tomorrow", ""]],
                  alignment=_a(17.8, 3.6, None), style="grid"),
        ],
    )


# --------------------------------------------------- weekly journal

def weekly_journal() -> Document:
    """Printable weekly planner for the current week (Monday to Sunday):
    goals, a day-by-day plan with today shaded, a habit tracker and an
    end-of-week review."""
    today = _dt.date.today()
    mon = _week_start(today)
    sun = mon + _dt.timedelta(days=6)
    days = [mon + _dt.timedelta(days=i) for i in range(7)]
    if mon.month == sun.month:
        span = f"{mon.day}–{sun.day} {_cal.month_name[sun.month]} {sun.year}"
    else:
        span = (f"{mon.day} {_cal.month_name[mon.month]} – "
                f"{sun.day} {_cal.month_name[sun.month]} {sun.year}")

    plan = [["Day", "Plan and appointments", "Evening"]]
    shading = {}
    for i, d in enumerate(days):
        plan.append([f"{_cal.day_abbr[d.weekday()]} {d.day}", "", ""])
        if d == today:
            shading.update({f"{i + 1},{c}": _TINT for c in range(3)})

    habits = [["Habit", "M", "T", "W", "T", "F", "S", "S"]] + [
        [h, "", "", "", "", "", "", ""] for h in (
            "Exercise (30 min)", "Read (20 pages)", "In bed before 23:00",
            "Two litres of water", "Plan tomorrow", "")]

    review = [["Review", "Notes"], ["Wins", ""], ["", ""],
              ["To improve", ""], ["", ""],
              ["Carry over", ""], ["", ""]]

    return Document(
        meta=_planner_meta(
            1.7, margin_left_cm=1.8, margin_right_cm=1.8,
            margin_top_cm=1.4, margin_bottom_cm=1.2,
        ),
        children=[
            Title(children=[Text(text=f"Week {today.isocalendar()[1]}")]),
            Author(children=[Text(text=span)]),
            _h("Goals for the week"),
            Table(rows=_blank_rows(3), alignment=_a(17.4, 0.7, None), style="grid"),
            _h("Week at a glance"),
            Table(rows=plan, alignment=_a(17.4, 1.7, None, 4.9), style="grid",
                  header=True, shading=shading),
            _h("Habit tracker"),
            Table(rows=habits, alignment=_a(17.4, None, *[1.1] * 7), style="grid",
                  header=True),
            _h("End-of-week review"),
            Table(rows=review, alignment=_a(17.4, 2.6, None), style="grid",
                  header=True,
                  merges=[[1, 0, 2, 1], [3, 0, 2, 1], [5, 0, 2, 1]]),
        ],
    )


# --------------------------------------------------- monthly journal

def monthly_journal() -> Document:
    """Printable monthly planner for the current month: goals, a week by
    week outline with dates, key dates, a small metrics table and a
    month-end review."""
    today = _dt.date.today()
    y, m = today.year, today.month
    weeks = _cal.Calendar(0).monthdatescalendar(y, m)
    outline = [["Week", "Dates", "Focus", "Milestones"]]
    shading = {}
    for i, w in enumerate(weeks):
        first = max(w[0], _dt.date(y, m, 1))
        last = min(w[-1], _dt.date(y, m, _cal.monthrange(y, m)[1]))
        if first == last:
            dates = f"{first.day} {_cal.month_abbr[m]}"
        else:
            dates = f"{first.day}–{last.day} {_cal.month_abbr[m]}"
        outline.append([str(w[0].isocalendar()[1]), dates, "", ""])
        if w[0] <= today <= w[-1]:
            shading.update({f"{i + 1},{c}": _TINT for c in range(4)})

    return Document(
        meta=_planner_meta(
            1.4, margin_left_cm=2.0, margin_right_cm=2.0,
            margin_top_cm=1.6, margin_bottom_cm=1.4,
        ),
        children=[
            Title(children=[Text(text=f"{_cal.month_name[m]} {y}")]),
            Author(children=[Text(text="Monthly planner")]),
            _h("Goals for the month"),
            Table(rows=[["", "Goal", "How I will know it is done"]]
                  + [[_BOX, "", ""] for _ in range(4)],
                  alignment=_a(17.0, 0.7, None, 6.5), style="grid", header=True),
            _h("Week by week"),
            Table(rows=outline, alignment=_a(17.0, 1.4, 2.8, None, 5.4),
                  style="grid", header=True, shading=shading),
            _h("Key dates"),
            Table(rows=[["Date", "Event"]] + [["", ""] for _ in range(5)],
                  alignment=_a(17.0, 2.6, None), style="grid", header=True),
            _h("Measures"),
            Table(rows=[["Measure", "Target", "Actual"],
                        ["Focused work (hours)", "", ""],
                        ["Exercise days", "", ""],
                        ["Pages or chapters read", "", ""],
                        ["Money in / out", "", ""]],
                  alignment=_a(17.0, None, 4.6, 4.6), style="grid",
                  header=True),
            _h("Month-end review"),
            Table(rows=[["Review", "Notes"],
                        ["What went well", ""], ["", ""],
                        ["What to change", ""], ["", ""],
                        ["Next month", ""], ["", ""]],
                  alignment=_a(17.0, 3.6, None), style="grid", header=True,
                  merges=[[1, 0, 2, 1], [3, 0, 2, 1], [5, 0, 2, 1]]),
        ],
    )


# --------------------------------------------------- calendar

def _calendar_latex(year: int, month: int, today: _dt.date | None = None) -> str:
    """Landscape wall-calendar grid: the month name and year above seven
    weekday columns; every cell has the day number at the top and room to
    write below. Days of the neighbouring months are greyed, today is
    marked with a black number."""
    weeks = _cal.Calendar(0).monthdatescalendar(year, month)
    cell_h = round(16.2 / len(weeks), 2)
    L = [
        "\\noindent{\\fontsize{34}{36}\\selectfont\\bfseries "
        f"{_cal.month_name[month]}}}\\hfill{{\\fontsize{{26}}{{30}}"
        f"\\selectfont\\color{{black!55}}{year}}}\\par\\vspace{{5pt}}",
        "\\setlength{\\tabcolsep}{2pt}\\renewcommand{\\arraystretch}{1}",
        "\\noindent\\makebox[\\textwidth][c]{%",
        "\\begin{tabular}{|" + "l|" * 7 + "}",
        "\\hline",
        " & ".join(
            f"\\parbox[c][0.7cm][c]{{3.85cm}}{{\\centering\\bfseries "
            f"\\textsc{{{n}}}}}" for n in _cal.day_name) + " \\\\",
        "\\hline",
    ]
    for w in weeks:
        cells = []
        for d in w:
            if d == today:
                num = (f"\\colorbox{{black}}{{\\textcolor{{white}}"
                       f"{{\\bfseries\\,{d.day}\\,}}}}")
            elif d.month != month:
                num = f"\\textcolor{{black!40}}{{{d.day}}}"
            else:
                num = f"\\textbf{{{d.day}}}"
            cells.append(
                f"\\parbox[t][{cell_h}cm][t]{{3.85cm}}"
                f"{{\\raggedleft\\small {num}}}")
        L.append(" & ".join(cells) + " \\\\")
        L.append("\\hline")
    L.append("\\end{tabular}}")
    return "\n".join(L)


def calendar() -> Document:
    """Landscape monthly calendar for the current month: one big page,
    weekday headers, a tall writing space in every day and today marked."""
    today = _dt.date.today()
    return Document(
        meta=_meta(
            title="", author="", body_font_pt=10,
            margin_left_cm=0.8, margin_right_cm=0.8,
            margin_top_cm=0.8, margin_bottom_cm=0.6,
            paragraph_indent=True, line_spacing=1.0, page_size="A4",
            class_options="landscape",
            preamble_extras="\\geometry{landscape}\n\\pagestyle{empty}",
            packages=DEFAULT_PACKAGES + ["array", "xcolor"],
        ),
        children=[
            RawLatex(text=_calendar_latex(today.year, today.month, today)),
        ],
    )


def _nodate(meta):
    meta.preamble_extras += "\n\\date{}"
    return meta


def _ref(label: str, kind: str = "ref") -> CrossRef:
    return CrossRef(label=label, kind=kind)


# --------------------------------------------------------- grant proposal

def grant_proposal() -> Document:
    """Research grant proposal with work packages, Gantt and budget."""
    return Document(
        meta=_nodate(_paper_meta("Grant proposal", "Q. Principal")),
        children=[
            Title(children=[Text(text=
                "SOLAR-CAT: Defect-engineered photocatalysts for solar "
                "hydrogen")]),
            Author(children=[Text(text=
                "Principal Investigator: Q. Principal · "
                "Co-Investigators: R. Coinvest, S. Partner")]),

            _sec("Summary"),
            _p("Green hydrogen from direct solar water splitting could "
               "decarbonise heavy industry, but particulate photocatalysts "
               "remain below 1 % solar-to-hydrogen (STH) efficiency. "
               "SOLAR-CAT combines in-situ spectroscopy, machine-learned "
               "defect models and high-throughput synthesis to reach 3 % "
               "STH in a 1 m² panel within 36 months, at a total cost of "
               "£1.51 M."),

            _sec("Objectives"),
            _ord_items(
                "O1 — Map the link between oxygen-vacancy density and "
                "carrier lifetime in doped SrTiO₃ (WP1, WP2).",
                "O2 — Train a surrogate model that predicts STH from "
                "synthesis parameters, with a mean absolute error below "
                "0.2 % (WP3).",
                "O3 — Demonstrate a 1 m² panel with ≥ 3 % STH over "
                "1000 h of outdoor operation (WP4).",
            ),

            _sec("State of the art and ambition"),
            _p("The STH efficiency is the hydrogen power produced per "
               "unit of incident solar power, and factorises into "
               "absorption, charge-separation and surface-reaction "
               "yields:"),
            _eq(r"\eta_{\text{STH}} = \frac{r_{\text{H}_2}\,\Delta G^\circ}"
                r"{P_{\text{sun}}\,A} = \eta_{\text{abs}}\,"
                r"\eta_{\text{sep}}\,\eta_{\text{cat}},",
                "eq:sth"),
            _p("with ", _m(r"\Delta G^\circ = 237\ \text{kJ mol}^{-1}"),
               " for water splitting. Al-doped SrTiO₃ shows near-unity "
               "quantum efficiency under ultraviolet light ",
               Citation(keys=["hartley2024"]),
               ", but the UV is only about 4 % of the solar spectrum. "
               "Visible-light designs have so far lost most of their "
               "carriers to defect-mediated recombination ",
               Citation(keys=["nguyen2025"]), "."),
            _p("Our target in Eq. ", _ref("eq:sth", "eqref"),
               " is ", _m(r"\eta_{\text{STH}} = 3\,\%"),
               ", reached for example with ",
               _m(r"\eta_{\text{abs}} = 0.45"), ", ",
               _m(r"\eta_{\text{sep}} = 0.25"), " and ",
               _m(r"\eta_{\text{cat}} = 0.27"),
               ". Under AM1.5G illumination (1000 W m⁻²) this means 30 W "
               "of hydrogen from 1 m², i.e. 0.46 mol h⁻¹ or about 10 L "
               "h⁻¹ at standard conditions.",
               Footnote(children=[Text(text=
                   "STH is defined for unbiased, overall water splitting "
                   "under simulated AM1.5G light; sacrificial-agent "
                   "experiments do not count towards the target.")])),

            _sec("Work plan"),
            _p("The project has five work packages (Table ",
               _ref("tab:wp"), ") laid out over twelve quarters (Table ",
               _ref("tab:gantt"), ")."),
            Table(rows=[
                ["WP", "Title", "Lead", "Months", "Person-months"],
                ["WP1", "Synthesis and doping", "Principal", "1–24", "30"],
                ["WP2", "In-situ spectroscopy", "Coinvest", "4–30", "24"],
                ["WP3", "Machine-learning models", "Partner", "6–33", "18"],
                ["WP4", "Panel demonstrator", "Principal", "18–36", "20"],
                ["WP5", "Management and dissemination", "Principal",
                 "1–36", "6"],
                ["", "Total", "", "", "98"],
            ], caption="Work packages.", label="tab:wp",
               alignment="lllcr", style="booktabs"),
            Table(rows=[
                ["WP", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8",
                 "Q9", "Q10", "Q11", "Q12"],
                ["WP1"] + ["■"] * 8 + [""] * 4,
                ["WP2", ""] + ["■"] * 9 + ["", ""],
                ["WP3", ""] + ["■"] * 10 + [""],
                ["WP4"] + [""] * 5 + ["■"] * 7,
                ["WP5"] + ["■"] * 12,
            ], caption="Gantt chart by quarter (Q1 = months 1–3).",
               label="tab:gantt", alignment="lcccccccccccc",
               style="booktabs"),

            _sec("Milestones and deliverables"),
            Table(rows=[
                ["\\#", "Milestone", "Month", "Verification"],
                ["M1", "Library of 200 doped compositions", "12",
                 "Open database released"],
                ["M2", "Surrogate model with MAE < 0.2 \\%", "24",
                 "Blind test set"],
                ["M3", "1 m² panel reaching ≥ 3 \\% STH", "33",
                 "Independent certification"],
                ["M4", "1000 h outdoor operation completed", "36",
                 "Public performance report"],
            ], caption="Milestones.", label="tab:ms", alignment="llcl",
               style="booktabs"),
            _p("Milestone M3 depends on the model of WP3: the 200 "
               "compositions of M1 provide the training data, and "
               "active learning selects the next 50 samples ",
               Citation(keys=["nguyen2025"]), "."),

            _sec("Risk management"),
            Table(rows=[
                ["Risk", "Likelihood", "Impact", "Mitigation"],
                ["Visible absorption insufficient", "Medium", "High",
                 "Fallback: tandem with BiVO₄"],
                ["Model under-performs", "Medium", "Medium",
                 "Active learning; more DFT data"],
                ["Panel degradation", "Low", "High",
                 "Encapsulation study in WP4 ",],
                ["Key staff leave", "Low", "Medium",
                 "Cross-training; two PDRAs per WP"],
            ], caption="Risk register.", label="tab:risk",
               alignment="lccl", style="booktabs"),

            _sec("Budget"),
            _p("Table ", _ref("tab:budget"), " summarises the request. "
               "Indirect costs are 80 % of staff costs, following the "
               "funder’s full-economic-costing rules."),
            Table(rows=[
                ["Category", "Year 1 (£k)", "Year 2 (£k)", "Year 3 (£k)",
                 "Total (£k)"],
                ["Staff", "210", "215", "220", "645"],
                ["Equipment", "180", "20", "10", "210"],
                ["Consumables", "35", "40", "30", "105"],
                ["Travel and dissemination", "8", "10", "14", "32"],
                ["Indirect (80 \\% of staff)", "168", "172", "176", "516"],
                ["Total", "601", "457", "450", "1508"],
            ], caption="Budget summary.", label="tab:budget",
               alignment="lrrrr", style="booktabs"),

            _sec("Impact and pathways"),
            _items(
                "Academic: FAIR open data and open-source models, "
                "released with milestone M1.",
                "Industrial: partnership with a panel manufacturer for "
                "scale-up beyond 1 m².",
                "Societal: public engagement through a solar-fuels "
                "exhibit.",
                "Training: 2 postdoctoral researchers and 3 PhD "
                "students.",
            ),
            _bib(
                ("hartley2024", "M. Hartley and L. Okafor, \\emph{J. "
                                "Photocatal. Sci.} \\textbf{12}, 345 "
                                "(2024)."),
                ("nguyen2025", "P. Nguyen, S. Aalto and R. Dube, "
                               "\\emph{Adv. Surf. Chem.} \\textbf{8}, "
                               "101 (2025)."),
            ),
        ],
    )


# ------------------------------------------------------- reviewer response

def response_to_reviewers() -> Document:
    """Point-by-point rebuttal letter for a manuscript revision."""
    return Document(
        meta=_nodate(_paper_meta("Response to reviewers", "A. Surface")),
        children=[
            Title(children=[Text(text="Response to Reviewers")]),
            Author(children=[Text(text="Manuscript APSUSC-D-26-01234 "
                                       "(revised)")]),
            _p(("Title: ", ["bold"]),
               "Oxygen vacancies and Ti³⁺ states in reduced anatase TiO₂ "
               "thin films"),
            _p("Dear Editor,"),
            _p("We thank you and the reviewers for the careful reading "
               "of our manuscript. We have addressed every comment. "
               "Reviewer comments are in ", ("bold", ["bold"]),
               ", our responses in plain text, and text added to the "
               "manuscript is in ", ("italics", ["italic"]),
               ". Page and line numbers refer to the revised version; "
               "Table ", _ref("tab:changes"),
               " lists all changes."),

            _sec("Reviewer 1"),
            _p(("Comment 1.1 — The Ti³⁺ component could be an artefact "
                "of differential charging. Please justify.", ["bold"])),
            _p("We agree this must be excluded. We repeated the "
               "measurements with the flood gun at three emission "
               "currents; the Ti⁴⁺–Ti³⁺ separation varied by less than "
               "0.03 eV (new Table S2). In addition, the Ti³⁺ fraction "
               "",
               _m(r"f_{3+} = A_{3+}/(A_{3+}+A_{4+})"),
               " is reversible upon re-oxidation in 10⁻⁶ mbar O₂, which "
               "charging artefacts would not be."),
            _p(("Added (p. 6, l. 142): “The chemical shift was invariant "
                "to neutraliser settings within 0.03 eV (Table S2).”",
                ["italic"])),
            _p(("Comment 1.2 — Why is the Lorentzian fraction fixed "
                "at 0.3?", ["bold"])),
            _p("Leaving ", _m(r"\eta"), " free led to strong "
               "correlation with the FWHM (", _m(r"|\rho| = 0.94"),
               "). We now report a sensitivity analysis over ",
               _m(r"\eta \in [0.2,\,0.4]"),
               ", in which the Ti³⁺ fraction changes by at most 0.6 "
               "percentage points:"),
            MathBlock(latex=r"\max_{\eta\in[0.2,\,0.4]}\bigl|f_{3+}(\eta)"
                            r"-f_{3+}(0.3)\bigr| \le 0.006 .",
                      numbered=True, label="eq:sens"),
            _p(("Added (p. 5, l. 118): “Varying the Lorentzian fraction "
                "between 0.2 and 0.4 changes the Ti³⁺ fraction by at "
                "most 0.6 percentage points (Table S3).”",
                ["italic"])),

            _sec("Reviewer 2"),
            _p(("Comment 2.1 — The activation energy seems low. Compare "
                "with the literature.", ["bold"])),
            _p("We have added a comparison with three previous "
               "studies (new Table 3) and discussed the role of the "
               "oxygen chemical potential in UHV, ",
               _m(r"\Delta\mu_{\text{O}}(T,p)"), ", which lowers the "
               "effective formation energy.",
               Footnote(children=[Text(text=
                   "At 700 K and 10⁻⁹ mbar the chemical potential is "
                   "about 1.5 eV below its value in air, which accounts "
                   "for most of the difference.")])),
            _p(("Comment 2.2 — Minor: typo in Eq. (3).", ["bold"])),
            _p("Corrected, thank you."),
            _p(("Comment 2.3 — Please deposit the raw spectra.",
                ["bold"])),
            _p("The raw spectra (VAMAS format) and fit files are now in "
               "a public repository; the link is in the Data "
               "availability statement."),

            _sec("Summary of changes"),
            Table(rows=[
                ["Section", "Change", "Prompted by"],
                ["Methods", "Charging control experiments", "R1.1"],
                ["Methods", "Sensitivity analysis on η", "R1.2"],
                ["Discussion", "Literature comparison, Table 3", "R2.1"],
                ["Eq. (3)", "Typo corrected", "R2.2"],
                ["Data availability", "Repository link added", "R2.3"],
                ["SI", "New Tables S2–S3", "R1.1, R1.2"],
            ], caption="All changes to the manuscript.",
               label="tab:changes", alignment="lll", style="booktabs"),
            _p("We believe the manuscript is substantially improved "
               "and hope it is now suitable for publication."),
            _p("Yours sincerely,"),
            _p("A. Surface, on behalf of all authors"),
        ],
    )


# ------------------------------------------------------------------ SOP

def lab_sop() -> Document:
    """Laboratory standard operating procedure with risk assessment."""
    return Document(
        meta=_nodate(_paper_meta("Standard operating procedure", "Lab manager")),
        children=[
            Title(children=[Text(text=
                "SOP-CHEM-014: Preparation of Piranha solution and "
                "cleaning of silicon substrates")]),
            Author(children=[Text(text=
                "Version 3.1 · Approved by: T. Safety · Review due: "
                "September 2027")]),

            Table(rows=[
                ["Document", "SOP-CHEM-014", "Location", "Fume hood FH-3"],
                ["Owner", "Lab manager", "Emergency", "ext. 2222"],
                ["Applies to", "All FH-3 users", "Training", "Required"],
            ], caption="Document control.", label="tab:doc",
               alignment="llll", style="booktabs"),

            _sec("Purpose and scope"),
            _p("This SOP describes the preparation and use of Piranha "
               "solution (3:1 H₂SO₄ : H₂O₂ by volume) to remove organic "
               "residues from Si wafers. It applies to all users of fume "
               "hood FH-3 in the Materials Chemistry laboratory. Do not "
               "use Piranha on wafers carrying photoresist residue in "
               "solvent; rinse and dry them first."),

            _sec("Hazards"),
            _p("Table ", _ref("tab:risk"), " lists the hazards before "
               "controls are applied."),
            Table(rows=[
                ["Hazard", "Severity", "Likelihood", "Risk", "Control"],
                ["Violent exotherm with organics", "5", "2", "10",
                 "No solvents in hood; small volumes"],
                ["Severe chemical burns", "4", "2", "8",
                 "Face shield, acid apron, neoprene gloves"],
                ["Pressure build-up in closed vessel", "5", "1", "5",
                 "Never cap; cool in open beaker"],
                ["Spill", "3", "2", "6", "Spill kit at FH-3; bund tray"],
            ], caption="Risk assessment (risk = severity × likelihood, "
                       "range 1–25).", label="tab:risk",
               alignment="lccrp{4.6cm}", style="booktabs"),

            _sec("Personal protective equipment"),
            _items(
                "Full face shield over safety goggles",
                "Acid-resistant apron and lab coat",
                "Heavy neoprene or butyl gloves over nitrile",
                "Closed shoes; work only with a second person present",
            ),

            _sec("Procedure"),
            _ord_items(
                "Clear the fume hood of all organic solvents and "
                "combustibles.",
                "Place a clean Pyrex beaker in the bund tray.",
                "Add 30 mL concentrated H₂SO₄ (96 %).",
                "Slowly add 10 mL H₂O₂ (30 %) — ALWAYS peroxide to "
                "acid. The mixture will reach about 120 °C.",
                "Immerse wafers with PTFE tweezers for 15 min.",
                "Rinse in three successive DI-water baths, then "
                "blow dry with N₂.",
                "Allow the solution to cool completely (at least 2 h) "
                "in the open beaker before disposal.",
            ),
            _p("The heat released on mixing can be estimated from the "
               "enthalpy of mixing. For 0.54 mol of acid (30 mL), an "
               "assumed ", _m(r"|\Delta H_{\text{mix}}| = 20\ "
                              r"\text{kJ mol}^{-1}"),
               ", a total mass of 66 g and ",
               _m(r"c_p = 1.8\ \text{J g}^{-1}\text{K}^{-1}"),
               ", the temperature rise is"),
            _eq(r"\Delta T \approx \frac{n\,|\Delta H_{\text{mix}}|}"
                r"{m\,c_p} = \frac{0.54 \times 2.0\times 10^{4}}"
                r"{66 \times 1.8}\ \text{K} \approx 90\ \text{K},",
                "eq:heat"),
            _p("which, from room temperature, gives the 120 °C quoted "
               "in the procedure. Eq. ", _ref("eq:heat", "eqref"),
               " is why the peroxide must be added slowly and the "
               "volumes kept small."),

            _sec("Waste disposal"),
            _p("Cooled Piranha is collected in the labelled vented "
               "container “Piranha waste — do not cap tightly”. Never "
               "pour it into the general acid-waste drum."),

            _sec("Emergency procedures"),
            _items(
                "Skin contact: drench in the safety shower for at least "
                "15 min, remove contaminated clothing, call a first "
                "aider.",
                "Eye contact: use the eyewash for at least 15 min and "
                "seek medical attention.",
                "Spill over 50 mL: evacuate and call the emergency "
                "number 2222.",
            ),

            _sec("Record of training"),
            Table(rows=[
                ["Name", "Trained by", "Date", "Signature"],
                ["J. Okoye", "T. Safety", "12 Jan 2026", "J.O."],
                ["M. Lindqvist", "T. Safety", "03 Mar 2026", "M.L."],
                ["", "", "", ""],
                ["", "", "", ""],
            ], caption="Training record (extend as users are trained).",
               label="tab:training", alignment="llll", style="booktabs"),
        ],
    )
