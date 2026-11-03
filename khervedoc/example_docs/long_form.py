"""Book chapter, thesis, posters, white paper, slides and a standalone figure."""
from __future__ import annotations

from ..model import (
    Abstract, Affiliation, Author, Citation, CrossRef, DEFAULT_PACKAGES, Document,
    Footnote, Frame, InlineRaw, List as ListNode, ListItem, Keywords, MathBlock, MathInline, Paragraph, RawLatex,
    Section, Table, Text, Theorem, Title,
)
from ..example_helpers import _items, _meta, _ord_items, _p


def _sec(text: str, level: int = 1, label: str | None = None) -> Section:
    return Section(level=level, children=[Text(text=text)], label=label)


def _m(latex: str) -> MathInline:
    return MathInline(latex=latex)


def _li(*items) -> ListNode:
    """Bullet list whose items are lists of inline runs."""
    return ListNode(ordered=False, items=[
        ListItem(children=[Text(text=r) if isinstance(r, str) else r
                           for r in it]) for it in items])


def _bib(*entries: tuple[str, str]) -> RawLatex:
    body = "\n".join(f"\\bibitem{{{k}}} {t}" for k, t in entries)
    return RawLatex(text="\\begin{thebibliography}{99}\n" + body
                         + "\n\\end{thebibliography}")


# ------------------------------------------------------------ standalone

def standalone_figure() -> Document:
    """One self-contained TikZ figure on a page cropped to its content."""
    return Document(
        meta=_meta(
            documentclass="standalone",
            title="", author="",
            body_font_pt=11,
            packages=DEFAULT_PACKAGES + ["tikz"],
            preamble_extras=(
                "\\usetikzlibrary{arrows.meta,decorations.pathmorphing,"
                "calc,positioning}"
            ),
        ),
        children=[
            RawLatex(text=r"""\begin{tikzpicture}[
    >=Stealth, font=\small,
    level/.style={very thick},
    lab/.style={font=\small\itshape}]
  % Energy axis
  \draw[->, thick] (-0.4,-0.6) -- (-0.4,6.2) node[above] {$E$};

  % Sample (left): valence band filled up to the Fermi level, core level below
  \fill[blue!12] (0,1.4) rectangle (4,2.4);
  \draw[level] (0,2.4) -- (4,2.4);
  \node[right] at (4.1,2.4) {$E_\mathrm{F}$};
  \node[lab] at (2,1.9) {valence band};
  \draw[level] (0.6,-0.2) -- (3.4,-0.2);
  \node[right] at (4.1,-0.2) {core level};

  % Vacuum level
  \draw[level, dashed] (0,5.0) -- (7.8,5.0);
  \node[right] at (7.9,5.0) {$E_\mathrm{vac}$};

  % Photon
  \draw[->, thick, red!70!black, decorate,
        decoration={snake, amplitude=1.2pt, segment length=6pt}]
        (-2.6,3.7) -- (1.6,0.0) node[pos=0.15, above=2pt, sloped] {$h\nu$};

  % Photoelectron
  \draw[->, very thick, green!45!black] (1.9,-0.1) -- (1.9,5.0)
        -- (1.9,5.9) node[above] {$e^-$};
  \fill[green!45!black] (1.9,-0.2) circle (2.4pt);

  % Energy bookkeeping
  \draw[<->] (5.6,2.4) -- (5.6,5.0)
        node[midway, right=2pt] {$\phi$};
  \draw[<->] (5.6,-0.2) -- (5.6,2.4)
        node[midway, right=2pt] {$E_\mathrm{B}$};
  \draw[dotted] (4,2.4) -- (5.6,2.4);
  \draw[dotted] (3.4,-0.2) -- (5.6,-0.2);
  \draw[<->] (6.9,5.0) -- (6.9,5.9);
  \draw[dotted] (1.9,5.9) -- (6.9,5.9);
  \node[right, align=left] at (7.0,5.45) {$E_\mathrm{K}$};

  % Result
  \node[draw, rounded corners, fill=yellow!15, inner sep=5pt]
        at (4.6,-1.6) {$E_\mathrm{K} = h\nu - E_\mathrm{B} - \phi$};
\end{tikzpicture}"""),
        ],
    )


# ------------------------------------------------------- tikzposter

_BLOCK_PASSTHROUGH = (
    # The serializer wraps the body of a tikzposter in one untitled
    # \block; let that wrapper vanish so the real blocks and columns
    # written below sit directly on the canvas.
    "\\AtBeginDocument{\\let\\ktorigblock\\block\n"
    "\\renewcommand{\\block}[2]{\\ifx\\relax#1\\relax #2\\else"
    "\\ktorigblock{#1}{#2}\\fi}}"
)


def _blk(title: str) -> RawLatex:
    return RawLatex(text=f"\\block{{{title}}}{{")


def _end() -> RawLatex:
    return RawLatex(text="}")


def poster() -> Document:
    """Conference poster in the tikzposter class (A0 portrait canvas)."""
    return Document(
        meta=_meta(
            documentclass="tikzposter",
            class_options="a1paper,portrait,25pt",
            title="", author="",
            body_font_pt=12,
            packages=DEFAULT_PACKAGES + ["booktabs", "hyperref", "tikz"],
            preamble_extras=(
                "\\usetheme{Default}\n"
                "\\usecolorstyle[colorOne=blue!55!black,colorTwo=blue!20,"
                "colorThree=orange!80!black]{Default}\n"
                "\\colorlet{backgroundcolor}{blue!4}\n"
                "\\institute{Department of Statistics, University of "
                "Somewhere}\n" + _BLOCK_PASSTHROUGH
            ),
        ),
        children=[
            Title(children=[Text(text="Adaptive mass matrices for HMC")]),
            Author(children=[Text(text="A. Researcher, B. Supervisor and "
                                       "C. Collaborator")]),
            RawLatex(text="\\begin{columns}\n\\column{0.5}"),
            _blk("Motivation"),
            _p("Bayesian inference in high-dimensional parameter spaces "
               "is slow because posteriors are strongly correlated: "
               "standard Markov chain Monte Carlo mixes poorly and "
               "tuning it by hand does not scale."),
            _items("Hamiltonian Monte Carlo (HMC) follows the geometry "
                   "of the posterior but needs a good mass matrix.",
                   "The No-U-Turn Sampler (NUTS) tunes the step size "
                   "only, and keeps an identity or diagonal mass matrix.",
                   "We adapt a full mass matrix online, at almost no "
                   "extra cost per iteration."),
            _end(),
            _blk("Method"),
            _p("Augment the target density ", _m(r"\pi(\theta)"),
               " with momenta ", _m(r"p \sim \mathcal{N}(0, M)"),
               " and simulate the Hamiltonian"),
            MathBlock(latex=r"H(\theta, p) = -\log \pi(\theta) + "
                            r"\tfrac{1}{2}\, p^\top M^{-1} p .",
                      numbered=True, label="eq:hamiltonian"),
            _p("Every ", _m("K"), " leapfrog steps the matrix ", _m("M"),
               " is refreshed by a rank-one update from the covariance "
               "of the last ", _m("W"), " accepted states, so ", _m("M"),
               " converges to the posterior precision and the dynamics "
               "of Equation ", CrossRef(label="eq:hamiltonian",
                                        kind="eqref"),
               " become isotropic."),
            _end(),
            _blk("Algorithm"),
            _ord_items("Warm up for 500 iterations with M = I and "
                       "dual-averaging step size.",
                       "Run K = 25 leapfrog steps per proposal and "
                       "accept or reject.",
                       "Every 100 iterations, update M from the "
                       "last W = 1000 accepted states.",
                       "Freeze the adaptation after 5000 iterations "
                       "and sample."),
            _end(),
            RawLatex(text="\\column{0.5}"),
            _blk("Results"),
            _p("Effective sample size per second, median of 20 runs "
               "in the table below:"),
            Table(
                rows=[
                    ["Problem (dimension)", "NUTS", "Ours", "Speed-up"],
                    ["Logistic regression (50)", "420", "2100", "5.0x"],
                    ["Gaussian process (200)", "38", "540", "14.2x"],
                    ["Hierarchical model (500)", "12", "240", "20.0x"],
                ],
                caption="Effective samples per second on three "
                        "benchmarks.",
                label="tab:poster-results", alignment="lrrr",
                style="grid",
            ),
            RawLatex(text=r"""\begin{center}
\begin{tikzpicture}[x=2.2cm,y=0.2cm]
  \foreach \v/\x/\n in {5.0/1/50, 14.2/2.4/200, 20.0/3.8/500}{
    \fill[blue!55!black] (\x,0) rectangle ++(0.9,\v);
    \node[below] at (\x+0.45,0) {\n};
    \node[above] at (\x+0.45,\v) {\v$\times$};
  }
  \draw[->] (0.6,0) -- (5.2,0) node[right] {\small dimension};
  \draw[->] (0.6,0) -- (0.6,26) node[above] {\small speed-up};
\end{tikzpicture}
\end{center}"""),
            _p("The gains grow with dimension because the adapted mass "
               "matrix de-correlates the geometry for the leapfrog "
               "integrator."),
            _end(),
            _blk("Guarantee"),
            _p("The adaptive chain keeps the correct stationary "
               "distribution when the adaptation vanishes:"),
            MathBlock(latex=r"\sum_{k=1}^{\infty} \|M_{k+1}-M_k\|_F "
                            r"< \infty .",
                      numbered=True, label="eq:diminishing"),
            _p("Our rank-one schedule satisfies this by construction, "
               "since the covariance estimate converges almost surely."),
            _end(),
            RawLatex(text="\\end{columns}"),
            _blk("Conclusions"),
            _items("Online mass-matrix adaptation improves HMC "
                   "efficiency by 5 to 20 times in high dimensions.",
                   "It is a drop-in replacement for NUTS in "
                   "probabilistic programming frameworks.",
                   "Code: github.com/aresearcher/adaptive-hmc"),
            _end(),
        ],
    )


# --------------------------------------------------------- a0poster

_TI3 = _m(r"\mathrm{Ti}^{3+}")


def a0_poster() -> Document:
    """Conference poster in the classic a0poster class: A0 portrait,
    three columns of sectioned text, a table and equations."""
    return Document(
        meta=_meta(
            documentclass="a0poster",
            class_options="a0,portrait",
            title="", author="",
            body_font_pt=12,
            column_count=1,
            margin_left_cm=3.0, margin_right_cm=3.0,
            margin_top_cm=3.0, margin_bottom_cm=3.0,
            paragraph_indent=False,
            packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"],
            preamble_extras=(
                "\\setlength{\\columnsep}{2cm}\n\\setlength{\\tabcolsep}{14pt}\n"
                "\\makeatletter\n"
                "\\renewcommand\\section{\\@startsection{section}{1}{0pt}"
                "{-1ex}{0.6ex}{\\normalfont\\VeryHuge\\bfseries}}\n"
                "\\makeatother"),
        ),
        children=[
            RawLatex(text=(
                "\\begin{center}\n"
                "{\\VeryHuge\\bfseries Oxygen vacancies control the "
                "photocurrent\\\\ of anatase TiO$_2$ thin films}\\\\[1.2cm]\n"
                "{\\Huge A. Surface, B. Vacuum and C. Synchrotron}\\\\[0.5cm]\n"
                "{\\huge Department of Materials, University of "
                "Somewhere}\n"
                "\\end{center}\n\\vspace{1cm}\\hrule\\vspace{1cm}")),
            RawLatex(text="\\begin{multicols}{2}\n\\veryHuge\\raggedright"),
            _sec("Why it matters"),
            _p("Anatase ", _m(r"\mathrm{TiO_2}"), " is the benchmark "
               "photoanode, yet its photocurrent varies by a factor of "
               "three between nominally identical films. We test "
               "whether the spread comes from oxygen vacancies, which "
               "create ", _TI3, " states below the conduction band."),
            _sec("Methods"),
            _li(["40 nm films grown by atomic layer deposition on FTO "
                 "glass."],
                ["Vacuum anneal for 1 h at 300, 500 or 700 \u00b0C."],
                ["Ti 2p XPS with monochromated Al ",
                 _m(r"\mathrm{K}\alpha"), " radiation to quantify the ",
                 _TI3, " fraction."],
                ["Photocurrent at 1.23 V vs RHE under AM1.5G "
                 "illumination (", _m(r"100\ \mathrm{mW\,cm^{-2}}"),
                 ")."]),
            _p("The ", _TI3, " fraction ", _m("f"), " follows an "
               "Arrhenius law in the annealing temperature ", _m("T"),
               ":"),
            MathBlock(latex=r"f(T) = f_0 \exp\!\left(-\frac{E_a}{k_B T}"
                            r"\right),",
                      numbered=True, label="eq:arrhenius"),
            _p("while the photocurrent density saturates once the "
               "vacancies start to act as recombination centres."),
            _sec("Results"),
            RawLatex(text=(
                "\\begin{center}\n"
                "\\begin{tabular}{rrr}\\toprule\n"
                "$T$ ($^\\circ$C) & Ti$^{3+}$ (\\%) & "
                "$J$ (mA\\,cm$^{-2}$) \\\\ \\midrule\n"
                "as grown & 2 & 0.31 \\\\\n300 & 4 & 0.52 \\\\\n"
                "500 & 9 & 0.88 \\\\\n700 & 14 & 0.61 \\\\ "
                "\\bottomrule\n\\end{tabular}\\\\[0.5cm]\n"
                "\\emph{Ti$^{3+}$ fraction and photocurrent density of "
                "the four films.}\n\\end{center}")),
            _p("The photocurrent peaks at ",
               _m(r"0.88\ \mathrm{mA\,cm^{-2}}"), " with 9 % ", _TI3,
               ": a few vacancies raise the conductivity, many trap "
               "carriers. Fitting Equation ",
               CrossRef(label="eq:arrhenius", kind="eqref"),
               " to the three annealed films gives ",
               _m(r"E_a = 0.62 \pm 0.05\ \mathrm{eV}"), "."),
            _sec("Conclusions"),
            _li(["Vacancy doping to about 9 % ", _TI3, " raises the "
                 "photocurrent 2.8-fold."],
                ["Annealing above 600 \u00b0C is counter-productive."],
                ["XPS is a fast quality check for photoanodes."]),
            _sec("Contact"),
            _p("a.surface@somewhere.example"),
            RawLatex(text="\\end{multicols}"),
        ],
    )


# ------------------------------------------------------------- beamer

def beamer_slides() -> Document:
    """A ten-minute conference talk in beamer: one idea per frame."""
    return Document(
        meta=_meta(
            documentclass="beamer",
            class_options="aspectratio=169",
            title="Faster builds with a shared cache",
            author="A. Speaker",
            body_font_pt=12,
            packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"],
            preamble_extras=(
                "\\usetheme{Madrid}\n"
                "\\usecolortheme{default}\n"
                "\\setbeamertemplate{navigation symbols}{}\n"
                "\\institute[Somewhere]{Developer Productivity Team, "
                "Somewhere Software}\n"
                "\\date{Engineering Summit 2026}"
            ),
        ),
        children=[
            Title(children=[Text(text="Faster builds with a shared cache")]),
            Author(children=[Text(text="A. Speaker")]),

            Frame(children=[Text(text="Outline")]),
            RawLatex(text="\\tableofcontents"),

            Section(level=1, children=[Text(text="The problem")]),

            Frame(children=[Text(text="Builds got slower, not our code")]),
            _items(
                "Median CI build: 8 min in 2024, 35 min today.",
                "Module count grew from 120 to 380.",
                "Cache hit rate on CI: below 40 %.",
            ),
            RawLatex(text="\\begin{alertblock}{Why it hurts}\n"
                          "Slow builds push people to batch changes "
                          "into big, risky pull requests.\n"
                          "\\end{alertblock}"),

            Frame(children=[Text(text="Where the time goes")]),
            Table(
                rows=[
                    ["Stage", "Minutes", "Share"],
                    ["Dependency resolution", "6", "17\\%"],
                    ["Compilation", "17", "49\\%"],
                    ["Tests", "12", "34\\%"],
                ],
                caption="Median time per stage, 35 min in total.",
                label="tab:stages", alignment="lrr", style="booktabs",
                header=True,
            ),

            Section(level=1, children=[Text(text="The idea")]),

            Frame(children=[Text(text="Key the cache on inputs, not machines")]),
            _p("A task output is stored under the hash of everything "
               "that can change it:"),
            MathBlock(latex=r"k = H\bigl(\text{sources},\ "
                            r"\text{toolchain},\ \text{flags}\bigr)",
                      numbered=False),
            _items(
                "Same key on any machine: the result is reused.",
                "Different JDK patch level: a different key, never a "
                "wrong result.",
            ),

            Frame(children=[Text(text="What to expect")]),
            _p("If a fraction ", _m("h"), " of tasks hit the cache, the "
               "build time falls to"),
            MathBlock(latex=r"T(h) = (1-h)\,T_0 + h\,\tau",
                      numbered=False),
            _p("with ", _m("T_0 = 35"), " min and ", _m(r"\tau"),
               " the cost of fetching cached outputs."),

            Section(level=1, children=[Text(text="Results")]),

            Frame(children=[Text(text="Pilot on two repositories")]),
            Table(
                rows=[
                    ["", "Before", "After"],
                    ["Cache hit rate", "38\\%", "87\\%"],
                    ["Median build", "21 min", "8.4 min"],
                    ["P95 build", "34 min", "13 min"],
                ],
                caption="Pilot results over four weeks.",
                label="tab:pilot", alignment="lrr", style="booktabs",
                header=True,
            ),
            _p("Median build time fell by 60 %."),

            Frame(children=[Text(text="Summary")]),
            _ord_items(
                "Builds are slow because the cache is keyed on machines.",
                "A content-addressed cache fixes that.",
                "The pilot cut the median build by 60 %.",
            ),
            RawLatex(text="\\begin{block}{Next step}\n"
                          "Roll out to the main monorepo in the June "
                          "maintenance window.\n\\end{block}"),
        ],
    )


# ------------------------------------------------------- book chapter

def book_chapter() -> Document:
    """A textbook chapter in the book class: definitions, worked example,
    numbered equations, a table, footnotes and a bibliography."""
    return Document(
        meta=_meta(
            documentclass="book",
            title="Radioactive decay",
            author="A. Author",
            class_options="oneside",
            body_font_pt=11,
            line_spacing=1.15,
            margin_left_cm=3.0, margin_right_cm=3.0,
            packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"],
        ),
        children=[
            Title(children=[Text(text="Radioactive decay")]),
            Author(children=[Text(text="A. Author")]),

            Section(level=1, children=[Text(text="Radioactive decay")],
                    label="ch:decay"),
            _p("An unstable nucleus transforms into another one at a "
               "moment that nothing in its past predicts. Yet a large "
               "sample of identical nuclei decays with perfect "
               "regularity. This chapter derives that regularity, "
               "defines the quantities used to measure it, and applies "
               "them to a medical radioisotope generator. The "
               "treatment follows the standard approach of "
               "introductory nuclear physics texts ",
               Citation(keys=["example2019", "sample2021"], style="cite"),
               "."),

            _sec("The decay law", 2),
            _p("Suppose a sample contains ", _m("N(t)"), " nuclei at "
               "time ", _m("t"), ". Each nucleus has the same "
               "probability per unit time ", _m(r"\lambda"),
               " of decaying, independent of its age and of its "
               "surroundings. In a short interval ", _m(r"\mathrm{d}t"),
               " the number of decays is therefore "
               "proportional to the number of nuclei present,"),
            MathBlock(latex=r"\frac{\mathrm{d}N}{\mathrm{d}t} = "
                            r"-\lambda N,",
                      numbered=True, label="eq:rate"),
            _p("and integrating from the initial population ",
               _m("N_0"), " gives the exponential law"),
            MathBlock(latex=r"N(t) = N_0\, e^{-\lambda t}.",
                      numbered=True, label="eq:decay"),
            _p("The constant ", _m(r"\lambda"), " is the decay constant, "
               "measured in ", _m(r"\mathrm{s^{-1}}"), "; the mean "
               "lifetime is its inverse, ", _m(r"\tau = 1/\lambda"),
               "."),

            _sec("Half-life and activity", 2),
            Theorem(kind="definition", title="Half-life",
                    children=[Text(text="The half-life "),
                              _m(r"t_{1/2}"),
                              Text(text=" is the time after which half "
                                        "of an initial population has "
                                        "decayed.")]),
            _p("Setting ", _m(r"N = N_0/2"), " in Equation ",
               CrossRef(label="eq:decay", kind="eqref"), " gives"),
            MathBlock(latex=r"t_{1/2} = \frac{\ln 2}{\lambda} "
                            r"\approx 0.693\,\tau.",
                      numbered=True, label="eq:halflife"),
            _p("What a detector counts is not ", _m("N"), " but the "
               "activity ", _m(r"A = \lambda N"),
               ", the number of decays per second. Its SI unit is the "
               "becquerel (1 Bq = 1 decay per second)",
               Footnote(children=[Text(text=
                   "The older unit, the curie, equals "),
                   _m(r"3.7\times10^{10}\ \mathrm{Bq}"),
                   Text(text=" and is still found in clinical "
                             "literature.")]),
               ". Because ", _m(r"A \propto N"), ", the activity "
               "obeys the same exponential law as the population, "
               "with the same half-life."),
            _p("Table ", CrossRef(label="tab:isotopes"), " lists "
               "five isotopes whose half-lives span seven orders of "
               "magnitude."),
            Table(
                rows=[
                    ["Isotope", "Half-life", "$\\lambda$ (s$^{-1}$)",
                     "Typical use"],
                    ["Tc-99m", "6.01 h", "$3.20\\times10^{-5}$",
                     "medical imaging"],
                    ["Po-210", "138 d", "$5.80\\times10^{-8}$",
                     "static eliminators"],
                    ["I-131", "8.02 d", "$1.00\\times10^{-6}$",
                     "thyroid therapy"],
                    ["Co-60", "5.27 y", "$4.17\\times10^{-9}$",
                     "radiotherapy sources"],
                    ["C-14", "5730 y", "$3.83\\times10^{-12}$",
                     "radiocarbon dating"],
                ],
                caption="Half-lives and decay constants of five "
                        "isotopes.",
                label="tab:isotopes", alignment="llrl",
                style="booktabs", header=True,
            ),

            _sec("A worked example", 2),
            Theorem(kind="example", title="",
                    children=[Text(text=
                        "A therapy dose of iodine-131 has an activity of "
                        "200 MBq. How many atoms does it contain, and "
                        "what is its activity after 24 days?")]),
            _p("From Table ", CrossRef(label="tab:isotopes"),
               ", ", _m(r"\lambda = 1.00\times10^{-6}\ \mathrm{s^{-1}}"),
               ". The number of atoms follows from the definition of "
               "activity:"),
            MathBlock(latex=r"N = \frac{A}{\lambda} = "
                            r"\frac{2.00\times10^{8}\ \mathrm{s^{-1}}}"
                            r"{1.00\times10^{-6}\ \mathrm{s^{-1}}} = "
                            r"2.0\times10^{14}.",
                      numbered=False),
            _p("With a molar mass of 131 g/mol this is about 44 ng of "
               "iodine, an invisible quantity. After 24 days, nearly "
               "three half-lives, Equation ",
               CrossRef(label="eq:decay", kind="eqref"),
               " gives"),
            MathBlock(latex=r"A(24\ \mathrm{d}) = 200\ \mathrm{MBq}\times "
                            r"2^{-24/8.02} \approx 25\ \mathrm{MBq}.",
                      numbered=False),

            _sec("Decay chains", 2),
            _p("Often the product of a decay is itself radioactive. "
               "For a parent ", _m("1"), " that feeds a daughter ",
               _m("2"), ", the daughter population obeys "
               r"", _m(r"\dot N_2 = \lambda_1 N_1 - \lambda_2 N_2"),
               ", whose solution with ", _m("N_2(0)=0"), " is"),
            MathBlock(latex=r"N_2(t) = N_1(0)\,"
                            r"\frac{\lambda_1}{\lambda_2-\lambda_1}"
                            r"\left(e^{-\lambda_1 t} - "
                            r"e^{-\lambda_2 t}\right).",
                      numbered=True, label="eq:bateman"),
            _p("When the parent lives much longer than the daughter, "
               "the ratio of activities settles to a constant, a state "
               "called transient equilibrium:"),
            MathBlock(latex=r"\frac{A_2}{A_1} \to "
                            r"\frac{\lambda_2}{\lambda_2-\lambda_1}.",
                      numbered=True, label="eq:equilibrium"),
            _p("The technetium generator used in hospitals works this "
               "way. Molybdenum-99 (65.9 h) decays to technetium-99m "
               "(6.01 h). Inserting the two decay constants, ",
               _m(r"0.0105\ \mathrm{h^{-1}}"), " and ",
               _m(r"0.115\ \mathrm{h^{-1}}"),
               " respectively, into Equation ",
               CrossRef(label="eq:equilibrium", kind="eqref"),
               " gives an activity ratio of about 1.1: the daughter "
               "is always slightly more active than its parent, and "
               "can be “milked” from the generator every day."),

            _sec("Summary", 2),
            _items(
                "Decay is random for one nucleus and exponential for "
                "many.",
                "The half-life is ln 2 divided by the decay constant.",
                "Activity decays with the population, with the same "
                "half-life.",
                "In a chain, the daughter reaches transient "
                "equilibrium when the parent is the longer-lived.",
            ),

            _bib(
                ("example2019", "N. Example, \\emph{Introduction to "
                 "Nuclear Physics}, 3rd ed. (Fictional Press, 2019)."),
                ("sample2021", "M. Sample and P. Placeholder, "
                 "\\emph{Radioisotopes in Medicine} (Imaginary "
                 "University Press, 2021)."),
            ),
        ],
    )


# -------------------------------------------------------- white paper

def white_paper() -> Document:
    """White paper: executive summary, problem, options, recommendation."""
    return Document(
        meta=_meta(
            title="Reducing build times in large-scale monorepos",
            author="A. Author",
            body_font_pt=11,
            line_spacing=1.15,
            paragraph_indent=False,
            packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"],
        ),
        children=[
            Title(children=[Text(text="Reducing build times in "
                                      "large-scale monorepos")]),
            Author(children=[Text(text="A. Author, Developer "
                                       "Productivity Team, Somewhere "
                                       "Software — May 2026")]),
            Abstract(children=[Text(text=
                "Median CI build time in our monorepo has grown from "
                "8 to 35 minutes in 18 months, because the module count "
                "tripled while caching stayed machine-local. We "
                "analyse the causes, compare three remedies and "
                "recommend a phased rollout of a shared build cache, "
                "dependency pruning and test sharding. We project a "
                "median incremental build of 10 minutes, a 70% "
                "reduction, for about 1.5 engineer-months.")]),

            _sec("Problem statement"),
            _p("A push to the main monorepo currently takes 35 minutes "
               "to build and test on average, and 52 minutes at the "
               "95th percentile. Developer surveys rank build latency "
               "as the first source of friction ",
               Citation(keys=["survey2026"]), ". The problem "
               "compounds: slow builds encourage large pull requests, "
               "which are harder to review, conflict more often and "
               "build more slowly."),
            _p("Table ", CrossRef(label="tab:stages"), " shows where "
               "the time goes."),
            Table(
                rows=[
                    ["Stage", "Median (min)", "Share"],
                    ["Dependency resolution", "6", "17\\%"],
                    ["Compilation", "17", "49\\%"],
                    ["Tests", "12", "34\\%"],
                    ["Total", "35", "100\\%"],
                ],
                caption="Median CI build time by stage.",
                label="tab:stages", alignment="lrr", style="booktabs",
                header=True,
            ),
            _p("Three factors contribute roughly equally to the "
               "regression:"),
            _ord_items(
                "The module count grew from 120 to 380 without "
                "revisiting the dependency graph; many modules pull in "
                "transitive dependencies they never use.",
                "The cache is local to each machine and is invalidated "
                "by environment drift (JDK patch level, locale, "
                "timezone). The CI cache hit rate is below 40%.",
                "Test execution is poorly parallelised: the payments "
                "integration suite takes 14 minutes on a single "
                "executor.",
            ),

            _sec("Options considered"),
            _sec("Option A: shared build cache", 2),
            _p("A content-addressed cache keys each task output on the "
               "hash of its inputs rather than on machine state. If a "
               "fraction ", _m("h"), " of tasks are served from the "
               "cache at a mean cost ", _m(r"\tau"),
               ", the build time becomes"),
            MathBlock(latex=r"T(h) = (1-h)\,T_0 + h\,\tau ,",
                      numbered=True, label="eq:model"),
            _p("where ", _m("T_0 = 35"), " min is today’s build. "
               "With ", _m("h = 0.8"), " and ", _m(r"\tau = 4"),
               " min, Equation ", CrossRef(label="eq:model", kind="eqref"),
               " gives about 10 minutes. A pilot on two smaller "
               "repositories raised the hit rate from 38% to 87% and "
               "cut the median build by 60%",
               Footnote(children=[Text(text=
                   "Four weeks of CI data, 1,240 builds in total.")]),
               "."),
            _sec("Option B: dependency pruning", 2),
            _p("Static analysis found 94 unused transitive edges. "
               "Removing them shrinks the rebuild set for a typical "
               "one-module change from about 70 modules to about 25. "
               "The change is low-risk: each removal is verified by a "
               "clean build before merging."),
            _sec("Option C: test sharding", 2),
            _p("Splitting the payments integration suite across four "
               "executors reduces its wall-clock time from 14 to "
               "4.5 minutes. It requires tagging 340 test files with a "
               "shard index."),

            _sec("Recommendation"),
            _p("We recommend the phased plan in Table ",
               CrossRef(label="tab:phases"), ". Phases 1 and 2 are "
               "independent and can run in parallel; phase 3 depends "
               "on the pruned graph of phase 2."),
            Table(
                rows=[
                    ["Phase", "Strategy", "Timeline", "Expected impact"],
                    ["1", "Shared cache", "Jun 2026",
                     "−60\\% median build time"],
                    ["2", "Dependency pruning", "Jul–Aug 2026",
                     "−30\\% rebuild set"],
                    ["3", "Test sharding", "Sep 2026",
                     "−10 min at P95"],
                ],
                caption="Phased rollout plan.",
                label="tab:phases", alignment="clll",
                style="booktabs", header=True,
            ),
            _p("Total estimated effort is 1.5 engineer-months."),

            _sec("Risks and mitigations"),
            _items(
                "Cache poisoning: content-addressed keys and a nightly "
                "integrity check.",
                "False-positive pruning: every removal is gated on a "
                "green CI run.",
                "Shard imbalance: monitored on a dashboard and "
                "re-balanced quarterly.",
            ),

            _sec("Conclusion"),
            _p("Build latency is a solvable problem. The three "
               "strategies are complementary and, together, bring the "
               "median build back below 12 minutes. We request "
               "approval to start phase 1 in the June maintenance "
               "window."),
            _bib(("survey2026", "Developer Productivity Team, "
                  "\\emph{Developer experience survey 2026}, internal "
                  "report, Somewhere Software, March 2026.")),
        ],
    )


# ------------------------------------------------------------- thesis

def thesis() -> Document:
    """PhD thesis in the report class: front matter, six chapters, an
    appendix and a bibliography, with a one-column 1.5-spaced layout."""
    return Document(
        meta=_meta(
            documentclass="report",
            title="Fast sparse regression for high-dimensional data",
            author="A. Student",
            body_font_pt=12,
            line_spacing=1.5,
            margin_left_cm=3.5, margin_right_cm=2.5,
            margin_top_cm=2.5, margin_bottom_cm=2.5,
            packages=DEFAULT_PACKAGES + [
                "booktabs", "tikz", "hyperref", "appendix",
                "algorithm2e",
            ],
        ),
        children=[
            Title(children=[Text(text="Fast sparse regression for "
                                      "high-dimensional data")]),
            Author(children=[Text(text="A. Student")]),
            Affiliation(children=[Text(text="Department of Computer "
                                            "Science, University of "
                                            "Somewhere")]),
            Abstract(children=[Text(text=
                "Sparse linear models are a workhorse of data analysis, "
                "but fitting them on datasets with millions of features "
                "remains slow. This thesis presents a proximal gradient "
                "algorithm whose cost per iteration is linear in the "
                "size of the data and which converges at the optimal "
                "rate for first-order methods. On four benchmark "
                "datasets it improves accuracy by 4 to 7 percentage "
                "points over three baselines at equal running time. "
                "We also give a convergence proof and a study of its "
                "limitations.")]),

            Section(level=1, children=[Text(text="Acknowledgements")],
                    numbered=False),
            _p("I thank my supervisor, Prof. J. Supervisor, for her "
               "guidance throughout this work, the members of the "
               "optimisation group for many fruitful discussions, and "
               "the Somewhere Research Council for funding under grant "
               "SRC-2022-114. Above all I thank my family."),

            RawLatex(text="\\tableofcontents"),

            # ------------------------------------------------ chapter 1
            Section(level=1, children=[Text(text="Introduction")],
                    label="ch:intro"),
            _sec("Background and motivation", 2),
            _p("Regularised regression is among the most widely used "
               "statistical tools. When the number of features ",
               _m("d"), " is large, the lasso ",
               Citation(keys=["tibs1996"], style="cite"),
               " selects a small subset of them by penalising the ",
               _m(r"\ell_1"), " norm of the coefficients. Genomics, "
               "text classification and online advertising routinely "
               "produce problems with ", _m(r"d > 10^6"),
               ", where even one pass over the data is expensive."),
            _sec("Research questions", 2),
            _p("This thesis addresses three questions:"),
            _ord_items(
                "Can the lasso be fitted with a cost per iteration "
                "linear in the number of non-zero entries of the data?",
                "Does the resulting algorithm retain the optimal "
                "convergence rate of first-order methods?",
                "How does it compare in accuracy with established "
                "solvers on standard benchmarks?",
            ),
            _sec("Thesis outline", 2),
            _p("Chapter 2 reviews the literature and Chapter 3 "
               "presents the algorithm and its analysis. Chapter 4 "
               "reports experiments (see Table ",
               CrossRef(label="tab:results"), " and Figure ",
               CrossRef(label="fig:conv"), "), Chapter 5 discusses "
               "them, and Chapter 6 concludes."),

            # ------------------------------------------------ chapter 2
            Section(level=1, children=[Text(text="Literature review")]),
            _sec("Sparse regression", 2),
            _p("Given a design matrix ", _m(r"X \in \mathbb{R}^{n\times d}"),
               " and a response ", _m(r"y \in \mathbb{R}^{n}"),
               ", the lasso solves"),
            MathBlock(latex=r"\beta^{*} = \arg\min_{\beta}\ "
                            r"\tfrac{1}{2}\|X\beta - y\|_2^2 + "
                            r"\lambda\|\beta\|_1 ,",
                      numbered=True, label="eq:lasso"),
            _p("with ", _m(r"\lambda > 0"), " controlling sparsity. "
               "Least-angle regression ",
               Citation(keys=["efron2004"], style="cite"),
               " traces the whole solution path but needs "
               "cubic time in the number of active features."),
            _sec("First-order methods", 2),
            _p("Coordinate descent ", Citation(keys=["friedman2010"],
                                                   style="cite"),
               " and proximal gradient methods ",
               Citation(keys=["beck2009"], style="cite"),
               " avoid matrix factorisations. Accelerated proximal "
               "gradient attains the optimal ",
               _m(r"O(1/t^2)"), " rate, but each iteration touches the "
               "full matrix."),
            _sec("Identified gap", 2),
            _p("No published solver combines a per-iteration cost "
               "proportional to the data sparsity with the accelerated "
               "rate and a guarantee on the selected support. Closing "
               "this gap is the aim of the thesis."),

            # ------------------------------------------------ chapter 3
            Section(level=1, children=[Text(text="Methodology")]),
            _sec("Problem formulation", 2),
            _p("We study Equation ", CrossRef(label="eq:lasso",
                                               kind="eqref"),
               " under the assumption that ", _m("X"), " has ",
               _m("m"), " non-zero entries, so one multiplication by ",
               _m("X"), " costs ", _m("O(m)"), ". Let ", _m("L"),
               " be the largest eigenvalue of ", _m(r"X^\top X"), "."),
            _sec("The algorithm", 2),
            _p("Algorithm ", CrossRef(label="alg:pgd"), " applies "
               "soft-thresholding after each gradient step of size ",
               _m("1/L"), "."),
            RawLatex(text=(
                "\\begin{algorithm}[H]\n"
                "\\SetAlgoLined\n"
                "\\KwIn{$X$, $y$, $\\lambda$, step size $\\eta = 1/L$, "
                "iterations $T$}\n"
                "\\KwOut{Coefficients $\\beta_T$}\n"
                "$\\beta_0 \\leftarrow 0$\\;\n"
                "\\For{$t = 1$ \\KwTo $T$}{\n"
                "  $g_t \\leftarrow X^\\top (X\\beta_{t-1} - y)$\\;\n"
                "  $\\beta_t \\leftarrow \\mathrm{soft}(\\beta_{t-1} - "
                "\\eta g_t,\\ \\eta\\lambda)$\\;\n"
                "}\n"
                "\\caption{Proximal gradient for the lasso}\n"
                "\\label{alg:pgd}\n"
                "\\end{algorithm}")),
            _sec("Convergence", 2),
            Theorem(kind="proposition", title="Convergence rate",
                    children=[Text(text="Let "), _m(r"F(\beta)"),
                              Text(text=" be the objective of "
                                        "Equation "),
                              CrossRef(label="eq:lasso", kind="eqref"),
                              Text(text=". Then Algorithm 1 satisfies "),
                              _m(r"F(\beta_t)-F(\beta^*) \le "
                                 r"\dfrac{L\|\beta^*\|_2^2}{2t}"),
                              Text(text=".")]),
            Theorem(kind="proof", title="", children=[
                Text(text="The bound follows from the standard "
                          "descent lemma for the smooth part and the "
                          "non-expansiveness of the proximal map; "
                          "see Appendix "),
                CrossRef(label="app:proof"), Text(text=".")]),
            _p("Adding momentum improves the rate to ",
               _m(r"O(1/t^2)"), ", at the price of one extra vector."),
            _sec("Implementation", 2),
            _p("The algorithm was implemented in Python 3.12 with "
               "NumPy and SciPy sparse matrices. Experiments ran on a "
               "workstation with 64 GB of memory. The stopping "
               "tolerance was ", _m(r"\epsilon = 10^{-6}"),
               " and the iteration limit ", _m("T = 10{,}000"), "."),

            # ------------------------------------------------ chapter 4
            Section(level=1, children=[Text(text="Results")]),
            _sec("Accuracy", 2),
            _p("Table ", CrossRef(label="tab:results"),
               " compares our method with three baselines on four "
               "benchmark datasets at equal wall-clock budget."),
            Table(
                rows=[
                    ["Method", "A", "B", "C", "D"],
                    ["Baseline 1", "82.3", "78.1", "85.6", "79.4"],
                    ["Baseline 2", "84.7", "80.3", "86.2", "81.0"],
                    ["Baseline 3", "86.1", "82.5", "87.0", "83.2"],
                    ["Ours", "91.4", "89.7", "92.1", "90.3"],
                ],
                caption="Test accuracy (\\%) on four benchmark datasets.",
                label="tab:results", alignment="lcccc",
                style="booktabs", header=True,
            ),
            _p("Our method is best on every dataset. The largest gain, "
               "7.2 percentage points over the best baseline, is on "
               "dataset B."),
            _sec("Convergence behaviour", 2),
            _p("Figure ", CrossRef(label="fig:conv"), " shows a "
               "typical run: the objective is within 6% of its final "
               "value after 500 iterations."),
            RawLatex(text=(
                "\\begin{figure}[H]\n\\centering\n"
                "\\begin{tikzpicture}[x=0.012cm,y=1.1cm]\n"
                "  \\draw[->] (0,0.8) -- (520,0.8) node[right] "
                "{\\small $t$};\n"
                "  \\draw[->] (0,0.8) -- (0,5.3) node[above] "
                "{\\small $F(\\beta_t)$};\n"
                "  \\draw[thick,blue!60!black,domain=0:500,samples=60] "
                "plot (\\x, {1 + 4*exp(-\\x/120)});\n"
                "  \\draw[dashed] (0,1) -- (500,1);\n"
                "  \\foreach \\t in {0,100,...,500}\n"
                "    \\draw (\\t,0.8) -- (\\t,0.7) "
                "node[below] {\\small \\t};\n"
                "\\end{tikzpicture}\n"
                "\\caption{Objective value of Algorithm 1 against "
                "the iteration count (normalised so that the optimum "
                "is 1).}\n"
                "\\label{fig:conv}\n\\end{figure}")),

            # ------------------------------------------------ chapter 5
            Section(level=1, children=[Text(text="Discussion")]),
            _sec("Interpretation", 2),
            _p("The results of Table ", CrossRef(label="tab:results"),
               " confirm that exploiting sparsity does not cost "
               "accuracy: the extra iterations gained within a fixed "
               "time budget translate directly into a better solution "
               "of Equation ", CrossRef(label="eq:lasso", kind="eqref"),
               "."),
            _sec("Limitations", 2),
            _items(
                "Features must be standardised before fitting; "
                "unscaled inputs slow convergence.",
                "Only tabular data were evaluated; text and image "
                "features remain future work.",
                "The convergence proof needs a fixed step size and "
                "does not cover adaptive schemes.",
            ),

            # ------------------------------------------------ chapter 6
            Section(level=1, children=[Text(text="Conclusion")]),
            _sec("Summary of contributions", 2),
            _ord_items(
                "A proximal gradient solver with cost linear in the "
                "data sparsity per iteration.",
                "A proof of the optimal first-order convergence rate.",
                "An empirical study showing gains of 4 to 7 "
                "percentage points on four benchmarks.",
            ),
            _sec("Future work", 2),
            _p("Natural extensions are streaming data, non-convex "
               "penalties and a distributed implementation."),

            # ------------------------------------------------ appendix
            RawLatex(text="\\appendix"),
            Section(level=1, children=[Text(text="Proof of the "
                                                 "convergence rate")],
                    label="app:proof"),
            _p("Let ", _m("f"), " be the smooth term, with gradient "
               "Lipschitz constant ", _m("L"), ". The descent lemma "
               "gives"),
            MathBlock(latex=r"f(\beta_t) \le f(\beta_{t-1}) + "
                            r"\langle \nabla f(\beta_{t-1}), "
                            r"\beta_t-\beta_{t-1}\rangle + "
                            r"\tfrac{L}{2}\|\beta_t-\beta_{t-1}\|_2^2 .",
                      numbered=True, label="eq:descent"),
            _p("Combining Equation ", CrossRef(label="eq:descent",
                                                kind="eqref"),
               " with the optimality condition of the proximal step "
               "and summing over ", _m("t"), " telescopes to the bound "
               "of the proposition."),
            Section(level=1, children=[Text(text="Additional results")]),
            Table(
                rows=[
                    ["Fold", "Precision", "Recall", "F1"],
                    ["1", "0.923", "0.911", "0.917"],
                    ["2", "0.935", "0.928", "0.931"],
                    ["3", "0.918", "0.905", "0.911"],
                    ["4", "0.941", "0.932", "0.936"],
                    ["5", "0.929", "0.919", "0.924"],
                ],
                caption="Per-fold cross-validation scores on dataset A.",
                label="tab:folds", alignment="lccc",
                style="booktabs", header=True,
            ),
            _bib(
                ("tibs1996", "A. Tester, Regression shrinkage and "
                 "selection via a norm penalty, \\emph{J. Fictional "
                 "Stat. Soc.} \\textbf{58} (1996) 267--288."),
                ("efron2004", "B. Example, C. Sample and D. Placeholder, "
                 "Least angle selection, \\emph{Ann. Imaginary Stat.} "
                 "\\textbf{32} (2004) 407--499."),
                ("friedman2010", "E. Model and F. Fitter, "
                 "Regularisation paths by coordinate descent, "
                 "\\emph{J. Fictional Softw.} \\textbf{33} (2010) "
                 "1--22."),
                ("beck2009", "G. Prox and H. Gradient, A fast "
                 "iterative shrinkage algorithm, \\emph{SIAM J. "
                 "Imaging Sci. (fictional)} \\textbf{2} (2009) "
                 "183--202."),
            ),
        ],
    )
