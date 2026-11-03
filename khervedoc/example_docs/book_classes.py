"""One example for each book class: memoir, KOMA, Tufte, amsbook."""
from __future__ import annotations

from ..example_helpers import _items, _meta, _ord_items, _p
from ..model import (
    Author, Citation, CrossRef, DEFAULT_PACKAGES, Document, Footnote,
    InlineRaw, MathBlock, MathInline, RawLatex, Section, Table, Text,
    Theorem, Title,
)


def _sec(text, level=1, label=None, numbered=True):
    return Section(level=level, children=[Text(text=text)], label=label,
                   numbered=numbered)


def _m(latex):
    return MathInline(latex=latex)


def _eq(latex, label=None):
    return MathBlock(latex=latex, numbered=label is not None, label=label)


def _fn(text):
    return Footnote(children=[Text(text=text)])


def _ref(label, kind="ref"):
    return CrossRef(label=label, kind=kind)


def _cite(*keys, style="cite"):
    return Citation(keys=list(keys), style=style)


def _side(text):
    """Margin note for the Tufte classes (no number)."""
    return InlineRaw(latex=r"\marginnote{" + text + "}")


def _thm(kind, *runs, title="", start=True):
    kids = []
    for r in runs:
        kids.append(Text(text=r) if isinstance(r, str) else r)
    return Theorem(kind=kind, title=title, children=kids, start=start)


def _bib(*entries):
    body = "\n".join(f"\\bibitem{{{k}}} {t}" for k, t in entries)
    return RawLatex(text="\\begin{thebibliography}{99}\n" + body
                         + "\n\\end{thebibliography}")


# ------------------------------------------------------------ memoir

def memoir_book() -> Document:
    """A short non-fiction book (two chapters) in the memoir class."""
    return Document(
        meta=_meta(
            documentclass="memoir", title="The Living Estuary",
            author="Marguerite Aldous", body_font_pt=11,
            line_spacing=1.0, paragraph_indent=True,
            margin_left_cm=3.0, margin_right_cm=3.0,
            packages=DEFAULT_PACKAGES + ["hyperref"],
        ),
        children=[
            Title(children=[Text(text="The Living Estuary")]),
            Author(children=[Text(text="Marguerite Aldous")]),

            _sec("Where the River Gives Up", label="ch:tides"),
            _p("An estuary is a place of argument. Twice a day the sea "
               "pushes inland, and twice a day the river pushes back; "
               "everything that lives between the two has to cope with "
               "water that changes its mind. Walk the mud of the Wenlow "
               "Estuary at low tide and you stand on the floor of a sea "
               "that left an hour ago and will return before supper."),
            _p("This book follows one such estuary through a single year. "
               "It is not a field manual, although it borrows from "
               "several; it is closer to a long walk with a good "
               "companion who stops often to point at things. The first "
               "chapter explains the physical machine, the tide and the "
               "salt gradient it drives. The second looks at the animals "
               "that have made a living inside that machine."),

            _sec("The tidal machine", 2),
            _p("The Wenlow rises on peat moorland and runs forty "
               "kilometres to the sea, but its last twelve kilometres "
               "belong to the tide. At spring tides the water at the "
               "mouth rises and falls by 5.8 metres; at the head of the "
               "estuary, where the channel narrows and the bed shoals, "
               "the range is larger still, an effect known as "
               "funnelling", _fn("Narrowing channels squeeze the tidal "
                                 "wave upward. In the most extreme "
                                 "cases a steep front, a tidal bore, "
                                 "runs upriver ahead of the flood."),
               ". Hydrographers estimate the volume of water that enters "
               "and leaves on each tide with the tidal prism,"),
            _eq(r"P = A_{\mathrm{s}}\, R,", "eq:prism"),
            _p("where ", _m("A_{\\mathrm{s}}"), " is the surface area of "
               "the estuary at mid-tide and ", _m("R"), " is the tidal "
               "range. For the Wenlow, ", _m("A_{\\mathrm{s}} = 14.2"),
               " km", _m("^2"), " and ", _m("R = 4.1"), " m on an "
               "average tide, so Equation ", _ref("eq:prism"),
               " gives a prism of roughly ", _m("5.8\\times10^{7}"),
               " cubic metres. That is about two hundred times the "
               "volume the river alone delivers over the same six "
               "hours, which is why the estuary belongs more to the sea "
               "than to the river that named it."),

            _sec("Salt and mud", 2),
            _p("Salinity falls steadily from the sea to the head of "
               "the estuary, but the transition is never tidy. On a "
               "falling tide, fresher water rides over saltier water "
               "like oil on vinegar; on a spring flood the two mix "
               "violently. Biologists therefore divide an estuary into "
               "zones by the salinity an animal can expect to meet, not "
               "by distance from the sea. Table ", _ref("tab:zones"),
               " gives the zones used throughout this book."),
            Table(
                rows=[["Zone", "Salinity (PSU)", "Distance from mouth (km)"],
                      ["Marine", "30 to 35", "0 to 3"],
                      ["Polyhaline", "18 to 30", "3 to 6"],
                      ["Mesohaline", "5 to 18", "6 to 9"],
                      ["Oligohaline", "0.5 to 5", "9 to 12"],
                      ["Tidal fresh", "below 0.5", "12 to 14"]],
               caption="Salinity zones of the Wenlow Estuary at mean "
                       "river flow.",
               label="tab:zones", alignment="lcc", style="booktabs",
               header=True),
            _p("The mud itself is a product of the same mixing. Fine "
               "clay particles carried by the river clump together when "
               "they meet salt water, sink, and settle in the quiet "
               "water behind the sandbanks. Over centuries this has "
               "built the broad flats that make the estuary so rich "
               "(", _cite("harrow1998"), "). A single square metre of "
               "healthy mud can hold ten thousand small worms and "
               "snails, and these in turn feed most of the estuary's "
               "birds."),

            _sec("Those Who Live in the Mud", label="ch:animals"),
            _p("Life in the estuary is built on a simple bargain: "
               "tolerate the changes, and the food is enormous. Few "
               "species accept the terms. Those that do tend to be "
               "present in huge numbers, and the Wenlow is no exception."),

            _sec("Burrowers and grazers", 2),
            _p("Three animals do most of the work on the mudflats."),
            _items("The ragworm, which burrows in the mesohaline mud "
                   "and surfaces to feed at high tide;",
                   "the mud snail, which grazes the film of algae on "
                   "the surface and leaves tracks visible from the sea "
                   "wall;",
                   "the baltic tellin, a thin pink bivalve that vacuums "
                   "the mud with a long siphon."),
            _p("Their numbers are not constant. Surveys by the Wenlow "
               "Estuary Trust show a marked winter fall, followed by a "
               "spring recovery that tracks the return of the algae "
               "(Table ", _ref("tab:density"), ")."),
            Table(
                rows=[["Species", "February", "May", "August"],
                      ["Ragworm", "2100", "3400", "5200"],
                      ["Mud snail", "800", "2900", "6100"],
                      ["Baltic tellin", "1500", "1900", "2300"]],
                caption="Mean density (animals per square metre) on the "
                        "central flats, 2022 survey.",
                label="tab:density", alignment="lrrr", style="booktabs",
                header=True),

            _sec("The birds that follow the tide", 2),
            _p("Every one of those animals is somebody's lunch. By "
               "October the flats fill with waders: knot, dunlin, "
               "redshank and curlew, each with a bill shaped for a "
               "different depth of mud. A curlew probes ten centimetres "
               "down for ragworm; a dunlin, with a short straight bill, "
               "picks tellins from the top two. They share the flats "
               "without much competition, a division of labour that "
               "ecologists call niche partitioning (",
               _cite("harrow1998", "vance2009"), ")."),
            _p("The birds keep to the tide's timetable and not the "
               "clock's. Each feeds as the flats are uncovered, roosts "
               "on the saltmarsh at high water, and returns when the "
               "mud reappears. A winter day on the estuary therefore "
               "has two long meals and two long rests, offset by about "
               "fifty minutes from the day before."),
            _p("That daily rhythm is fragile. A walker with a dog on "
               "the flats at the wrong moment can send three hundred "
               "birds into the air, and each unplanned flight burns "
               "energy that a wader in January can ill afford",
               _fn("Vance estimated that a single disturbance costs a "
                   "wintering dunlin about four per cent of its daily "
                   "energy intake."), ". The simplest conservation "
               "measure in the estuary turns out to be an honest tide "
               "table pinned to the car park noticeboard."),
            _bib(("harrow1998", "T. Harrow, \\emph{Mud, Salt and "
                  "Sediment}. Fenmouth University Press, 1998."),
                 ("vance2009", "R. Vance and L. Okoro, Disturbance and "
                  "energy budgets of wintering waders. \\emph{Journal of "
                  "Estuarine Birds} \\textbf{14} (2009), 211--226.")),
        ],
    )


# ------------------------------------------------------------ KOMA report

def koma_report() -> Document:
    """A technical annual report in scrreprt."""
    return Document(
        meta=_meta(
            documentclass="scrreprt",
            title="River Calder Catchment: Annual Water Quality Report 2025",
            author="Calder Catchment Partnership",
            body_font_pt=11, line_spacing=1.15,
            margin_left_cm=3.0, margin_right_cm=3.0,
            packages=DEFAULT_PACKAGES + ["hyperref"],
        ),
        children=[
            Title(children=[Text(text="River Calder Catchment: Annual "
                                      "Water Quality Report 2025")]),
            Author(children=[Text(text="Calder Catchment Partnership")]),

            _sec("Summary", numbered=False),
            _p("This report presents the results of the 2025 monitoring "
               "programme on the River Calder and its four main "
               "tributaries. Twenty-four sites were sampled monthly for "
               "nutrients, dissolved oxygen, and faecal indicator "
               "organisms. Overall water quality improved at nineteen "
               "sites compared with 2024. Phosphorus remains the "
               "principal concern: eleven sites exceeded the "
               "0.05 mg/L good-status threshold, mostly downstream of "
               "sewage treatment works."),
            _p("The main findings are:"),
            _items("median total phosphorus fell from 0.071 to "
                   "0.058 mg/L across the catchment;",
                   "dissolved oxygen met the standard at all sites in "
                   "every month except July at Holme Bridge;",
                   "bathing-water classification at Calder Weir "
                   "improved from sufficient to good."),

            _sec("Introduction", label="ch:intro"),
            _sec("Purpose and scope", 2),
            _p("The Calder Catchment Partnership brings together the "
               "water company, three local authorities, farming "
               "groups, and volunteer anglers. Its monitoring "
               "programme gives a shared evidence base for decisions "
               "on investment and enforcement. This report covers the "
               "calendar year 2025 and follows the method of the "
               "2023 and 2024 reports so that results can be compared "
               "directly (", _cite("calder24"), ")."),
            _sec("The catchment", 2),
            _p("The catchment covers 412 km", _m("^2"), " and supports "
               "about 180,000 people. Upland areas to the west are "
               "managed moorland; the middle valley is mixed farming; "
               "the lower reaches pass through the towns of Holme and "
               "Ashby before meeting the estuary at Calder Weir. Mean "
               "annual rainfall is 1150 mm in the uplands and 780 mm "
               "on the coast."),

            _sec("Monitoring Method", label="ch:method"),
            _sec("Sampling", 2),
            _p("Grab samples were taken on the first Tuesday of each "
               "month at 24 fixed sites. Field staff measured "
               "temperature, pH, and dissolved oxygen in situ with "
               "calibrated probes. Water for laboratory analysis was "
               "kept at 4 degrees Celsius and delivered to the "
               "accredited laboratory within 24 hours."),
            _sec("Calculating nutrient load", 2),
            _p("Pollutant loads were estimated from the concentration "
               "of each sample and the daily mean flow recorded at the "
               "nearest gauging station:"),
            _eq(r"L = k \sum_{i=1}^{n} C_i\, Q_i,", "eq:load"),
            _p("where ", _m("C_i"), " is the concentration in mg/L, ",
               _m("Q_i"), " the flow in m", _m("^3"), "/s on the day of "
               "sample ", _m("i"), ", and ", _m("k"), " a conversion "
               "constant to kilograms per year. Equation ",
               _ref("eq:load"), " is applied separately at each site "
               "and averaged over the twelve samples."),

            _sec("Results", label="ch:results"),
            _sec("Nutrients", 2),
            _p("Table ", _ref("tab:phos"), " lists median total "
               "phosphorus and the annual load at six representative "
               "sites, from the headwaters to the tidal limit. "
               "Concentrations rise sharply below the Holme sewage "
               "works and remain high until the river reaches the "
               "estuary."),
            Table(
                rows=[["Site", "Median TP (mg/L)", "Load (kg/yr)",
                       "Status"],
                      ["Upper Calder", "0.021", "310", "Good"],
                      ["Hebble Beck", "0.034", "540", "Good"],
                      ["Holme Bridge", "0.092", "2870", "Moderate"],
                      ["Ashby Mill", "0.081", "3420", "Moderate"],
                      ["Calder Weir", "0.064", "4150", "Moderate"],
                      ["Tidal limit", "0.049", "4390", "Good"]],
                caption="Median total phosphorus (TP) and annual load at "
                        "six sites, 2025.",
                label="tab:phos", alignment="lccl", style="booktabs",
                header=True),
            _sec("Oxygen and bacteria", 2),
            _p("Dissolved oxygen stayed above the 7 mg/L standard "
               "in all months except July, when a warm, low-flow "
               "spell pushed the Holme Bridge site down to 5.8 mg/L. "
               "Faecal indicator counts were within the permitted "
               "range at every site, and the single bathing-water "
               "failure of 2024 did not recur."),

            _sec("Recommendations", label="ch:rec"),
            _p("The Partnership recommends the following actions for "
               "2026, in order of priority."),
            _ord_items("Bring forward the upgrade of the Holme "
                       "sewage works phosphorus removal.",
                       "Extend riparian buffer strips along Hebble "
                       "Beck, working with the eight farms identified "
                       "in the 2025 survey.",
                       "Install a continuous oxygen sensor at Holme "
                       "Bridge to capture summer events that monthly "
                       "sampling cannot.",
                       "Repeat the sampling programme with unchanged "
                       "methods to keep the series comparable."),
            _p("Progress on each action will be reported at the "
               "Partnership's quarterly meetings. Full data tables "
               "are available from the secretariat on request",
               _fn("Contact the secretariat at the address on the "
                   "inside cover."), "."),
            _bib(("calder24", "Calder Catchment Partnership, "
                  "\\emph{Annual Water Quality Report 2024}. Holme, "
                  "2025.")),
        ],
    )


# ------------------------------------------------------------ KOMA book

def koma_book() -> Document:
    """A teaching book (two chapters) in scrbook."""
    return Document(
        meta=_meta(
            documentclass="scrbook",
            title="Practical Statistics for Field Biologists",
            author="Ines Kowalczyk", body_font_pt=11, line_spacing=1.15,
            paragraph_indent=False,
            margin_left_cm=3.0, margin_right_cm=3.0,
            packages=DEFAULT_PACKAGES + ["hyperref"],
        ),
        children=[
            Title(children=[Text(text="Practical Statistics for Field "
                                      "Biologists")]),
            Author(children=[Text(text="Ines Kowalczyk")]),

            _sec("Describing Your Data", label="ch:describe"),
            _p("Every field season ends with a spreadsheet. Before you "
               "run a single test, you need to know what is in it. This "
               "chapter shows how to summarise a sample honestly, with "
               "a handful of numbers and one good picture."),
            _sec("Centre and spread", 2),
            _p("Suppose you measured the wing length of ", _m("n = 8"),
               " blue tits caught at one ringing site, in millimetres: "
               "64, 66, 63, 67, 65, 64, 68, 63. The most common summary "
               "of centre is the sample mean,"),
            _eq(r"\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i,", "eq:mean"),
            _p("which here is ", _m("\\bar{x} = 65.0"), " mm. The mean "
               "alone says nothing about how scattered the birds are. "
               "For that we use the sample standard deviation,"),
            _eq(r"s = \sqrt{\frac{1}{n-1}\sum_{i=1}^{n}"
                r"\left(x_i - \bar{x}\right)^2},", "eq:sd"),
            _p("which is ", _m("s = 1.85"), " mm for these data. Note "
               "the divisor ", _m("n-1"), " in Equation ", _ref("eq:sd"),
               ": a sample sits closer to its own mean than to the "
               "true population mean, so dividing by ", _m("n"),
               " would understate the spread", _fn("This is Bessel's "
               "correction. For samples above about thirty the "
               "difference is under two per cent."), "."),
            _sec("Choosing a summary", 2),
            _p("Means and standard deviations suit roughly symmetric "
               "data. When a few extreme values dominate, as with "
               "counts of parasites per host, use the median and the "
               "interquartile range instead. Table ", _ref("tab:sum"),
               " collects the usual pairs."),
            Table(
                rows=[["Data shape", "Centre", "Spread"],
                      ["Symmetric, no outliers", "Mean", "Standard "
                       "deviation"],
                      ["Skewed or with outliers", "Median", "Interquartile "
                       "range"],
                      ["Counts with many zeros", "Median", "Range"],
                      ["Proportions", "Percentage", "Binomial interval"]],
                caption="Which summary to report for which kind of data.",
                label="tab:sum", alignment="lll", style="booktabs",
                header=True),
            _p("Whichever summary you choose, plot the raw data as "
               "well. A dot for every animal costs nothing and "
               "protects you from errors that no summary statistic can "
               "reveal."),

            _sec("Comparing Two Groups", label="ch:compare"),
            _p("The commonest question in field biology is whether "
               "two sets of animals differ. Do birds in nest boxes "
               "fledge more chicks than birds in natural cavities? "
               "Does the beetle count differ between grazed and "
               "ungrazed plots?"),
            _sec("The two-sample t statistic", 2),
            _p("Given two independent samples with means ",
               _m("\\bar{x}_1"), " and ", _m("\\bar{x}_2"),
               ", standard deviations ", _m("s_1"), " and ", _m("s_2"),
               ", and sizes ", _m("n_1"), " and ", _m("n_2"),
               ", Welch's statistic is"),
            _eq(r"t = \frac{\bar{x}_1 - \bar{x}_2}"
                r"{\sqrt{s_1^2/n_1 + s_2^2/n_2}}.", "eq:welch"),
            _p("A large absolute value of ", _m("t"), " means the "
               "difference between the means is large compared with "
               "its own uncertainty (", _cite("zar99"), "). Welch's "
               "form does not assume equal variances, so it is safe "
               "to use by default."),
            _sec("A worked example", 2),
            _p("Twenty nest boxes and twenty natural cavities were "
               "checked in a single season. The fledging results are "
               "in Table ", _ref("tab:fledge"), ". Applying Equation ",
               _ref("eq:welch"), " gives ", _m("t = 2.93"),
               " on about 36 degrees of freedom, corresponding to "
               "a two-sided ", _m("p = 0.006"), "."),
            Table(
                rows=[["Site type", "n", "Mean fledglings", "SD"],
                      ["Nest box", "20", "6.4", "1.9"],
                      ["Natural cavity", "20", "4.9", "1.7"]],
                caption="Chicks fledged per nest in two nest types.",
                label="tab:fledge", alignment="lrrr", style="booktabs",
                header=True),
            _p("The sensible reading is that nest boxes raised "
               "fledging success by about 1.5 chicks per nest. Report "
               "that difference and its confidence interval first; "
               "the ", _m("p"), "-value is a supporting detail."),
            _p("Three habits keep this kind of analysis honest."),
            _ord_items("Decide on the comparison before you look at "
                       "the data.",
                       "Report every comparison you made, not only the "
                       "significant ones.",
                       "Share the raw data alongside the paper."),
            _bib(("zar99", "J. Zar, \\emph{Biostatistical Analysis}, "
                  "4th ed. Marlowe Press, 1999.")),
        ],
    )


# ------------------------------------------------------------ Tufte handout

def tufte_handout() -> Document:
    """A study handout in the Tufte style, with sidenotes in the margin."""
    return Document(
        meta=_meta(
            documentclass="tufte-handout",
            title="Waves on a String",
            author="Dr. Oliver Penhale",
            body_font_pt=10, line_spacing=1.0,
            packages=DEFAULT_PACKAGES,
        ),
        children=[
            Title(children=[Text(text="Waves on a String")]),
            Author(children=[Text(text="Dr. Oliver Penhale")]),

            _p("This handout accompanies the second lecture on "
               "vibrations. It covers the wave equation for a "
               "stretched string and the normal modes that explain how "
               "a guitar string produces a note.",
               _side("Margin notes in this handout carry asides, "
                     "units, and references, so the main text can "
                     "stay on the argument.")),

            _sec("The wave equation"),
            _p("Take a string of length ", _m("L"), " under tension ",
               _m("T"), " with mass per unit length ", _m("\\mu"),
               ". Displace it slightly from rest, and write ",
               _m("y(x,t)"), " for the transverse displacement at "
               "position ", _m("x"), " and time ", _m("t"),
               ". Applying Newton's second law to a short segment "
               "gives", _fn("The small-angle approximation is used "
                            "throughout: slopes are assumed much "
                            "smaller than one, so the tension is the "
                            "same everywhere along the string.")),
            _eq(r"\frac{\partial^2 y}{\partial t^2} = v^2\,"
                r"\frac{\partial^2 y}{\partial x^2}, \qquad "
                r"v = \sqrt{T/\mu},", "eq:wave"),
            _p("where ", _m("v"), " is the speed of waves on the "
               "string.", _side("For a steel guitar string with "
                                "$T = 80$ N and $\\mu = 0.0006$ kg/m, "
                                "$v$ is about 365 m/s.")),

            _sec("Normal modes"),
            _p("A string fixed at both ends can only vibrate in "
               "patterns that fit a whole number of half-wavelengths "
               "between the supports. Each pattern is a normal mode, "
               "with displacement"),
            _eq(r"y_n(x,t) = A_n \sin\!\left(\frac{n\pi x}{L}\right)"
                r"\cos(\omega_n t + \varphi_n),", "eq:mode"),
            _p("and angular frequency ", _m("\\omega_n = n\\pi v/L"),
               " for ", _m("n = 1, 2, 3, \\dots"), " The lowest mode "
               "(", _m("n=1"), ") is the fundamental; the others are "
               "harmonics.", _side("The frequency in hertz is "
                                   "$f_n = \\omega_n/2\\pi$, so "
                                   "$f_1 = v/2L$.")),
            _p("Using the numbers from the margin, a 0.65 m string has "
               "a fundamental of about 281 Hz, close to the note C",
               _m("_4"), ". Table ", _ref("tab:harm"), " lists the "
               "first four harmonics."),
            Table(
                rows=[["Mode n", "Frequency (Hz)", "Nodes"],
                      ["1", "281", "0"],
                      ["2", "562", "1"],
                      ["3", "843", "2"],
                      ["4", "1124", "3"]],
                caption="Harmonics of a 0.65 m string with v = 365 m/s.",
                label="tab:harm", alignment="ccc", style="booktabs",
                header=True),

            _sec("Why plucking position matters"),
            _p("A string plucked at its midpoint contains only odd "
               "harmonics, since the even modes have a node there and "
               "cannot be excited. Plucking near the bridge instead "
               "excites many harmonics with large amplitude, and the "
               "sound becomes brighter and thinner. Guitarists use "
               "this deliberately.",
               _side("Try it: pluck an open string above the "
                     "twelfth fret, then close to the bridge, and "
                     "listen.")),

            _sec("Exercises"),
            _ord_items("Show that Equation 1 is satisfied by each "
                       "mode in Equation 2 when the frequency is "
                       "as stated.",
                       "A violin string has L = 0.325 m and a "
                       "fundamental of 440 Hz. Find the wave speed.",
                       "Which harmonics are missing when a string is "
                       "plucked one third of the way along?"),
        ],
    )


# ------------------------------------------------------------ Tufte book

def tufte_book() -> Document:
    """A chapter-based book in Tufte style, with sidenotes and margin
    notes."""
    return Document(
        meta=_meta(
            documentclass="tufte-book",
            title="Reading the Weather",
            author="Fiona Maclaren",
            body_font_pt=10, line_spacing=1.0,
            packages=DEFAULT_PACKAGES,
        ),
        children=[
            Title(children=[Text(text="Reading the Weather")]),
            Author(children=[Text(text="Fiona Maclaren")]),

            _sec("The Barometer and the Sky", label="ch:baro"),
            _p("Long before satellites, sailors read the weather from "
               "two things: the height of the mercury and the shape of "
               "the clouds. Both still work. This chapter explains why, "
               "and how to combine them into a forecast you can "
               "trust for the next six hours.",
               _side("All pressures in this book are in hectopascals "
                     "(hPa). Standard sea-level pressure is "
                     "1013.25 hPa.")),

            _sec("What a barometer measures", 2),
            _p("A barometer measures the weight of the air above it. "
               "Pressure falls with height roughly exponentially, "
               "following the barometric formula"),
            _eq(r"p(h) = p_0\, e^{-h/H}, \qquad H \approx 8.4\ "
                r"\mathrm{km},", "eq:baro"),
            _p("where ", _m("p_0"), " is the pressure at sea level and ",
               _m("H"), " is the scale height", _fn("The scale height "
               "depends on temperature, so the real atmosphere is a "
               "little more complicated; 8.4 km suits typical mid-"
               "latitude conditions."), ". At the summit of a 1344 m "
               "hill Equation ", _ref("eq:baro"), " predicts a pressure "
               "about 15 per cent lower than at the foot."),
            _p("What matters for forecasting is not the absolute "
               "reading but its change. Meteorologists call this the "
               "pressure tendency, and Table ", _ref("tab:tend"),
               " gives the standard rules of thumb.",
               _side("Always correct the reading to sea level before "
                     "you compare it with a published chart.")),
            Table(
                rows=[["Tendency in 3 hours", "Likely weather"],
                      ["Rising by more than 6 hPa", "Clearing, then "
                       "windy"],
                      ["Rising slowly", "Settled, fair"],
                      ["Steady", "No change"],
                      ["Falling slowly", "Cloud and light rain later"],
                      ["Falling by more than 6 hPa", "Gale or heavy "
                       "rain within hours"]],
                caption="Pressure tendency and the weather that "
                        "usually follows.",
                label="tab:tend", alignment="ll", style="booktabs",
                header=True),

            _sec("Reading the clouds", 2),
            _p("High, thin clouds that arrive from the west often "
               "precede a warm front by a day. They thicken, lower, "
               "and darken as rain approaches. By contrast, towering "
               "cumulus that builds in the afternoon on a hot day "
               "warns of a shower, not a change of air mass.",
               _side("Mackerel sky and mares' tails: the old rhyme "
                     "says that they make tall ships carry low "
                     "sails.")),

            _sec("Wind and the Rule of Buys Ballot", label="ch:wind"),
            _p("Wind is air moving from high pressure to low, but the "
               "spin of the Earth bends its path. In the northern "
               "hemisphere the result is simple to state: stand with "
               "your back to the wind and low pressure is on your "
               "left. This rule, named after a Dutch meteorologist, "
               "lets you locate a depression from a single wind "
               "observation."),
            _sec("The strength of the wind", 2),
            _p("Wind speed follows the pressure gradient. Closely "
               "spaced isobars, as shown on any chart, mean strong "
               "wind. The balance between the pressure-gradient and "
               "Coriolis forces gives the geostrophic wind,"),
            _eq(r"v_g = \frac{1}{\rho f}\,\frac{\Delta p}{\Delta n},",
                "eq:geo"),
            _p("where ", _m("\\rho"), " is air density, ", _m("f"),
               " the Coriolis parameter, and ", _m("\\Delta p/\\Delta n"),
               " the pressure change across a distance ", _m("\\Delta n"),
               " perpendicular to the isobars. At 55 degrees north, a "
               "gradient of 4 hPa over 100 km gives a geostrophic wind "
               "of about 27 m/s in Equation ", _ref("eq:geo"),
               ", which is the strong gale of Beaufort force 10.",
               _side("1 m/s is about 1.94 knots. Force 10 spans "
                     "24.5 to 28.4 m/s.")),
            _p("Near the surface, friction slows the wind and turns "
               "it a little towards low pressure, so real winds blow "
               "across the isobars at around 20 degrees over the sea "
               "and 35 degrees over land."),
        ],
    )


# ------------------------------------------------------------ AMS book

def ams_book() -> Document:
    """A mathematics monograph chapter in amsbook."""
    return Document(
        meta=_meta(
            documentclass="amsbook", title="Topics in Metric Spaces",
            author="Helena Brandt", body_font_pt=11, line_spacing=1.1,
            paragraph_indent=True,
            packages=DEFAULT_PACKAGES + ["amsthm"],
        ),
        children=[
            Title(children=[Text(text="Topics in Metric Spaces")]),
            Author(children=[Text(text="Helena Brandt")]),

            _sec("Complete Metric Spaces", label="ch:complete"),
            _p("This chapter develops the theory of complete metric "
               "spaces up to the Banach fixed point theorem and one "
               "of its standard applications. We assume the reader is "
               "familiar with sequences of real numbers and with the "
               "definition of a metric space."),

            _sec("Cauchy sequences", 2, label="sec:cauchy"),
            _p("Let ", _m("(X,d)"), " be a metric space."),
            _thm("definition", "A sequence ", _m("(x_n)"), " in ",
                 _m("X"), " is a ", "Cauchy "
                 "sequence if for every ", _m("\\varepsilon > 0"),
                 " there is an ", _m("N"), " such that ",
                 _m("d(x_m, x_n) < \\varepsilon"), " whenever ",
                 _m("m,n \\ge N"), "."),
            _p("Every convergent sequence is Cauchy, but the converse "
               "can fail: the sequence ", _m("x_n = 1/n"), " is Cauchy "
               "in the open interval ", _m("(0,1)"), " yet has no "
               "limit there. This motivates the following notion."),
            _thm("definition", "A metric space is ", "complete",
                 " if every Cauchy sequence in it converges to a "
                 "point of the space."),
            _thm("example", "The real line ", _m("\\mathbb{R}"),
                 " with ", _m("d(x,y) = |x-y|"), " is complete. The "
                 "rationals ", _m("\\mathbb{Q}"), " with the same "
                 "metric are not: a sequence of rationals converging "
                 "to ", _m("\\sqrt{2}"), " is Cauchy but has no limit "
                 "in ", _m("\\mathbb{Q}"), "."),
            _thm("proposition", "A closed subset of a complete metric "
                 "space is complete.", title="Closed subsets"),
            _thm("proof", "Let ", _m("F \\subseteq X"), " be closed "
                 "and let ", _m("(x_n)"), " be Cauchy in ", _m("F"),
                 ". It is Cauchy in ", _m("X"), ", so it converges to "
                 "some ", _m("x \\in X"), ". Since ", _m("F"),
                 " is closed, ", _m("x \\in F"), "."),

            _sec("The contraction principle", 2, label="sec:banach"),
            _thm("definition", "A map ", _m("T : X \\to X"), " is a ",
                 "contraction if there is a constant ",
                 _m("0 \\le q < 1"), " with"),
            _eq(r"d(Tx, Ty) \le q\, d(x,y) \quad \text{for all } "
                r"x,y \in X.", "eq:contract"),
            _thm("theorem", "Let ", _m("(X,d)"), " be a non-empty "
                 "complete metric space and ", _m("T"), " a "
                 "contraction on ", _m("X"), " with constant ",
                 _m("q"), ". Then ", _m("T"), " has exactly one fixed "
                 "point ", _m("x^*"), ", and for any ", _m("x_0 \\in X"),
                 " the iterates ", _m("x_{n+1} = T x_n"),
                 " converge to ", _m("x^*"), " with",
                 title="Banach fixed point theorem"),
            _eq(r"d(x_n, x^*) \le \frac{q^n}{1-q}\, d(x_1, x_0).",
                "eq:rate"),
            _thm("proof", "Put ", _m("x_{n+1} = Tx_n"), ". By "
                 "Equation ", _ref("eq:contract", "eqref"), ", ",
                 _m("d(x_{n+1}, x_n) \\le q^n d(x_1, x_0)"),
                 ". For ", _m("m > n"), " the triangle inequality and "
                 "the geometric series give ",
                 _m("d(x_m, x_n) \\le q^n d(x_1,x_0)/(1-q)"),
                 ", so ", _m("(x_n)"), " is Cauchy and converges to "
                 "some ", _m("x^*"), " by completeness. Contractions "
                 "are continuous, so ", _m("Tx^* = x^*"),
                 ". If ", _m("y^*"), " is another fixed point then ",
                 _m("d(x^*,y^*) \\le q\\, d(x^*,y^*)"), ", which forces ",
                 _m("d(x^*,y^*) = 0"), ". Letting ", _m("m\\to\\infty"),
                 " in the estimate for ", _m("d(x_m,x_n)"),
                 " gives Equation ", _ref("eq:rate", "eqref"), "."),
            _thm("remark", "The bound in Equation ", _ref("eq:rate",
                 "eqref"), " is useful in practice: it tells how many "
                 "iterations guarantee a given accuracy before the "
                 "computation starts (", _cite("rudin76"), ")."),

            _sec("An application", 2, label="sec:ode"),
            _p("The contraction principle proves the existence and "
               "uniqueness of solutions to ordinary differential "
               "equations. Consider the initial value problem ",
               _m("y' = f(t,y)"), ", ", _m("y(t_0) = y_0"),
               ", where ", _m("f"), " is continuous and Lipschitz in ",
               _m("y"), " with constant ", _m("K"), "."),
            _thm("theorem", "There is ", _m("\\delta > 0"), " such "
                 "that the problem has a unique solution on ",
                 _m("[t_0 - \\delta, t_0 + \\delta]"), ".",
                 title="Picard-Lindel\u00f6f"),
            _p("The problem is equivalent to the fixed point equation ",
               _m("y = Ty"), ", where"),
            _eq(r"(Ty)(t) = y_0 + \int_{t_0}^{t} f(s, y(s))\, ds.",
                "eq:picard"),
            _thm("proof", "On the complete space of continuous "
                 "functions on ", _m("[t_0-\\delta, t_0+\\delta]"),
                 " with the supremum metric, the map ", _m("T"),
                 " in Equation ", _ref("eq:picard", "eqref"),
                 " is a contraction with constant ", _m("K\\delta"),
                 ", provided ", _m("\\delta < 1/K"),
                 ". The Banach fixed point theorem now applies."),
            _bib(("rudin76", "W. Rudin, \\emph{Principles of "
                  "Mathematical Analysis}, 3rd ed. Fictional Press, "
                  "1976.")),
        ],
    )
