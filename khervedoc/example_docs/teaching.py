"""Lab report, problem set, lecture notes, review and proposal."""
from __future__ import annotations

from ..model import (
    Abstract, Author, Citation, CrossRef, DEFAULT_PACKAGES, Document,
    Footnote, InlineRaw, Keywords, MathBlock, MathInline, Paragraph,
    RawLatex, Section, Table, Text, Theorem, Title,
)
from ..example_helpers import _items, _meta, _ord_items, _p


def _sec(text: str, level: int = 1, label: str | None = None) -> Section:
    return Section(level=level, children=[Text(text=text)], label=label)


def _m(latex: str) -> MathInline:
    return MathInline(latex=latex)


def _thm(kind: str, *runs, title: str = "", start: bool = True) -> Theorem:
    children = []
    for r in runs:
        if isinstance(r, str):
            r = Text(text=r)
        elif isinstance(r, tuple):
            r = Text(text=r[0], marks=list(r[1]))
        children.append(r)
    return Theorem(kind=kind, title=title, children=children, start=start)


def _bib(*entries: tuple[str, str]) -> RawLatex:
    body = "\n".join(f"\\bibitem[{lab}]{{{k}}} {t}" for k, lab, t in entries)
    return RawLatex(text="\\begin{thebibliography}{99}\n" + body
                         + "\n\\end{thebibliography}")


# ------------------------------------------------------------- lab report

def lab_report() -> Document:
    """Undergraduate lab report: objective, theory, apparatus, procedure,
    data, analysis with uncertainties, discussion and conclusion."""
    return Document(
        meta=_meta(
            title="Speed of sound by resonance tube",
            author="A. Student",
            body_font_pt=12,
            line_spacing=1.15,
        ),
        children=[
            Title(children=[Text(text="Determination of the speed of sound "
                                      "in air by the resonance-tube "
                                      "method")]),
            Author(children=[Text(text="A. Student — PHYS 2010, Group 4B, "
                                       "14 October 2026")]),
            Abstract(children=[Text(text=
                "The speed of sound in air was measured with a "
                "closed resonance tube and three tuning forks (256, 440 "
                "and 512 Hz). From the spacing of the first two "
                "resonances at each frequency we obtain "
                "v = 341.6 ± 0.8 m/s at 21.3 °C, 0.8% below the accepted "
                "value of 344.2 m/s. The end correction measured "
                "independently, 1.2 cm, is close to the theoretical "
                "0.6 r = 1.0 cm.")]),

            _sec("Objective"),
            _p("To measure the speed of sound in air at room temperature "
               "from the resonance lengths of a tube closed at one end "
               "and driven by tuning forks of known frequency, and to "
               "compare the result with the accepted value."),

            _sec("Theory"),
            _p("A tube closed at one end supports standing waves when the "
               "air column is an odd number of quarter wavelengths long. "
               "For the ", _m("n"), "-th resonance (",
               _m(r"n = 1, 3, 5, \ldots"),
               ") the measured column length ", _m("L_n"),
               " satisfies"),
            MathBlock(latex=r"L_n + \varepsilon = \frac{n\lambda}{4},"
                            r"\qquad \lambda = \frac{v}{f},",
                      numbered=True, label="eq:resonance"),
            _p("where ", _m(r"\varepsilon \approx 0.6\,r"),
               " is the end correction for a tube of inner radius ",
               _m("r"), " and ", _m("f"),
               " is the fork frequency. Subtracting the first resonance "
               "from the second one (", _m("n = 3"),
               ") removes the unknown end correction:"),
            MathBlock(latex=r"v = 2f\,(L_3 - L_1).",
                      numbered=True, label="eq:speed"),
            _p("The accepted speed of sound in dry air depends on the "
               "temperature ", _m("T"), " in degrees Celsius as"),
            MathBlock(latex=r"v_{\mathrm{ref}} \approx 331.3 + 0.606\,T"
                            r"\;\text{m/s}.",
                      numbered=True, label="eq:vref"),

            _sec("Apparatus"),
            _items(
                "Glass resonance tube, 100 cm long, inner diameter "
                "3.4 cm, connected to an adjustable water reservoir",
                "Tuning forks of 256, 440 and 512 Hz (calibrated "
                "to ±0.5 Hz) and a rubber mallet",
                "Metre rule (±0.5 mm)",
                "Digital thermometer (±0.1 °C)",
            ),

            _sec("Procedure"),
            _ord_items(
                "Record the room temperature and pressure.",
                "Strike the 256 Hz fork and hold it above the open end "
                "of the tube.",
                "Lower the water level slowly until the first loud "
                "resonance is heard, and record its length L1.",
                "Continue lowering the water until the second resonance "
                "and record L3.",
                "Repeat the pair of readings three times.",
                "Repeat the whole procedure with the 440 Hz and 512 Hz "
                "forks.",
            ),

            _sec("Results"),
            _p("The room temperature was ", _m(r"T = 21.3 \pm 0.1"),
               " °C and the pressure 1013 hPa. The measured resonance "
               "lengths are listed in Table ",
               CrossRef(label="tab:data"), "."),
            Table(
                rows=[
                    ["Fork (Hz)", "Trial", "L1 (cm)", "L3 (cm)"],
                    ["256", "1", "31.8", "98.2"],
                    ["256", "2", "31.6", "98.0"],
                    ["256", "3", "31.9", "98.4"],
                    ["440", "1", "18.2", "57.3"],
                    ["440", "2", "18.4", "57.1"],
                    ["440", "3", "18.3", "57.4"],
                    ["512", "1", "15.6", "49.0"],
                    ["512", "2", "15.5", "48.8"],
                    ["512", "3", "15.7", "49.1"],
                ],
                caption="Resonance lengths measured with three tuning "
                        "forks (reading uncertainty ±0.1 cm).",
                label="tab:data", alignment="rrrr", header=True,
            ),

            _sec("Analysis"),
            _p("The three trials at each frequency were averaged and "
               "inserted in Equation ", CrossRef(label="eq:speed",
                                                 kind="eqref"),
               ". For the 256 Hz fork, ",
               _m(r"\bar L_1 = 31.77"), " cm and ",
               _m(r"\bar L_3 = 98.20"), " cm, so"),
            MathBlock(latex=r"v_{256} = 2 \times 256\,\mathrm{Hz} \times "
                            r"(0.9820 - 0.3177)\,\mathrm{m} = "
                            r"340.1\;\text{m/s}."),
            _p("The uncertainty of each speed combines the scatter of the "
               "three trials (standard error of the mean) in "
               "quadrature. The results for all forks, together with the "
               "end correction ", _m(r"\varepsilon = \lambda/4 - L_1"),
               " obtained from Equation ",
               CrossRef(label="eq:resonance", kind="eqref"),
               ", are given in Table ", CrossRef(label="tab:results"), "."),
            Table(
                rows=[
                    ["Fork (Hz)", "v (m/s)", "Epsilon (cm)"],
                    ["256", "340.1 ± 0.7", "1.45"],
                    ["440", "342.9 ± 0.9", "1.18"],
                    ["512", "341.7 ± 1.1", "1.08"],
                    ["Mean", "341.6 ± 0.8", "1.24"],
                ],
                caption="Speed of sound and end correction for each "
                        "tuning fork.",
                label="tab:results", alignment="rrr", header=True,
            ),
            _p("The mean is ", _m(r"v = 341.6 \pm 0.8"),
               " m/s, where the uncertainty is the standard error of the "
               "three fork values. Equation ",
               CrossRef(label="eq:vref", kind="eqref"),
               " gives ", _m(r"v_{\mathrm{ref}} = 344.2"),
               " m/s at 21.3 °C, so our result is 2.6 m/s (0.8%) lower."),

            _sec("Discussion"),
            _p("The measured end correction (1.2 cm on average) agrees "
               "with the theoretical value ",
               _m(r"0.6\,r = 1.0"),
               " cm for a tube of radius 1.7 cm, which supports the "
               "quarter-wave model of Equation ",
               CrossRef(label="eq:resonance", kind="eqref"),
               ". The remaining 0.8% deficit is larger than the "
               "statistical uncertainty, so a systematic effect is "
               "likely. The most probable cause is the temperature of "
               "the air inside the tube, which is cooled by the water "
               "column and may be a degree or so below the room "
               "temperature (", _m(r"\Delta v \approx 0.6"),
               " m/s per kelvin). Humidity, which raises the speed of "
               "sound slightly, was not measured.",
               Footnote(children=[Text(text=
                   "Moist air is less dense than dry air, so the speed of "
                   "sound rises by about 0.3 m/s at 50% relative humidity "
                   "and 21 °C.")]),
               ),

            _sec("Conclusion"),
            _p("The speed of sound at 21.3 °C was found to be ",
               _m(r"341.6 \pm 0.8"),
               " m/s, within 1% of the accepted value of 344.2 m/s. The "
               "end correction agrees with theory. Measuring the "
               "temperature inside the tube and the humidity would "
               "reduce the systematic error in a repeat of the "
               "experiment."),
        ],
    )


# --------------------------------------------------------------- homework

def homework() -> Document:
    """Problem set with points per problem, theorem-style statements and
    solutions written as proofs.

    Kept in the article class: the exam class only offers raw
    \\question lists, which the visual tab would show as code."""
    return Document(
        meta=_meta(
            title="Problem set 7",
            author="A. Student",
            body_font_pt=11,
            line_spacing=1.15,
            paragraph_indent=False,
        ),
        children=[
            Title(children=[Text(text="MATH 3120 Linear Algebra and "
                                      "Analysis: Problem Set 7")]),
            Author(children=[Text(text="A. Student — due 27 November 2026 "
                                       "(40 points)")]),

            _sec("Problem 1 (10 points)"),
            _thm("lemma",
                 "Let ", _m("V"), " be a finite-dimensional inner-product "
                 "space over ", _m(r"\mathbb{C}"), " and let ",
                 _m(r"T\colon V \to V"), " be self-adjoint. Then every "
                 "eigenvalue of ", _m("T"), " is real."),
            _p(("Solution.", ["bold"]), " Let ", _m(r"Tv = \lambda v"),
               " with ", _m(r"v \neq 0"),
               ". Using linearity of the inner product in the first slot "
               "and conjugate-linearity in the second,"),
            MathBlock(
                latex=(r"\lambda\langle v,v\rangle = \langle Tv,v\rangle "
                       r"= \langle v,Tv\rangle "
                       r"= \bar\lambda\langle v,v\rangle,"),
                numbered=True, label="eq:selfadj"),
            _p("where the middle equality is self-adjointness. Since ",
               _m(r"\langle v,v\rangle > 0"), ", equation ",
               CrossRef(label="eq:selfadj", kind="eqref"),
               " gives ", _m(r"\lambda = \bar\lambda"), ", that is ",
               _m(r"\lambda \in \mathbb{R}"), "."),

            _sec("Problem 2 (10 points)"),
            _p("Evaluate the Dirichlet integral"),
            MathBlock(latex=r"I = \int_0^{\infty}\frac{\sin x}{x}\,dx.",
                      numbered=True, label="eq:sinc"),
            _p(("Solution.", ["bold"]),
               " Introduce a convergence factor and define"),
            MathBlock(latex=r"F(s) = \int_0^{\infty}\frac{e^{-sx}\sin x}"
                            r"{x}\,dx,\qquad s>0,",
                      numbered=True, label="eq:laplace"),
            _p("so that ", _m(r"I = \lim_{s\to 0^+}F(s)"),
               ". Differentiating under the integral sign (justified by "
               "dominated convergence for ", _m("s>0"), ") gives"),
            MathBlock(latex=r"F'(s) = -\int_0^{\infty}e^{-sx}\sin x\,dx"
                            r" = -\frac{1}{1+s^2}."),
            _p("Hence ", _m(r"F(s) = C - \arctan s"),
               ". Since ", _m(r"|F(s)| \le \int_0^\infty e^{-sx}\,dx = "
                              r"1/s \to 0"),
               " as ", _m(r"s\to\infty"), ", we get ",
               _m(r"C = \pi/2"), " and therefore"),
            MathBlock(latex=r"I = F(0^+) = \frac{\pi}{2}.",
                      numbered=True, label="eq:sinc-result"),

            _sec("Problem 3 (10 points)"),
            _p("Determine all groups of order 6 up to isomorphism."),
            _p(("Solution.", ["bold"]), " Let ", _m("G"),
               " be a group with ", _m(r"|G| = 6"),
               ". By Sylow's third theorem the number ", _m("n_3"),
               " of Sylow 3-subgroups divides 2 and satisfies ",
               _m(r"n_3 \equiv 1 \pmod 3"),
               ", so ", _m("n_3 = 1"), " and the subgroup ",
               _m(r"N \cong \mathbb{Z}/3"), " is normal. By Cauchy's "
               "theorem there is an element ", _m("t"),
               " of order 2, and ", _m(r"G = N\rtimes\langle t\rangle"),
               ". The action of ", _m("t"), " on ", _m("N"),
               " is an automorphism of ", _m(r"\mathbb{Z}/3"),
               " of order dividing 2, and there are exactly two such "
               "automorphisms:"),
            _items(
                "the trivial action, which gives the direct product "
                "and so ",
                "inversion, which gives the symmetric group ",
            ),
            _p("These give ", _m(r"\mathbb{Z}/3\times\mathbb{Z}/2"
                                r"\cong\mathbb{Z}/6"), " and ",
               _m("S_3"), ", which are not isomorphic because the first "
               "is abelian. Hence there are exactly two groups of "
               "order 6."),

            _sec("Problem 4 (10 points)"),
            _thm("lemma",
                 "Let ", _m(r"f\colon[0,1]\to\mathbb{R}"),
                 " be continuous with ",
                 _m(r"\int_0^1 f(x)\,x^n\,dx = 0"), " for all integers ",
                 _m(r"n\ge 0"), ". Then ", _m(r"f\equiv 0"), "."),
            _p(("Solution.", ["bold"]),
               " By linearity the hypothesis gives ",
               _m(r"\int_0^1 f\,p\,dx = 0"), " for every polynomial ",
               _m("p"), ". Given ", _m(r"\varepsilon>0"),
               ", the Weierstrass approximation theorem provides a "
               "polynomial ", _m("p"), " with ",
               _m(r"\|f-p\|_\infty<\varepsilon"), ". Then"),
            MathBlock(
                latex=(r"\int_0^1 f^2\,dx = \int_0^1 f\,(f-p)\,dx "
                       r"\le \|f\|_\infty\,\varepsilon."),
                numbered=False),
            _p("Letting ", _m(r"\varepsilon\to 0"), " gives ",
               _m(r"\int_0^1 f^2 = 0"), ". As ", _m("f^2"),
               " is continuous and non-negative, ", _m(r"f\equiv 0"),
               ". ", _m(r"\square")),
        ],
    )


# ---------------------------------------------------------- lecture notes

def lecture_notes() -> Document:
    """Lecture notes with real Theorem blocks: definitions, theorems,
    proofs and examples."""
    return _with_theorem_blocks(_lecture_notes_source())


def _with_theorem_blocks(doc: Document) -> Document:
    """Turn any theorem-like environment still written as a LaTeX
    RawLatex block into editable Theorem paragraphs."""
    import re
    from ..importers import import_body_fragment
    out = []
    for b in doc.children:
        if isinstance(b, RawLatex) and re.match(
                r"\s*\\begin\{(theorem|lemma|proposition|corollary|"
                r"definition|example|remark|proof)\}", b.text):
            out.extend(import_body_fragment(b.text))
        else:
            out.append(b)
    doc.children = out
    return doc


def _lecture_notes_source() -> Document:
    lab = lambda s: InlineRaw(latex=f"\\label{{{s}}}")  # noqa: E731
    return Document(
        meta=_meta(
            title="Metric Spaces: Lecture 12",
            author="Prof. A. Lecturer",
            body_font_pt=11,
            line_spacing=1.15,
            packages=DEFAULT_PACKAGES + ["hyperref"],
        ),
        children=[
            Title(children=[Text(text="MATH 4200 Metric Spaces")]),
            Author(children=[Text(text="Prof. A. Lecturer — Lecture 12: "
                                       "Compactness")]),

            _sec("Compactness"),
            _p("Compactness is one of the central ideas of analysis and "
               "topology. A compact set behaves like a finite set in "
               "several important ways: continuous functions attain their "
               "extrema on it, sequences in it have convergent "
               "subsequences, and every open cover can be reduced to a "
               "finite one. Throughout, ", _m("(X,d)"),
               " is a metric space and ", _m("B(p,r)"),
               " denotes the open ball of radius ", _m("r"),
               " about ", _m("p"), "."),

            _sec("Definitions", 2),
            _thm("definition",
                 "An ", ("open cover", ["italic"]), " of a set ",
                 _m(r"K\subseteq X"), " is a family ",
                 _m(r"\{U_\alpha\}_{\alpha\in A}"),
                 " of open sets with ",
                 _m(r"K\subseteq\bigcup_{\alpha\in A}U_\alpha"), ".",
                 title="Open cover"),
            _thm("definition",
                 "A set ", _m("K"), " is ", ("compact", ["italic"]),
                 " if every open cover of ", _m("K"),
                 " has a finite subcover.", title="Compact set"),
            _p("Compactness is intrinsic: it depends only on the metric "
               "induced on ", _m("K"), ", not on the ambient space ",
               _m("X"), "."),

            _sec("First properties", 2),
            _thm("theorem",
                 "Every compact subset of a metric space is closed and "
                 "bounded."),
            _thm("proof",
                 "Let ", _m("K"), " be compact. Fix ", _m(r"p\in X"),
                 ". The balls ", _m(r"B(p,n)"), ", ", _m(r"n\ge1"),
                 ", cover ", _m("K"),
                 ", so finitely many of them do, and ",
                 _m(r"K\subseteq B(p,N)"), " for some ", _m("N"),
                 ". Hence ", _m("K"), " is bounded."),
            _thm("proof",
                 "To see that ", _m("K"), " is closed, let ",
                 _m(r"q\notin K"), " and put ", _m(r"r_x = d(x,q)/2"),
                 " for ", _m(r"x\in K"),
                 ". The balls ", _m(r"B(x,r_x)"), " cover ", _m("K"),
                 "; choose a finite subcover ",
                 _m(r"B(x_1,r_1),\dots,B(x_n,r_n)"),
                 ". Then ", _m(r"B(q,\min_i r_i)"),
                 " misses every ball of the subcover, hence misses ",
                 _m("K"), ". So ", _m(r"X\setminus K"),
                 " is open.", start=False),
            _thm("remark",
                 "The converse fails in general: the closed unit ball of "
                 "an infinite-dimensional normed space is closed and "
                 "bounded but not compact. In ", _m(r"\mathbb{R}^n"),
                 " it does hold."),

            _sec("The Heine–Borel theorem", 2),
            _thm("theorem",
                 "A subset of ", _m(r"\mathbb{R}^n"),
                 " is compact if and only if it is closed and bounded.", title="Heine–Borel"),
            _p("The proof (see the textbook, Chapter 4, §3) rests on the "
               "following lemma."),
            _thm("lemma",
                 "Every bounded sequence in ", _m(r"\mathbb{R}^n"),
                 " has a convergent subsequence.",
                 title="Bolzano–Weierstrass"),
            _thm("proof",
                 "Take ", _m("n=1"), ". A bounded sequence ", _m("(x_k)"),
                 " lies in some interval ", _m("[a,b]"),
                 ". One of the halves ", _m("[a,(a+b)/2]"), " and ",
                 _m("[(a+b)/2,b]"),
                 " contains infinitely many terms; keep it and pick a "
                 "term from it. Repeating this produces nested closed "
                 "intervals whose lengths tend to zero, so they share a "
                 "single point ", _m(r"\ell"),
                 ", and the chosen terms converge to ", _m(r"\ell"), "."),
            _thm("proof",
                 "For ", _m(r"\mathbb{R}^n"),
                 " apply the one-dimensional argument to the coordinates "
                 "one after another, passing to a subsequence each time.",
                 start=False),

            _sec("Compactness and continuity", 2),
            _thm("proposition",
                 "If ", _m("K"), " is compact and ",
                 _m(r"f\colon K\to Y"), " is continuous, then ",
                 _m("f(K)"), " is compact."),
            _thm("proof",
                 "Let ", _m(r"\{V_\alpha\}"), " be an open cover of ",
                 _m("f(K)"), ". The sets ", _m(r"f^{-1}(V_\alpha)"),
                 " are open and cover ", _m("K"),
                 ", so finitely many of them do; the corresponding ",
                 _m(r"V_\alpha"), " cover ", _m("f(K)"), "."),
            _thm("theorem",
                 "Let ", _m("K"), " be a non-empty compact set and ",
                 _m(r"f\colon K\to\mathbb{R}"),
                 " continuous. Then ", _m("f"),
                 " attains its maximum and minimum on ", _m("K"), ".", title="Extreme value theorem"),
            _thm("proof",
                 "By the proposition, ", _m("f(K)"),
                 " is compact in ", _m(r"\mathbb{R}"),
                 ", hence closed and bounded by the Heine–Borel "
                 "theorem. A non-empty bounded set has a supremum, and a closed "
                 "set contains it, so the maximum is attained. The "
                 "minimum is handled in the same way."),

            _sec("Examples", 2),
            _thm("example",
                 "The closed disc ",
                 _m(r"D=\{(x,y): x^2+y^2\le1\}"),
                 " is compact. It is bounded, and closed as the preimage "
                 "of ", _m(r"(-\infty,1]"),
                 " under the continuous map ", _m(r"(x,y)\mapsto x^2+y^2"),
                 ". Apply the Heine–Borel theorem."),
            _thm("example",
                 "The interval ", _m("(0,1]"),
                 " is bounded but not compact: the open sets ",
                 _m(r"U_n=(1/n,\,2)"),
                 " cover it, but no finite subfamily does, since a finite "
                 "union is just the largest ", _m("U_n"),
                 ", which misses points near 0."),

            _sec("Exercises", 2),
            _ord_items(
                "Prove that a finite union of compact sets is compact.",
                "Show that a closed subset of a compact set is compact.",
                "Let K be compact and f: K → R continuous. Prove that f is "
                "uniformly continuous on K.",
                "Give a closed, bounded subset of the metric space "
                "(Q, |x − y|) that is not compact.",
            ),
        ],
    )


# ------------------------------------------------------ literature review

def literature_review() -> Document:
    """Literature review: thematic sections, author-year citations, a
    summary table and a bibliography."""
    return Document(
        meta=_meta(
            title="Machine learning for materials discovery",
            author="A. Researcher",
            body_font_pt=12,
            line_spacing=1.3,
            packages=DEFAULT_PACKAGES + ["natbib", "hyperref"],
        ),
        children=[
            Title(children=[Text(text="Machine learning for materials "
                                      "discovery: a literature review")]),
            Author(children=[Text(text="A. Researcher — Materials "
                                       "Science, Somewhere")]),
            Abstract(children=[Text(text=
                "This review surveys machine-learning methods for the "
                "discovery of inorganic crystalline materials, in work "
                "published between 2016 and 2026. We organise the "
                "literature into three themes (property prediction, "
                "generative design and active learning), compare "
                "representative methods and their reported accuracy, and "
                "identify four open challenges: scarce experimental "
                "data, uncertainty quantification, multi-objective "
                "design and reproducibility.")]),
            Keywords(children=[Text(text="machine learning · materials "
                "discovery · graph neural networks · generative models · "
                "active learning")]),

            _sec("Introduction", label="sec:intro"),
            _p("Finding a material with a target combination of "
               "properties is a search problem over an enormous space of "
               "compositions and structures. Early statistical models "
               "mapped hand-built descriptors to properties ",
               Citation(keys=["varga2016", "lindqvist2018"],
                        style="citep"),
               "; the field has since added generative models that "
               "propose new compounds ",
               Citation(keys=["okafor2019", "brandt2021"], style="citep"),
               " and active-learning loops that choose the next "
               "experiment ", Citation(keys=["moreau2020"], style="citep"),
               ". The review is restricted to inorganic crystals; "
               "molecular and polymer systems are surveyed elsewhere ",
               Citation(keys=["haddad2022"], style="citep"), "."),
            _p("Section ", CrossRef(label="sec:prediction"),
               " covers property prediction, Section ",
               CrossRef(label="sec:generative"),
               " generative design and Section ",
               CrossRef(label="sec:active"),
               " active learning. Section ",
               CrossRef(label="sec:challenges"),
               " closes with the open challenges."),

            _sec("Property prediction", label="sec:prediction"),
            _p("The most mature theme is supervised learning of a "
               "property from a structure. Early models used composition "
               "and elemental statistics as features ",
               Citation(keys=["varga2016"], style="citep"),
               ", whereas later ones learn a representation directly "
               "from the crystal graph, with atoms as nodes and "
               "interatomic distances as edge features ",
               Citation(keys=["lindqvist2018", "tanaka2019"],
                        style="citep"), "."),
            _p(Citation(keys=["lindqvist2018"], style="citet"),
               " reported a mean absolute error of 0.04 eV/atom for "
               "formation energy on a public database of about "
               "50 000 DFT calculations, and ",
               Citation(keys=["tanaka2019"], style="citet"),
               " lowered it further with edge updates (Table ",
               CrossRef(label="tab:methods"), ")."),
            Table(
                rows=[
                    ["Theme", "Method", "Task", "Result"],
                    ["Prediction", "Crystal graph net",
                     "Formation energy", "MAE 0.04 eV/atom"],
                    ["Prediction", "Edge-update graph net",
                     "Formation energy", "MAE 0.03 eV/atom"],
                    ["Generation", "Variational autoencoder",
                     "Valid structures", "fraction 0.40"],
                    ["Generation", "Diffusion model",
                     "Valid structures", "fraction 0.75"],
                    ["Active learning", "Bayesian optimisation",
                     "Experiments needed", "3x fewer than grid"],
                ],
                caption="Representative methods and the results reported "
                        "by the cited studies.",
                label="tab:methods", header=True,
                alignment="llll",
            ),
            _p("Two limitations persist. First, almost all training data "
               "are DFT values that carry systematic errors relative to "
               "experiment. Second, accuracy degrades for chemistries "
               "far from the training set ",
               Citation(keys=["bergstrom2021"], style="citep"), "."),

            _sec("Generative design", label="sec:generative"),
            _p("Generative models propose structures instead of scoring "
               "given ones. Variational autoencoders were applied first ",
               Citation(keys=["okafor2019"], style="citep"),
               ", followed by adversarial networks and, more recently, "
               "diffusion models ",
               Citation(keys=["brandt2021"], style="citep"),
               ". The central difficulty is synthesisability. ",
               Citation(keys=["brandt2021"], style="citet"),
               " conditioned generation on distance to the convex hull "
               "of formation energies, so that proposed compounds are "
               "close to thermodynamic stability."),

            _sec("Active learning", label="sec:active"),
            _p("Active learning closes the loop between model and "
               "laboratory by selecting the measurement with the highest "
               "expected information gain. ",
               Citation(keys=["moreau2020"], style="citet"),
               " used a Gaussian-process surrogate to find a target alloy "
               "composition with three times fewer experiments than a "
               "grid search. Multi-fidelity variants mix cheap DFT "
               "evaluations with costly measurements ",
               Citation(keys=["nakamura2022"], style="citep"), "."),

            _sec("Open challenges", label="sec:challenges"),
            _items(
                "Experimental (as opposed to computed) data remain "
                "scarce and unevenly reported.",
                "Uncertainty estimates for neural models are rarely "
                "calibrated.",
                "Balancing stability, cost, toxicity and performance "
                "in one design objective is little explored.",
                "Few studies release both code and data, which "
                "prevents end-to-end reproduction.",
            ),

            _sec("Conclusion"),
            _p("Machine learning already speeds up screening and "
               "guides experiments. The next step is likely to be "
               "closed-loop laboratories in which prediction, "
               "synthesis and characterisation update one another "
               "automatically, provided that uncertainty is treated "
               "properly."),
            _bib(
                ("varga2016", "Varga and Ito(2016)",
                 "Varga, P. and Ito, K. (2016). Composition-based "
                 "prediction of formation energies. \\emph{Journal of "
                 "Example Materials Informatics}, 2(1):10--24."),
                ("lindqvist2018", "Lindqvist et al.(2018)",
                 "Lindqvist, E., Osei, N. and Park, J. (2018). Crystal "
                 "graph networks for property prediction. \\emph{Journal "
                 "of Example Materials Informatics}, 4(3):201--219."),
                ("okafor2019", "Okafor and Reyes(2019)",
                 "Okafor, C. and Reyes, L. (2019). Latent-space "
                 "generation of inorganic compounds. \\emph{Example "
                 "Proceedings on Learning for Science}, 112--121."),
                ("tanaka2019", "Tanaka and Weiss(2019)",
                 "Tanaka, S. and Weiss, M. (2019). Edge-updated graph "
                 "networks for crystals. \\emph{Journal of Example "
                 "Materials Informatics}, 5(2):77--95."),
                ("moreau2020", "Moreau et al.(2020)",
                 "Moreau, A., Singh, R. and Kovacs, T. (2020). Adaptive "
                 "search for shape-memory alloys. \\emph{Example Alloys "
                 "Letters}, 8:455--468."),
                ("brandt2021", "Brandt et al.(2021)",
                 "Brandt, H., Mensah, K. and Li, Y. (2021). Diffusion "
                 "models for stable crystal generation. \\emph{Example "
                 "Proceedings on Learning for Science}, 301--314."),
                ("bergstrom2021", "Bergstr\\\"om and Nair(2021)",
                 "Bergstr\\\"om, F. and Nair, D. (2021). Extrapolation "
                 "limits of learned materials models. \\emph{Journal of "
                 "Example Materials Informatics}, 7(1):1--18."),
                ("haddad2022", "Haddad(2022)",
                 "Haddad, Z. (2022). Machine learning for molecules and "
                 "polymers: a survey. \\emph{Example Reviews in "
                 "Chemistry}, 15:88--130."),
                ("nakamura2022", "Nakamura and Fox(2022)",
                 "Nakamura, H. and Fox, G. (2022). Multi-fidelity "
                 "acquisition for materials experiments. \\emph{Example "
                 "Alloys Letters}, 10:12--29."),
            ),
        ],
    )


# ------------------------------------------------------ research proposal

def research_proposal() -> Document:
    """Research proposal: summary, background with citations, aims,
    methodology, timeline, risks and budget."""
    return Document(
        meta=_meta(
            title="Research proposal",
            author="Dr A. Researcher",
            body_font_pt=12,
            line_spacing=1.15,
            packages=DEFAULT_PACKAGES + ["natbib", "hyperref"],
        ),
        children=[
            Title(children=[Text(text="Bias-tailored quantum error "
                                      "correction for superconducting "
                                      "circuits")]),
            Author(children=[Text(text="Dr A. Researcher — Quantum "
                                       "Engineering, Somewhere")]),

            _sec("Project summary"),
            _p("We request £335k over 36 months to design, simulate and "
               "demonstrate quantum error-correcting codes tailored to "
               "the biased noise of transmon qubits. The expected "
               "outcomes are (i) a code family that needs fewer physical "
               "qubits than the surface code at the same logical error "
               "rate, (ii) a decoder fast enough for real-time feedback, "
               "and (iii) an experimental demonstration on a 20-qubit "
               "device."),

            _sec("Background and motivation"),
            _p("Fault-tolerant quantum computing needs error correction ",
               Citation(keys=["almeida2015", "ngo2017"], style="citep"),
               ". The surface code ",
               Citation(keys=["ngo2017"], style="citep"),
               " is the leading candidate because of its high threshold "
               "and local checks, but it needs of the order of ",
               _m("d^2"), " physical qubits per logical qubit at code "
               "distance ", _m("d"),
               ", which is too many for near-term devices."),
            _p("When one type of error dominates, for example dephasing "
               "in transmons, the noise is described by the bias ",
               _m(r"\eta = p_Z/p_X"),
               ". Codes that exploit a large ", _m(r"\eta"),
               " can reach a given logical error rate with far fewer "
               "qubits ", Citation(keys=["hartmann2020", "iyer2023"],
                                   style="citep"),
               ". This project takes those theoretical results to the "
               "laboratory. Below threshold the logical error rate "
               "follows the usual scaling"),
            MathBlock(latex=r"p_L \approx A\left(\frac{p}{p_{\mathrm{th}}}"
                            r"\right)^{\lceil d/2\rceil},",
                      numbered=True, label="eq:scaling"),
            _p("where ", _m("p"), " is the physical error rate, ",
               _m(r"p_{\mathrm{th}}"), " the threshold and ", _m("A"),
               " a constant of order one. Raising ",
               _m(r"p_{\mathrm{th}}"),
               " through bias is the lever we use."),

            _sec("Aims and objectives"),
            _ord_items(
                "Design stabiliser codes optimised for the noise of "
                "state-of-the-art transmons.",
                "Build an open-source decoder with a latency below "
                "1 microsecond per syndrome round.",
                "Implement the best code on a 20-qubit device and "
                "measure the logical error rate at distances 3, 5 and 7.",
                "Benchmark it against the surface code under identical "
                "hardware conditions.",
            ),

            _sec("Methodology"),
            _sec("Code construction", 2),
            _p("A computer search over CSS codes, parameterised by the "
               "bias ", _m(r"\eta"),
               ", will minimise the number of physical qubits ",
               _m("n"), " subject to a target ",
               _m(r"p_L"), " from Equation ",
               CrossRef(label="eq:scaling", kind="eqref"), "."),
            _sec("Decoder design", 2),
            _p("We will adapt the union-find decoder ",
               Citation(keys=["fischer2021"], style="citep"),
               " with a weighted growth rule that expands clusters "
               "unequally along the two error types, reducing the number "
               "of growth steps and the decoding time."),
            _sec("Experimental validation", 2),
            _p("Each code instance will be run for ", _m("10^6"),
               " syndrome rounds on the 20-qubit device in our "
               "laboratory, and the logical error rate extracted from "
               "repeated stabiliser measurements. The schedule is in "
               "Table ", CrossRef(label="tab:timeline"), "."),

            _sec("Timeline"),
            Table(
                rows=[
                    ["Period", "Milestone"],
                    ["Months 1–6", "Code enumeration and simulation"],
                    ["Months 7–12", "Decoder implementation and "
                                    "simulated benchmarks"],
                    ["Months 13–18", "Device calibration and distance-3 "
                                     "experiments"],
                    ["Months 19–30", "Experimental campaign at "
                                     "distances 3, 5 and 7"],
                    ["Months 31–36", "Analysis, publication and "
                                     "software release"],
                ],
                caption="Proposed timeline.", label="tab:timeline",
                alignment="lp{9cm}", header=True,
            ),

            _sec("Risks"),
            _items(
                "Device coherence below specification: mitigated by "
                "running the first campaign at distance 3, which needs "
                "only 17 qubits.",
                "Decoder latency above budget: a fallback lookup-table "
                "decoder is sufficient at distance 3.",
            ),

            _sec("Budget"),
            Table(
                rows=[
                    ["Item", "Cost (£k)"],
                    ["Postdoctoral researcher (36 months)", "180"],
                    ["PhD student (36 months)", "90"],
                    ["Cryostat maintenance", "40"],
                    ["Consumables and travel", "25"],
                    ["Total", "335"],
                ],
                caption="Budget summary.", label="tab:budget",
                alignment="lr", header=True,
            ),

            _sec("Expected impact"),
            _p("The project will show whether bias-tailored codes give a "
               "practical route to lower-overhead error correction. The "
               "decoder and simulation tools will be released openly, "
               "and the experimental data will serve as a benchmark for "
               "future code designs."),
            _bib(
                ("almeida2015", "Almeida and Voss(2015)",
                 "Almeida, R. and Voss, E. (2015). A primer on quantum "
                 "error correction. \\emph{Example Quantum Reviews}, "
                 "3:1--40."),
                ("ngo2017", "Ngo et al.(2017)",
                 "Ngo, T., Haas, B. and Lund, C. (2017). Topological "
                 "codes with local checks. \\emph{Example Quantum "
                 "Reviews}, 5:101--130."),
                ("hartmann2020", "Hartmann and Osei(2020)",
                 "Hartmann, J. and Osei, K. (2020). Codes for "
                 "asymmetric noise. \\emph{Journal of Example Quantum "
                 "Information}, 6(2):55--72."),
                ("fischer2021", "Fischer et al.(2021)",
                 "Fischer, M., Dube, S. and Ramos, P. (2021). Almost "
                 "linear-time decoding of topological codes. "
                 "\\emph{Journal of Example Quantum Information}, "
                 "7(4):300--318."),
                ("iyer2023", "Iyer and Cho(2023)",
                 "Iyer, V. and Cho, H. (2023). Fewer qubits for biased "
                 "noise. \\emph{Example Quantum Reviews}, 11:15--44."),
            ),
        ],
    )


def exam_paper() -> Document:
    """A short test in the exam class: questions with points, parts, a
    points table and the solutions, which print when the class option
    `answers` is set."""
    meta = _meta(title="Physics 101 — Midterm Test", author="",
                 documentclass="exam", class_options="12pt",
                 body_font_pt=12, line_spacing=1.0)
    meta.preamble_extras = (
        "\\addpoints\n\\pagestyle{headandfoot}\n\\pointsinrightmargin\n"
        "\\pointpoints{point}{points}\n"
        "\\firstpageheader{Physics 101}{Midterm Test}{Autumn 2026}\n"
        "\\runningheader{Physics 101}{Midterm Test}{Page \\thepage\\ of "
        "\\numpages}\n"
        "\\firstpagefooter{}{}{}\n"
        "\\runningfooter{}{}{}")
    return Document(meta=meta, children=[
        RawLatex(text=(
            "\\begin{center}\\fbox{\\fbox{\\parbox{0.85\\textwidth}{"
            "\\centering Answer every question. Show your working: most of "
            "the marks are for the method. You have 50 minutes. Calculators "
            "are allowed; take $g = 9.81\\,\\mathrm{m\\,s^{-2}}$.}}}"
            "\\end{center}\n"
            "\\vspace{0.5em}\n"
            "\\makebox[\\textwidth]{Name:\\enspace\\hrulefill}\n"
            "\\vspace{0.5em}\n"
            "\\begin{center}\\gradetable[h][questions]\\end{center}")),
        RawLatex(text=(
            "\\begin{questions}\n"
            "\\question A ball is thrown straight up at "
            "$12\\,\\mathrm{m\\,s^{-1}}$ from the edge of a cliff "
            "$20\\,\\mathrm{m}$ high and lands at the foot of the cliff.\n"
            "\\begin{parts}\n"
            "\\part[2] How high above the cliff edge does it rise?\n"
            "\\begin{solution}$h = v^2/2g = 144/19.62 = 7.34\\,\\mathrm{m}$."
            "\\end{solution}\n"
            "\\part[4] How long is it in the air?\n"
            "\\begin{solution}Solve $-20 = 12t - 4.905t^2$: "
            "$t = (12 + \\sqrt{144 + 392.4})/9.81 = 3.58\\,\\mathrm{s}$."
            "\\end{solution}\n"
            "\\end{parts}\n"
            "\\question[4] A $2.0\\,\\mathrm{kg}$ block slides from rest down "
            "a frictionless slope of height $1.5\\,\\mathrm{m}$. Find its speed "
            "at the bottom and say which conservation law you used.\n"
            "\\begin{solution}Energy is conserved: "
            "$v = \\sqrt{2gh} = \\sqrt{29.43} = 5.42\\,\\mathrm{m\\,s^{-1}}$, "
            "whatever the mass.\\end{solution}\n"
            "\\question Two resistors, $6\\,\\Omega$ and $3\\,\\Omega$, "
            "are connected in parallel across a $9\\,\\mathrm{V}$ battery.\n"
            "\\begin{parts}\n"
            "\\part[2] What is their combined resistance?\n"
            "\\begin{solution}$R = (1/6 + 1/3)^{-1} = 2\\,\\Omega$."
            "\\end{solution}\n"
            "\\part[3] What current does the battery supply, and how is it "
            "shared?\n"
            "\\begin{solution}$I = 9/2 = 4.5\\,\\mathrm{A}$: "
            "$1.5\\,\\mathrm{A}$ through $6\\,\\Omega$ and "
            "$3.0\\,\\mathrm{A}$ through $3\\,\\Omega$.\\end{solution}\n"
            "\\end{parts}\n"
            "\\question[5] Explain, in two or three sentences, why a "
            "satellite in a circular orbit is accelerating although its "
            "speed does not change.\n"
            "\\begin{solution}Acceleration is the rate of change of "
            "velocity, a vector. The direction of the velocity turns "
            "continuously towards the centre, so there is a centripetal "
            "acceleration $v^2/r$ supplied by gravity.\\end{solution}\n"
            "\\makeemptybox{5em}\n"
            "\\end{questions}")),
    ])
