"""The welcome tour, the empty page and the article family."""
from __future__ import annotations

from ..example_helpers import _items, _meta, _ord_items, _p
from ..model import (
    Abstract, Affiliation, Author, Citation, Correspondence, CrossRef,
    DEFAULT_PACKAGES, Document, Footnote, Keywords, Link, MathBlock,
    MathInline, Paragraph, RawLatex, Section, Table, Text, Theorem, Title,
)


def _h(text: str, level: int = 1, label: str | None = None) -> Section:
    return Section(level=level, children=[Text(text=text)], label=label)


def _bib(*entries: tuple[str, str]) -> RawLatex:
    body = "\n".join(f"\\bibitem{{{k}}} {t}" for k, t in entries)
    return RawLatex(text="\\begin{thebibliography}{99}\n" + body
                         + "\n\\end{thebibliography}")


# ---------------------------------------------------------------- welcome

def welcome() -> Document:
    """Guided tour of the editor: what a new user sees first."""
    return Document(
        meta=_meta(title="Welcome to KherveTeX",
                   author="The KherveTeX team",
                   packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"],
                   preamble_extras=r"\usepackage[normalem]{ulem}"),
        children=[
            Title(children=[Text(text="Welcome to KherveTeX")]),
            Author(children=[Text(text="A ten-minute guided tour of the editor")]),

            _h("What KherveTeX is"),
            _p(
                "KherveTeX is a word processor that writes real LaTeX. You "
                "type and format here, in the ", ("Visual", ["bold"]),
                " tab, the way you would in Word. Every pause, the "
                "document is compiled to PDF so you can see exactly what "
                "will be printed. Behind the scenes it is stored as a "
                "structured model (headings, paragraphs, lists, tables, "
                "equations) that is turned into clean, readable ",
                (".tex", ["code"]), " source on demand.",
            ),
            _p(
                "This page is itself a KherveTeX document. Click anywhere "
                "in it and type, change a heading, or break something on "
                "purpose: nothing you do here is saved unless you save it, "
                "and ", ("File > New", ["bold"]),
                " always gives you a fresh page.",
            ),

            _h("Quick start"),
            _p("The shortest path from an empty page to a finished PDF:"),
            _ord_items(
                "Press Ctrl+N (Cmd+N on a Mac) for a blank document, or "
                "pick a ready-made one from the Examples menu.",
                "Type your title and text. Use the Paragraph style box on "
                "the ribbon for headings, an abstract or keywords.",
                "Insert what you need from the Insert menu: a table, an "
                "equation, a footnote, a citation, a cross-reference.",
                "Check the PDF in the side panel (Ctrl+4) or on its own "
                "tab (Ctrl+3). Compile on demand with Ctrl+Shift+C.",
                "Save with Ctrl+S. Export a PDF, a .tex file or a Word "
                "file from File > Export.",
            ),

            _h("The tabs: Visual, Code and PDF"),
            _p(
                "Three views of the same document, one keystroke apart. "
                "Visual (Ctrl+1) is where you write. Code (Ctrl+2) shows "
                "the LaTeX that KherveTeX generates, so you can read it, "
                "copy it, or learn from it. PDF (Ctrl+3) is the compiled "
                "result. In ", ("View", ["bold"]),
                " you can keep the PDF beside the page, in its own "
                "window on a second screen, or hide it entirely to write "
                "undisturbed.",
            ),
            _p(
                "If something looks wrong in the PDF, the Console "
                "(View > Show Console) lists the compiler messages in "
                "plain text.",
            ),

            _h("Formatting text"),
            _p(
                "Select text and use the ribbon or the Format menu to make "
                "it ", ("bold", ["bold"]), ", ", ("italic", ["italic"]),
                ", ", ("underlined", ["underline"]), ", ",
                ("struck through", ["strikethrough"]), " or ",
                ("monospaced", ["code"]), ". Subscripts (H",
                ("2", ["subscript"]), "O), superscripts (m",
                ("2", ["superscript"]), ") and ",
                ("small caps", ["smallcaps"]),
                " work the same way. Every mark becomes the matching LaTeX "
                "command, so the PDF always agrees with the page.",
            ),
            _h("Headings and paragraph styles", level=2),
            _p(
                "The Paragraph style box turns the current paragraph into "
                "a heading (five levels, numbered automatically), a title, "
                "an author line, an abstract or a keyword line. The "
                "outline of your document is then always one glance away. "
                "Alignment (left, centre, right, justified) sits next to "
                "the formatting buttons.",
            ),
            _h("Lists", level=2),
            _p("Bulleted and numbered lists nest with Tab and Shift+Tab. "
               "Inside an item you can use bold, links, footnotes and "
               "inline math like any other text. Some things worth "
               "knowing:"),
            _items(
                "Use a bulleted list for things with no order, such as "
                "an inventory or a set of options.",
                "Use a numbered list for a procedure, where the order "
                "matters.",
                "Nested lists change their bullet style on their own at "
                "each depth.",
            ),

            _h("Mathematics"),
            _p(
                "Inline math such as ", MathInline(latex=r"E = mc^2"),
                " is typed with Ctrl+M; a displayed equation is Ctrl+Shift+M. "
                "The Equation builder (Ctrl+Shift+E) offers fractions, "
                "integrals, matrices and more as templates, and the Symbol "
                "palette (Ctrl+Shift+G) holds Greek letters, operators "
                "and arrows. A numbered, labelled equation:",
            ),
            MathBlock(latex=r"\int_{-\infty}^{\infty} e^{-x^{2}}\,dx = \sqrt{\pi}",
                      numbered=True, label="eq:gauss"),
            _p(
                "Multi-line derivations use the aligned environments. Here "
                "is the quadratic formula derived by completing the square:",
            ),
            MathBlock(
                latex=(
                    "\\begin{align}\n"
                    "  a x^2 + b x + c &= 0 \\\\\n"
                    "  \\left(x + \\tfrac{b}{2a}\\right)^2 &= "
                    "\\tfrac{b^2 - 4ac}{4a^2} \\\\\n"
                    "  x &= \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\n"
                    "\\end{align}"
                ),
                numbered=True,
            ),
            _p(
                "To point back at an equation, use Insert > Cross-reference "
                "and pick it from the list: Equation ",
                CrossRef(label="eq:gauss", kind="eqref"),
                " is the Gaussian integral above. If the equation is "
                "renumbered later, the reference follows.",
            ),

            _h("Tables"),
            _p(
                "Insert > Table creates a grid you fill in directly, with "
                "a caption and a label for cross-references. Table ",
                CrossRef(label="tab:shortcuts", kind="ref"),
                " collects the shortcuts used in this tour (on a Mac, "
                "read Ctrl as Cmd).",
            ),
            Table(
                rows=[
                    ["Action",             "Shortcut",      "Menu"],
                    ["Bold / italic / underline", "Ctrl+B / I / U", "Format"],
                    ["Inline math",        "Ctrl+M",        "Insert"],
                    ["Math block",         "Ctrl+Shift+M",  "Insert"],
                    ["Equation builder",   "Ctrl+Shift+E",  "Insert"],
                    ["Symbol palette",     "Ctrl+Shift+G",  "Insert"],
                    ["Hyperlink",          "Ctrl+K",        "Insert"],
                    ["Visual / Code / PDF", "Ctrl+1 / 2 / 3", "View"],
                    ["Compile now",        "Ctrl+Shift+C",  "Compiler"],
                    ["New comment",        "Ctrl+Alt+M",    "Review"],
                    ["New window",         "Ctrl+Shift+N",  "File"],
                ],
                caption="Keyboard shortcuts used in this tour.",
                label="tab:shortcuts",
                alignment="lll",
                header=True,
            ),

            _h("Figures, links, footnotes and citations"),
            _p(
                "Insert > Figure places an image with a caption; relative "
                "paths are resolved against the document's folder, and a "
                "missing image shows as a labelled placeholder instead of "
                "breaking the build. Insert > Drawing and the Flowchart "
                "builder (Ctrl+Shift+F) draw simple diagrams without "
                "leaving the editor.",
            ),
            _p(
                "Hyperlinks (Ctrl+K) look like ",
                Link(url="https://tectonic-typesetting.github.io/",
                     children=[Text(text="the Tectonic project")]),
                ", the LaTeX engine that compiles your documents. "
                "A footnote",
                Footnote(children=[Text(text=
                    "A footnote is typed inline and printed at the foot "
                    "of the page in the PDF.")]),
                " is typed in place and moves to the bottom of the page "
                "in the PDF. A citation such as ",
                Citation(keys=["example2026"], style="cite"),
                " points to an entry of the reference list at the end of "
                "this document; Insert > Citation lists the keys "
                "available.",
            ),

            _h("Layout: pages and columns"),
            _p(
                "Document properties (File menu) sets the page size, "
                "margins, font, font size and line spacing for the whole "
                "document. The 1, 2 and 3 column buttons next to the "
                "alignment group reflow everything at once, and Insert > "
                "Multi-column region puts a two-column block inside an "
                "otherwise single-column page.",
            ),

            _h("Versions with Git"),
            _p(
                "Each saved document lives in a Git repository. ",
                ("Git > Save snapshot and upload", ["bold"]),
                " records a version, and ",
                ("Git > View version history", ["bold"]),
                " lets you browse every snapshot and go back to any of "
                "them. Snapshots use your normal Git identity, so they "
                "look the same as commits made from the command line.",
            ),

            _h("Review: comments and highlights"),
            _p(
                "Select a passage and choose Review > New comment "
                "(Ctrl+Alt+M) to leave a note for yourself or a "
                "co-author. Highlights mark text without changing it. "
                "Accept or reject a comment from the Review menu, and "
                "step through them with the next and previous buttons.",
            ),

            _h("Importing and exporting"),
            _p(
                "File > Import reads existing ", (".tex", ["code"]),
                ", Word (.docx), PDF and Markdown files. Anything the "
                "editor does not understand is kept as a raw LaTeX block, "
                "so an imported file can be exported again without losing "
                "content. File > Export writes .tex, .docx or .pdf.",
            ),
            _p(
                "The Compiler menu chooses between the LaTeX engine and "
                "Typst, and ",
                ("Compiler status", ["bold"]),
                " tells you whether the engine and its offline package "
                "cache are ready.",
            ),

            _h("Where to go next"),
            _p(
                "Open the ", ("Examples", ["bold"]),
                " menu for starting points: articles in one, two or three "
                "columns, letters, a CV, a lab report, lecture notes, "
                "journal templates and more. Each opens in its own window "
                "so this tour stays open. Help > User guide has the full "
                "reference, and Help > Keyboard shortcuts lists every "
                "key binding.",
            ),
            _p(
                "Happy writing. ",
                ("The KherveTeX team", ["italic"]),
            ),

            _bib(("example2026",
                  "I.~Writer and J.~Typesetter, \\emph{Writing documents "
                  "visually: an example reference}, Example Press, 2026.")),
        ],
    )


# ---------------------------------------------------------------- blank

def blank() -> Document:
    """A truly empty page, like Word: one empty paragraph, no title."""
    return Document(
        meta=_meta(),
        children=[Paragraph(children=[])],
    )


# ---------------------------------------------------------------- article

# Maxwell model with k_m = 0.20 W/(m K). Measured values, fit and table are
# kept consistent: k_f = 9.7 W/(m K), chi^2 = 1.4 for 4 degrees of freedom.
_RHO_M, _RHO_F, _K_M, _K_F = 1.15, 2.10, 0.20, 9.7
_RUNS = [(0, 0.20, 0.01), (5, 0.23, 0.01), (10, 0.27, 0.01),
         (15, 0.29, 0.01), (20, 0.34, 0.015), (30, 0.44, 0.02)]


def _maxwell(phi: float) -> float:
    kf, km = _K_F, _K_M
    return km * (kf + 2 * km + 2 * phi * (kf - km)) / (kf + 2 * km - phi * (kf - km))


def _article_rows() -> list[list[str]]:
    rows = [["Frac.", "Meas.", "Model", "Gain"]]
    for vol, k, u in _RUNS:
        phi = vol / 100
        rows.append([f"{phi:.2f}", f"{k:.2f}", f"{_maxwell(phi):.2f}",
                     f"{k / _K_M:.2f}"])
    return rows


def _article_body(title: str, subtitle: str) -> list:
    """Shared body of the single-, two- and three-column articles: a short
    experimental paper, the same text under three layouts."""
    note = Footnote(children=[Text(text=
        "Example document (" + subtitle + "). All names, institutions, "
        "data and references are fictional.")])
    return [
        Title(children=[Text(text=title)]),
        # \maketitle sets the author in a one-line box: in a narrow column
        # the names go on separate lines instead.
        *([Author(children=[Text(text="A. Author")]),
           Author(children=[Text(text="B. Coauthor")]),
           Author(children=[Text(text="C. Reviewer"), note])]
          if "three" in subtitle else
          [Author(children=[Text(text="A. Author¹, B. Coauthor¹, C. Reviewer²"),
                            note])]),
        *([] if "three" in subtitle else [
            Affiliation(children=[Text(text=
                "¹ Department of Materials Engineering, Northfield "
                "University")]),
            Affiliation(children=[Text(text=
                "² Halden Institute of Applied Physics")])]),
        Correspondence(children=[Text(text="a.author@example.org")]),
        Abstract(children=[Text(text=
            "Epoxy resins are good electrical insulators but poor "
            "conductors of heat, which limits their use in power "
            "electronics. We disperse hexagonal boron nitride platelets "
            "in a bisphenol-A epoxy at volume fractions from 0 to 30% and "
            "measure the thermal conductivity at 25 °C with a transient "
            "hot-wire probe. The conductivity rises from 0.20 W/(m K) for "
            "the neat resin to 0.44 W/(m K) at 30 vol%, a factor of 2.2. "
            "A Maxwell effective-medium model describes all compositions "
            "with a single filler conductivity of about 10 W/(m K), far "
            "below the bulk value, pointing to interfacial resistance as "
            "the limiting factor.")]),
        Keywords(children=[Text(text=
            "thermal conductivity · epoxy composites · boron nitride · "
            "effective-medium theory")]),

        _h("Introduction", label="sec:intro"),
        _p(
            "Heat removal is a central constraint in compact power "
            "electronics, where a polymer encapsulant must insulate "
            "electrically yet carry heat away from the device. Neat "
            "epoxies conduct only about 0.2 W/(m K), two to three orders "
            "of magnitude less than ceramics. The usual remedy is to load "
            "the resin with a ceramic filler, and hexagonal boron nitride "
            "(h-BN) is attractive because it combines a high in-plane "
            "conductivity with electrical resistivity above "
            "10",
            ("12", ["superscript"]), " Ω cm ",
            Citation(keys=["lindqvist2019", "okafor2021"], style="cite"),
            ".",
        ),
        _p(
            "Reported gains vary widely between laboratories, partly "
            "because the measurement method, the platelet size and the "
            "filler–matrix interface differ from study to study. Here we "
            "prepare a single series of composites from one resin batch "
            "and one filler grade, measure them with one method, and test "
            "whether a simple effective-medium model can describe the "
            "whole series. Section ",
            CrossRef(label="sec:methods", kind="ref"),
            " describes the samples and the measurement, Section ",
            CrossRef(label="sec:results", kind="ref"),
            " gives the results, and Section ",
            CrossRef(label="sec:discussion", kind="ref"),
            " discusses them.",
        ),

        _h("Materials and methods", label="sec:methods"),
        _h("Sample preparation", level=2),
        _p("Composites were made in five steps:"),
        _ord_items(
            "The filler (h-BN platelets, median lateral size 5 µm) was "
            "dried for 12 h at 120 °C.",
            "The resin and hardener were mixed at the stoichiometric "
            "ratio and degassed for 10 min.",
            "The filler was added in portions and homogenised in a "
            "planetary mixer at 2000 rpm.",
            "The mixture was cast into cylindrical moulds 40 mm in "
            "diameter and 80 mm tall.",
            "Samples were cured for 2 h at 80 °C and 4 h at 120 °C.",
        ),
        _p(
            "Six compositions were prepared, from 0 to 30 vol% filler. "
            "The densities of the resin and the filler are 1.15 and "
            "2.10 g/cm³, and the density of each composite follows from "
            "the rule of mixtures (Table ",
            CrossRef(label="tab:results", kind="ref"), ").",
        ),
        _h("Thermal measurements", level=2),
        _p(
            "The thermal conductivity was measured at 25 °C with a "
            "transient hot-wire probe embedded in each cylinder. A "
            "constant heating power ", MathInline(latex="q"),
            " per unit length is applied to the wire and the temperature "
            "rise ", MathInline(latex="\\Delta T"),
            " is recorded against time ", MathInline(latex="t"),
            ". For an ideal line source in an infinite medium the "
            "conductivity follows from the slope of ",
            MathInline(latex="\\Delta T"), " against ",
            MathInline(latex="\\ln t"), ":",
        ),
        MathBlock(
            latex=("k = \\frac{q}{4\\pi}\\,"
                   "\\left(\\frac{\\mathrm{d}\\,\\Delta T}"
                   "{\\mathrm{d}\\ln t}\\right)^{-1}."),
            numbered=True, label="eq:hotwire",
        ),
        _p(
            "Each value is the mean of five runs separated by 15 minutes "
            "to let the sample relax",
            Footnote(children=[Text(text=
                "Only the window between 1 s and 10 s was fitted, to "
                "avoid wire-contact effects at early times and boundary "
                "effects at late times.")]),
            "; the uncertainty is the larger of the run-to-run scatter "
            "and the 3% calibration uncertainty of the probe.",
        ),
        _h("Effective-medium model", level=2),
        _p(
            "We compare the data with the Maxwell model for spherical "
            "inclusions of conductivity ", MathInline(latex="k_f"),
            " at volume fraction ", MathInline(latex="\\phi"),
            " in a matrix of conductivity ", MathInline(latex="k_m"), ":",
        ),
        MathBlock(
            latex=("k_{\\mathrm{eff}} = k_m\\,"
                   "\\frac{k_f + 2k_m + 2\\phi\\,(k_f - k_m)}"
                   "{k_f + 2k_m - \\phi\\,(k_f - k_m)}."),
            numbered=True, label="eq:maxwell",
        ),
        _p(
            "With ", MathInline(latex="k_m"),
            " fixed at the measured value of the neat resin, ",
            MathInline(latex="k_f"),
            " is the only free parameter. It is found by minimising",
        ),
        MathBlock(
            latex=("\\chi^2(k_f) = \\sum_{i=1}^{N}"
                   "\\left(\\frac{k_i - k_{\\mathrm{eff}}(\\phi_i; k_f)}"
                   "{\\sigma_i}\\right)^2,"),
            numbered=True, label="eq:chi2",
        ),
        _p(
            "over the ", MathInline(latex="N = 5"),
            " filled samples, where ", MathInline(latex="k_i"),
            " and ", MathInline(latex="\\sigma_i"),
            " are the measured conductivity and its uncertainty.",
        ),

        _h("Results", label="sec:results"),
        _p(
            "Table ", CrossRef(label="tab:results", kind="ref"),
            " lists the measured conductivities. The neat resin gives ",
            MathInline(latex="k_m = 0.20\\ \\mathrm{W\\,m^{-1}\\,K^{-1}}"),
            ", and the conductivity grows monotonically with filler "
            "content to ", MathInline(latex="0.44\\ \\mathrm{W\\,m^{-1}\\,K^{-1}}"),
            " at 30 vol%.",
        ),
        Table(
            rows=_article_rows(),
            caption=("Filler volume fraction (Frac.), measured and modelled thermal "
                     "conductivity k (W/(m K)) at 25 °C, and enhancement "
                     "over the neat resin. Uncertainties: 0.010 to "
                     "0.020 W/(m K). The model uses a filler "
                     "conductivity of 9.7 W/(m K)."),
            label="tab:results",
            alignment="rrrr",
            header=True,
        ),
        _p(
            "Minimising Eq. ", CrossRef(label="eq:chi2", kind="eqref"),
            " gives ", MathInline(latex="k_f = 9.7\\ \\mathrm{W\\,m^{-1}\\,K^{-1}}"),
            " with ", MathInline(latex="\\chi^2 = 1.4"),
            " for 4 degrees of freedom. The one-standard-deviation "
            "interval, 5.7 to 28 W/(m K), is asymmetric because the model "
            "saturates when ", MathInline(latex="k_f \\gg k_m"),
            ". All model values in Table ",
            CrossRef(label="tab:results", kind="ref"),
            " lie within one standard deviation of the measurements.",
        ),

        _h("Discussion", label="sec:discussion"),
        _p(
            "The fitted filler conductivity is much lower than the "
            "in-plane value of several hundred W/(m K) reported for "
            "single h-BN crystals ", Citation(keys=["lindqvist2019"], style="cite"),
            ". This is expected for randomly oriented platelets "
            "separated from the matrix by an interfacial thermal "
            "resistance, and it is consistent with other epoxy–ceramic "
            "composites ", Citation(keys=["okafor2021", "tanaka2023"], style="cite"),
            ". Because Eq. ", CrossRef(label="eq:maxwell", kind="eqref"),
            " is insensitive to ", MathInline(latex="k_f"),
            " above about 30 W/(m K), the data cannot tell a poor "
            "interface from a poor filler; direct interface or "
            "single-platelet measurements would be needed.",
        ),
        _p(
            "Two limitations should be kept in mind. The Maxwell model "
            "ignores platelet shape and orientation, so it cannot "
            "describe the onset of percolation expected above 30 vol%. "
            "And all samples came from one resin batch, so batch-to-batch "
            "variation is not included in the uncertainties.",
        ),

        _h("Conclusions", label="sec:conclusions"),
        _p(
            "Adding 30 vol% h-BN raises the thermal conductivity of an "
            "epoxy resin from 0.20 to 0.44 W/(m K). A one-parameter "
            "Maxwell model fits the whole series with an effective "
            "filler conductivity of about 10 W/(m K), which suggests that "
            "improving the filler–matrix interface, rather than the "
            "filler itself, is the most promising route to higher "
            "conductivity.",
        ),

        Section(level=1, numbered=False,
                children=[Text(text="Acknowledgements")]),
        _p(
            "This work was supported by the Example Foundation (grant "
            "EF-0000). We thank the technical staff of the Northfield "
            "materials workshop for help with the moulds, and the "
            "maintainers of ",
            Link(url="https://tectonic-typesetting.github.io/",
                 children=[Text(text="Tectonic")]),
            ", the LaTeX engine used to typeset this document.",
        ),

        _bib(
            ("lindqvist2019",
             "M.~Lindqvist and S.~Brandt, Thermal transport in layered "
             "boron nitride, \\emph{J.\\ Example Mater.}\\ \\textbf{12}, "
             "345--356 (2019)."),
            ("okafor2021",
             "N.~Okafor, P.~Silva and R.~Haas, Ceramic fillers for "
             "thermally conductive polymers, \\emph{Example Polym.\\ "
             "Rev.}\\ \\textbf{8}, 101--128 (2021)."),
            ("tanaka2023",
             "H.~Tanaka and E.~Moreau, Interfacial resistance in epoxy "
             "composites, \\emph{Proc.\\ Example Conf.\\ Heat Transf.}, "
             "pp.~77--84 (2023)."),
        ),
    ]


def article() -> Document:
    """Single-column research article."""
    return Document(
        meta=_meta(title="Thermal conductivity of BN–epoxy composites",
                   author="A. Author, B. Coauthor, C. Reviewer",
                   packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"]),
        children=_article_body(
            "Thermal conductivity of boron nitride–epoxy composites",
            "single-column layout"),
    )


def two_column_article() -> Document:
    """Two-column research article: the layout of most physics and
    chemistry journals."""
    return Document(
        meta=_meta(title="Thermal conductivity of BN–epoxy composites",
                   author="A. Author, B. Coauthor, C. Reviewer",
                   column_count=2, body_font_pt=10,
                   packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"]),
        children=_article_body(
            "Thermal conductivity of boron nitride–epoxy composites",
            "two-column layout"),
    )


def three_column_document() -> Document:
    """Three-column version of the same article (multicols)."""
    return Document(
        meta=_meta(title="Thermal conductivity of BN–epoxy composites",
                   author="A. Author, B. Coauthor, C. Reviewer",
                   column_count=3, body_font_pt=10,
                   packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"]),
        children=_article_body(
            "Thermal conductivity of boron nitride–epoxy composites",
            "three-column layout"),
    )


# ---------------------------------------------------------------- math

def math_heavy() -> Document:
    """Short mathematical note: quadratics, with theorem, proof, worked
    example and a multivariable generalisation."""
    return Document(
        meta=_meta(title="Quadratic functions",
                   packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"]),
        children=[
            Title(children=[Text(text="Quadratic functions: completing the square")]),
            Author(children=[Text(text="A. Author")]),
            Abstract(children=[Text(text=
                "We derive the vertex form and the roots of a real "
                "quadratic function by completing the square, prove the "
                "discriminant test as a theorem, apply the results to a "
                "projectile problem, and show how the same idea locates "
                "the stationary point of a quadratic form in several "
                "variables.")]),
            Keywords(children=[Text(text=
                "quadratic function · discriminant · vertex form · "
                "quadratic form")]),

            _h("Definition and vertex form", label="sec:def"),
            _p("A real quadratic function is a polynomial of degree "
               "exactly two:"),
            MathBlock(latex="f(x) = a x^2 + b x + c, \\qquad a \\neq 0,",
                      numbered=True, label="eq:quad"),
            _p(
                "with real coefficients ", MathInline(latex="a"), ", ",
                MathInline(latex="b"), " and ", MathInline(latex="c"),
                ". Factor ", MathInline(latex="a"),
                " out of the first two terms of Eq. ",
                CrossRef(label="eq:quad", kind="eqref"),
                " and add and subtract ", MathInline(latex="(b/2a)^2"),
                " inside the bracket:",
            ),
            MathBlock(
                latex=(
                    "\\begin{align*}\n"
                    "  f(x) &= a\\left[\\left(x + \\tfrac{b}{2a}\\right)^2 "
                    "- \\tfrac{b^2}{4a^2}\\right] + c \\\\\n"
                    "       &= a\\left(x + \\tfrac{b}{2a}\\right)^2 "
                    "+ \\frac{4ac - b^2}{4a},\n"
                    "\\end{align*}"
                ),
            ),
            _p("that is,"),
            MathBlock(
                latex=("f(x) = a\\left(x + \\frac{b}{2a}\\right)^2 "
                       "- \\frac{\\Delta}{4a},"),
                numbered=True, label="eq:vertex",
            ),
            _p(
                "where ", MathInline(latex="\\Delta = b^2 - 4ac"),
                " is the discriminant. Equation ",
                CrossRef(label="eq:vertex", kind="eqref"),
                " is the vertex form: the graph of ", MathInline(latex="f"),
                " is a parabola with its vertex at ",
                MathInline(latex="x = -b/2a"), ", where ",
                MathInline(latex="f"), " takes the value ",
                MathInline(latex="-\\Delta/4a"),
                ". It is a minimum when ", MathInline(latex="a > 0"),
                " and a maximum when ", MathInline(latex="a < 0"), ".",
            ),

            _h("Roots and the discriminant", label="sec:roots"),
            Theorem(kind="theorem", title="Discriminant test", children=[
                Text(text="Let "), MathInline(latex="f"),
                Text(text=" be the quadratic function of Eq. "),
                CrossRef(label="eq:quad", kind="ref"),
                Text(text=". Then "), MathInline(latex="f(x) = 0"),
                Text(text=" has two distinct real roots if "),
                MathInline(latex="\\Delta > 0"),
                Text(text=", exactly one real root if "),
                MathInline(latex="\\Delta = 0"),
                Text(text=", and no real root if "),
                MathInline(latex="\\Delta < 0"),
                Text(text=". In every case the roots are given by the "
                          "quadratic formula."),
            ]),
            MathBlock(
                latex="x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}.",
                numbered=True, label="eq:formula",
            ),
            Theorem(kind="proof", children=[
                Text(text="Setting "), MathInline(latex="f(x) = 0"),
                Text(text=" in Eq. "),
                CrossRef(label="eq:vertex", kind="eqref"),
                Text(text=" gives "),
                MathInline(latex="\\left(x + \\tfrac{b}{2a}\\right)^2 = "
                                 "\\Delta / 4a^2"),
                Text(text=". A real square is never negative, so there is "
                          "no real solution when "),
                MathInline(latex="\\Delta < 0"),
                Text(text=", the single solution "),
                MathInline(latex="x = -b/2a"),
                Text(text=" when "), MathInline(latex="\\Delta = 0"),
                Text(text=", and two solutions "),
                MathInline(latex="x = -b/2a \\pm \\sqrt{\\Delta}/2a"),
                Text(text=" when "), MathInline(latex="\\Delta > 0"),
                Text(text=", which is Eq. "),
                CrossRef(label="eq:formula", kind="eqref"),
                Text(text="."),
            ]),
            _p(
                "Geometrically, the sign of ", MathInline(latex="\\Delta"),
                " tells whether the vertex lies on the same side of the "
                "x-axis as the parabola opens (no crossing), on the axis "
                "(tangent), or beyond it (two crossings). Table ",
                CrossRef(label="tab:cases", kind="ref"),
                " summarises the cases.",
            ),
            Table(
                rows=[
                    ["Discriminant", "Real roots", "Graph touches the x-axis"],
                    ["Δ > 0", "two, distinct", "at two points"],
                    ["Δ = 0", "one, repeated", "tangent at the vertex"],
                    ["Δ < 0", "none (complex pair)", "never"],
                ],
                caption="Number of real roots according to the sign of the discriminant.",
                label="tab:cases",
                alignment="lll",
                header=True,
            ),

            _h("A worked example: a thrown ball", label="sec:example"),
            _p(
                "A ball is thrown vertically upwards at ",
                MathInline(latex="v_0 = 12\\ \\mathrm{m/s}"),
                " from a height ", MathInline(latex="h_0 = 1.5\\ \\mathrm{m}"),
                ". With ", MathInline(latex="g = 9.81\\ \\mathrm{m/s^2}"),
                " its height at time ", MathInline(latex="t"), " is",
            ),
            MathBlock(
                latex="h(t) = h_0 + v_0 t - \\tfrac{1}{2} g t^2 "
                      "= -4.905\\,t^2 + 12\\,t + 1.5,",
                numbered=True, label="eq:ball",
            ),
            _p(
                "a quadratic with ", MathInline(latex="a = -4.905"), ", ",
                MathInline(latex="b = 12"), " and ",
                MathInline(latex="c = 1.5"),
                ". The vertex gives the highest point:",
            ),
            MathBlock(
                latex=("t^\\ast = \\frac{v_0}{g} \\approx 1.22\\ \\mathrm{s},"
                       "\\qquad h(t^\\ast) = h_0 + \\frac{v_0^2}{2g} "
                       "\\approx 8.84\\ \\mathrm{m}."),
            ),
            _p(
                "The ball lands when ", MathInline(latex="h(t) = 0"),
                ". Here ", MathInline(latex="\\Delta = 12^2 + 4 \\cdot 4.905 "
                                           "\\cdot 1.5 \\approx 173.4 > 0"),
                ", so there are two real roots; the negative one is "
                "unphysical and the other is",
            ),
            MathBlock(
                latex=("t = \\frac{-12 - \\sqrt{173.4}}{2(-4.905)} "
                       "\\approx 2.57\\ \\mathrm{s}."),
            ),

            _h("Several variables", label="sec:multi"),
            _p(
                "Completing the square also locates the stationary point "
                "of a quadratic form. For a real symmetric matrix ",
                MathInline(latex="A"), ", a vector ",
                MathInline(latex="\\mathbf{b}"), " and a scalar ",
                MathInline(latex="c"), ", consider",
            ),
            MathBlock(
                latex=("q(\\mathbf{x}) "
                       "= \\mathbf{x}^\\top A \\mathbf{x} "
                       "+ 2 \\mathbf{b}^\\top \\mathbf{x} + c."),
                numbered=True, label="eq:qform",
            ),
            _p(
                "If ", MathInline(latex="A"),
                " is invertible, ", MathInline(latex="q"),
                " has a unique stationary point at ",
                MathInline(latex="\\mathbf{x}^\\ast = -A^{-1}\\mathbf{b}"),
                ", where it takes the value ",
                MathInline(latex="c - \\mathbf{b}^\\top A^{-1}\\mathbf{b}"),
                ". The stationary point is a minimum when ",
                MathInline(latex="A"),
                " is positive definite. For example, in two variables with",
            ),
            MathBlock(
                latex=("A = \\begin{pmatrix} 2 & 1 \\\\ 1 & 3 \\end{pmatrix},"
                       "\\quad \\mathbf{b} = \\begin{pmatrix} -1 \\\\ 2 "
                       "\\end{pmatrix},\\quad c = 0,"),
            ),
            _p(
                "we have ", MathInline(latex="\\det A = 5 > 0"),
                " and ", MathInline(latex="\\operatorname{tr} A = 5 > 0"),
                ", so ", MathInline(latex="A"),
                " is positive definite and ",
                MathInline(latex="\\mathbf{x}^\\ast = -A^{-1}\\mathbf{b} = "
                                 "(1.0,\\,-1.0)^\\top"),
                ". The one-variable case of Eq. ",
                CrossRef(label="eq:qform", kind="eqref"),
                " is ", MathInline(latex="A = [a]"), ", ",
                MathInline(latex="\\mathbf{b} = [b/2]"),
                ", and recovers the vertex of Section ",
                CrossRef(label="sec:def", kind="ref"), ".",
            ),

            _h("Summary", label="sec:summary"),
            _p(
                "Completing the square turns a quadratic into its vertex "
                "form, Eq. ", CrossRef(label="eq:vertex", kind="eqref"),
                ", from which the quadratic formula and the "
                "discriminant test follow in one line each. The same "
                "step gives the highest point of a thrown ball and "
                "generalises to quadratic forms in several variables.",
            ),
        ],
    )
