"""A short paper for each journal class: amsart, llncs, acmart, sn-jnl, mnras, apa7, scrartcl."""
from __future__ import annotations

from ..model import (
    Abstract, Affiliation, Author, Citation, Correspondence, CrossRef,
    DEFAULT_PACKAGES, Document, Footnote, Keywords, List as ListNode,
    ListItem, MathBlock, MathInline, Paragraph, RawLatex, Section, Table,
    Text, Theorem, Title,
)
from ..example_helpers import _items, _meta, _ord_items, _p


def _sec(text, level=1, label=None):
    return Section(level=level, children=[Text(text=text)], label=label)


def _m(latex):
    return MathInline(latex=latex)


def _eq(latex, label=None):
    return MathBlock(latex=latex, numbered=label is not None, label=label)


def _thm(kind, *runs, title="", start=True):
    p = _p(*runs)
    return Theorem(kind=kind, title=title, children=p.children, start=start)


# The stand-in keyword environment puts a space before each separator;
# define it here with \unskip so the commas sit against the words.
_KEYWORD_ENV = (
    "\\newenvironment{keyword}{\\par\\medskip\\noindent"
    "\\textbf{Keywords:}\\enspace\\def\\sep{\\unskip, }}{\\par\\medskip}")


def _ref(label, kind="ref"):
    return CrossRef(label=label, kind=kind)


def _bib(*entries):
    """thebibliography from (key, text) pairs; a key written 'key|label'
    gives the natbib optional label (author-year styles)."""
    lines = []
    for k, t in entries:
        if "|" in k:
            k, lab = k.split("|", 1)
            lines.append(f"\\bibitem[{lab}]{{{k}}} {t}")
        else:
            lines.append(f"\\bibitem{{{k}}} {t}")
    return RawLatex(text="\\begin{thebibliography}{99}\n" + "\n".join(lines)
                         + "\n\\end{thebibliography}")


# ================================================================ amsart

def _gap_rows():
    lam = 1 / 3
    rows = [["b", "Geometric mean", "Refined bound", "Arithmetic mean"]]
    for b in (0.25, 2, 4, 8, 16):
        gm = b ** (1 - lam)
        ref = gm + min(lam, 1 - lam) * (1 - b ** 0.5) ** 2
        am = lam + (1 - lam) * b
        rows.append([f"{b:g}", f"{gm:.4f}", f"{ref:.4f}", f"{am:.4f}"])
    return rows


def amsart_paper() -> Document:
    """Short mathematics paper in the AMS article class."""
    return Document(
        meta=_meta(
            documentclass="amsart", class_options="11pt",
            title="A sharpened weighted arithmetic-geometric mean inequality",
            author="N. Varga",
            line_spacing=1.0, paragraph_indent=True,
            packages=DEFAULT_PACKAGES + ["hyperref"],
            preamble_extras=(
                "\\subjclass[2020]{Primary 26D15; Secondary 26D20}\n"
                "\\keywords{arithmetic-geometric mean inequality, Young's "
                "inequality, convexity}\n"
                "\\address{Department of Mathematics, University of "
                "Northfield, Northfield NF1 2AB, Examplia}\n"
                "\\email{n.varga@example.org}"),
        ),
        children=[
            Title(children=[Text(text=
                "A sharpened weighted arithmetic-geometric mean "
                "inequality")]),
            Author(children=[Text(text="N. Varga")]),
            Abstract(children=[Text(text=
                "We prove a two-term refinement of the weighted "
                "arithmetic-geometric mean inequality in which the error "
                "term is a multiple of the squared difference of the "
                "square roots of the two numbers, and we show that "
                "equality holds only in the trivial cases. The argument "
                "uses nothing beyond the classical inequality itself. As "
                "a corollary we obtain a sharpened form of Young's "
                "inequality.")]),

            _sec("Introduction", label="sec:intro"),
            _p("For positive real numbers ", _m("a"), " and ", _m("b"),
               " and a weight ", _m(r"\lambda\in[0,1]"),
               " the weighted arithmetic-geometric mean inequality states "
               "that"),
            _eq(r"a^{\lambda}b^{1-\lambda}\le \lambda a+(1-\lambda)b,",
                "eq:amgm"),
            _p("with equality for ", _m(r"0<\lambda<1"), " exactly when ",
               _m("a=b"), ". It follows at once from the concavity of the "
               "logarithm, and it is the usual route to Young's inequality "
               "for products. Refinements of ", _ref("eq:amgm", "eqref"),
               " that add a non-negative term to the left-hand side "
               "were studied by several authors ",
               Citation(keys=["hale21", "ito19"]),
               ". The purpose of this note is to give a short proof of one "
               "such refinement, with a complete discussion of the cases of "
               "equality."),
            _p("Throughout, ", _m(r"r(\lambda)=\min\{\lambda,\,1-\lambda\}"),
               "."),

            _sec("The main result", label="sec:main"),
            _p("For ", _m("a,b>0"), " and ", _m(r"0<\lambda<1"),
               " we compare the two sides of"),
            _eq(r"a^{\lambda}b^{1-\lambda}+r(\lambda)\left(\sqrt a-\sqrt b"
                r"\right)^{2}\le \lambda a+(1-\lambda)b.", "eq:main"),
            _thm("theorem", "The inequality ", _ref("eq:main", "eqref"),
                 " holds for all ", _m("a,b>0"), " and all ",
                 _m(r"0<\lambda<1"), ".", title="Refined mean inequality"),
            _thm("theorem", "If moreover ", _m(r"\lambda\neq\tfrac12"),
                 ", equality holds in ", _ref("eq:main", "eqref"),
                 " if and only if ", _m("a=b"), "."),
            _thm("proof",
                 "Both sides of ", _ref("eq:main", "eqref"),
                 " are unchanged when ", _m("(a,\\lambda)"), " and ",
                 _m("(b,1-\\lambda)"), " are exchanged, so we may assume ",
                 _m(r"\lambda\le\tfrac12"), ", that is ",
                 _m(r"r(\lambda)=\lambda"),
                 ". Expanding the square gives ",
                 _m(r"\lambda a+(1-\lambda)b-\lambda(\sqrt a-\sqrt b)^{2}"
                    r"=(1-2\lambda)\,b+2\lambda\sqrt{ab}"),
                 ". The right-hand side is a weighted arithmetic mean of ",
                 _m("b"), " and ", _m(r"\sqrt{ab}"), " with weights ",
                 _m(r"1-2\lambda"), " and ", _m(r"2\lambda"),
                 ", which are non-negative and add up to 1. By ",
                 _ref("eq:amgm", "eqref"), " it is at least ",
                 _m(r"b^{1-2\lambda}(\sqrt{ab})^{2\lambda}"
                    r"=b^{1-2\lambda}(ab)^{\lambda}=a^{\lambda}b^{1-\lambda}"),
                 ", which is the first claim. For the second claim let ",
                 _m(r"0<\lambda<\tfrac12"),
                 ". Then both weights are positive, so equality in the "
                 "last step forces ", _m(r"b=\sqrt{ab}"), ", that is ",
                 _m("a=b"), "; conversely both sides of ",
                 _ref("eq:main", "eqref"), " equal ", _m("a"),
                 " when ", _m("a=b"), ". The case ",
                 _m(r"\lambda>\tfrac12"), " follows by symmetry."),
            _thm("remark", "For ", _m(r"\lambda=\tfrac12"),
                 " the inequality ", _ref("eq:main", "eqref"),
                 " is an identity, since ",
                 _m(r"\tfrac12(a+b)-\tfrac12(\sqrt a-\sqrt b)^{2}"
                    r"=\sqrt{ab}"), ". The weight ",
                 _m(r"\tfrac12"), " is therefore the only one for which "
                 "the refinement uses up the whole gap."),

            _sec("A numerical illustration", label="sec:numbers"),
            _p("Table ", _ref("tab:gap"), " compares the three quantities "
               "in the main theorem for ", _m(r"\lambda=\tfrac13"),
               " and ", _m("a=1"), ". The refined lower bound is "
               "always at most the arithmetic mean, and it recovers more "
               "of the gap as ", _m("b"), " moves away from ", _m("a"),
               "."),
            Table(
                rows=_gap_rows(),
                caption=("Weighted means for a = 1 and weight 1/3: the "
                         "geometric mean, the refined bound and the "
                         "arithmetic mean."),
                label="tab:gap", alignment="rrrr", style="booktabs",
                header=True),

            _sec("A sharpened Young inequality", label="sec:young"),
            _p("Let ", _m("p,q>1"), " with ", _m(r"\tfrac1p+\tfrac1q=1"),
               " and ", _m("x,y>0"), ". We claim that"),
            _eq(r"xy+\min\{\tfrac1p,\tfrac1q\}"
                r"\left(x^{p/2}-y^{q/2}\right)^{2}"
                r"\le \frac{x^{p}}{p}+\frac{y^{q}}{q}.", "eq:young"),
            _thm("corollary", "Inequality ", _ref("eq:young", "eqref"),
                 " holds for all such ", _m("p,q,x,y"), ".",
                 title="Sharpened Young inequality"),
            _thm("proof", "Apply the main theorem with ", _m(r"a=x^{p}"), ", ",
                 _m(r"b=y^{q}"), " and ", _m(r"\lambda=1/p"),
                 ". Then ", _m(r"a^{\lambda}b^{1-\lambda}=xy"),
                 ", because ", _m(r"1-\lambda=1/q"), ", and ",
                 _m(r"r(\lambda)=\min\{1/p,1/q\}"), "."),
            _p("When ", _m("p=q=2"), " the corollary reads ",
               _m(r"xy+\tfrac12(x-y)^{2}\le\tfrac12(x^{2}+y^{2})"),
               ", which is an equality, in agreement with the Remark "
               "above.", Footnote(children=[Text(text=
                   "This is the identity ")] + [
                   _m(r"(x-y)^{2}=x^{2}-2xy+y^{2}"), Text(text=".")]),
               ),

            Section(level=1, numbered=False,
                    children=[Text(text="Acknowledgement")]),
            _p("The author thanks the participants of the Northfield "
               "inequalities seminar for helpful comments."),
            _bib(
                ("hale21", "L. Hale and P. Okonkwo, \\emph{Remainder terms "
                 "for classical mean inequalities}, J. Example Anal. "
                 "\\textbf{14} (2021), no.~2, 101--117."),
                ("ito19", "K. Ito, \\emph{A note on Young-type "
                 "inequalities}, Ann. Fictional Math. \\textbf{7} (2019), "
                 "55--62."),
            ),
        ],
    )


# ================================================================ llncs

def _fp_rows():
    rows = [["f (bits)", "FPR bound (per cent)", "Filter, bits/key", "Bloom, bits/key"]]
    import math
    for f in (8, 12, 16):
        eps = 8 / (2 ** f - 1)
        rows.append([str(f), f"{eps * 100:.3f}", f"{f / 0.95:.2f}",
                     f"{1.44 * math.log2(1 / eps):.2f}"])
    return rows


def llncs_paper() -> Document:
    """Springer LNCS conference paper (computer science)."""
    return Document(
        meta=_meta(
            documentclass="llncs", title="Compact fingerprint filters",
            author="M. Marren",
            body_font_pt=10, line_spacing=1.0, paragraph_indent=True,
            packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"],
            preamble_extras=_KEYWORD_ENV + "\n\\bibliographystyle{splncs04}",
        ),
        children=[
            Title(children=[Text(text=
                "Two-Choice Fingerprint Filters for Deduplicating "
                "Event Streams")]),
            Author(children=[Text(text="Tomas Marren and Sana Oduya")]),
            Affiliation(children=[Text(text=
                "Institute of Computing, University of Northfield, "
                "Northfield, Examplia")]),
            Affiliation(children=[Text(text=
                "Lowmoor Systems Lab, Lowmoor, Examplia")]),
            Correspondence(children=[Text(text=
                "Corresponding author: t.marren@example.org")]),
            Abstract(children=[Text(text=
                "Event pipelines must discard duplicate messages without "
                "keeping every identifier in memory. We describe a "
                "membership filter that stores short fingerprints in a "
                "table of small buckets, where each key may live in one "
                "of two buckets. We prove a closed-form bound on the "
                "false-positive rate, show that with 12-bit fingerprints "
                "the structure needs about 12.6 bits per key at 95% "
                "load, and report that a prototype drops 99.8% of "
                "synthetic duplicates at 2.1 million events per second "
                "on a single core.")]),
            Keywords(children=[Text(text=
                "approximate membership · hashing · stream processing")]),

            _sec("Introduction", label="sec:intro"),
            _p("A message broker that delivers at least once must remove "
               "duplicates before an event reaches a consumer. Keeping "
               "all identifiers in a hash set costs tens of bytes per "
               "key; an approximate filter answers the question ",
               ("have we seen this key?", ["italic"]),
               " in a few bits, at the price of a small chance of a false "
               "positive and no chance of a false negative. Bloom "
               "filters ", Citation(keys=["bloom70"]),
               " are the textbook answer, but they cannot delete a key, "
               "which a sliding window over a stream requires."),
            _p("Our contributions are:"),
            _items(
                "a fingerprint filter with two candidate buckets per key "
                "and a bounded eviction walk;",
                "a closed-form false-positive bound (Theorem 1) and its "
                "space cost in bits per key;",
                "an evaluation on synthetic click streams showing that "
                "the filter matches a Bloom filter in space while "
                "supporting deletion.",
            ),
            _p("Section ", _ref("sec:design"), " describes the design, "
               "Sect. ", _ref("sec:analysis"), " the analysis and Sect. ",
               _ref("sec:eval"), " the evaluation. Related designs are "
               "surveyed in ", Citation(keys=["fan14", "kaur18"]), "."),

            _sec("Design", label="sec:design"),
            _p("The filter is an array of ", _m("m"), " buckets with ",
               _m("b"), " slots each; a slot holds an ", _m("f"),
               "-bit fingerprint or is empty. For a key ", _m("x"),
               " let ", _m(r"\varphi(x)"), " be its non-zero fingerprint "
               "and ", _m("h(x)"), " a hash of the key. The two candidate "
               "buckets are"),
            _eq(r"i_1=h(x)\bmod m,\qquad "
                r"i_2=i_1\oplus h(\varphi(x))\bmod m,", "eq:buckets"),
            _p("so that either bucket can be recomputed from the other "
               "and the fingerprint alone. This symmetry lets an "
               "eviction move a stored fingerprint without knowing its "
               "key.", Footnote(children=[Text(text=
                   "The table size m is a power of two, so that the "
                   "exclusive or in the equation above stays inside "
                   "the table.")]),
               " Insertion places the fingerprint in a free slot of either "
               "bucket; if both are full, it evicts a random resident "
               "to its alternate bucket and repeats for at most 500 "
               "steps before the table is declared full."),

            _sec("Analysis", label="sec:analysis"),
            _p("A query for an absent key compares its fingerprint with "
               "the ", _m("2b"), " slots of its two buckets. We assume "
               "fingerprints are uniform on ", _m(r"\{1,\dots,2^f-1\}"),
               "."),
            _thm("theorem", "Let the filter store ", _m("n"),
                 " keys. For an absent key the probability of a false "
                 "positive is at most ", _m(r"2b/(2^{f}-1)"),
                 ", and the filter uses ", _m(r"f/\alpha"),
                 " bits per key at load factor ", _m(r"\alpha=n/(mb)"),
                 "."),
            _thm("proof", "The query is positive only if one of the ",
                 _m("2b"), " inspected slots holds the query's "
                 "fingerprint. Each slot is empty or holds a fingerprint "
                 "that matches the query's with probability at most ",
                 _m(r"1/(2^{f}-1)"),
                 ", so a union bound over the slots gives the first "
                 "claim. The table has ", _m("mb"), " slots of ", _m("f"),
                 " bits, and ", _m("mb=n/\\alpha"),
                 ", which gives the second."),
            _p("For ", _m("b=4"), " and ", _m(r"\alpha=0.95"),
               " the bound gives the figures in Table ",
               _ref("tab:space"), ". We compare against an optimally "
               "tuned Bloom filter, which needs ",
               _m(r"1.44\log_2(1/\varepsilon)"),
               " bits per key for a false-positive rate ",
               _m(r"\varepsilon"), "."),
            Table(
                rows=_fp_rows(),
                caption="False-positive bound and space for b = 4 and load 0.95.",
                label="tab:space", alignment="rrrr", style="booktabs",
                header=True),
            _p("Below a rate of about 0.2% the two structures need the "
               "same space; at looser rates a Bloom filter is smaller, "
               "but it cannot delete."),

            _sec("Evaluation", label="sec:eval"),
            _p("We implemented the filter in Rust and ran it on one "
               "core of a 3.2 GHz desktop processor. The workload is a "
               "synthetic click stream of 50 million events in which "
               "40% of the identifiers are repeats drawn from a "
               "sliding window of the last 4 million events."),
            Table(
                rows=[
                    ["Structure", "Memory (MB)", "Dropped (per cent)",
                     "Mevents/s"],
                    ["Hash set", "412.0", "100.0", "1.3"],
                    ["Bloom filter", "6.3", "99.8", "2.6"],
                    ["Fingerprint filter", "6.3", "99.8", "2.1"],
                ],
                caption="Deduplication of 20 million repeated events.",
                label="tab:eval", alignment="lrrr", style="booktabs",
                header=True),
            _p("Table ", _ref("tab:eval"), " shows that the filter "
               "matches the Bloom filter in memory and in the share of "
               "duplicates it drops, at a modest cost in throughput, "
               "and uses about 65 times less memory than the hash set. "
               "Unlike the Bloom filter it can expire old events by "
               "deleting them, which keeps the false-positive rate "
               "constant over a long stream."),

            _sec("Conclusion", label="sec:concl"),
            _p("Two-choice fingerprint filters give a Bloom-like space "
               "cost with deletion. Future work includes resizing the "
               "table online and a lock-free variant for multi-core "
               "brokers."),
            _bib(
                ("bloom70", "Bloom, B.H.: Space/time trade-offs in hash "
                 "coding with allowable errors. Commun. Example Mach. "
                 "\\textbf{13}(7), 422--426 (1970)"),
                ("fan14", "Fan, L., Roy, A., Thapa, V.: Fingerprint "
                 "tables for fast set membership. In: Proc. Example "
                 "Conf. on Networked Systems, pp. 75--88. Examplia (2014)"),
                ("kaur18", "Kaur, H., Lindqvist, E.: A survey of "
                 "approximate membership structures. Example Comput. "
                 "Surv. \\textbf{51}(2), 1--32 (2018)"),
            ),
        ],
    )


# ================================================================ acmart

def acmart_paper() -> Document:
    """ACM conference paper (sigconf) in human-computer interaction."""
    return Document(
        meta=_meta(
            documentclass="acmart", class_options="sigconf",
            title="Line height and reading speed on phones",
            author="R. Salgado",
            body_font_pt=10, line_spacing=1.0, paragraph_indent=True,
            packages=DEFAULT_PACKAGES + ["booktabs"],
            preamble_extras=(
                _KEYWORD_ENV + "\n"
                "\\setcopyright{none}\n"
                "\\settopmatter{printacmref=false}\n"
                "\\renewcommand\\footnotetextcopyrightpermission[1]{}\n"
                "\\acmConference[HCI Examples '27]{Example Conference on "
                "Human Factors in Computing}{May 2027}{Northfield, "
                "Examplia}\n"
                "\\ccsdesc[500]{Human-centered computing~Empirical "
                "studies in HCI}\n"
                "\\ccsdesc[300]{Human-centered computing~Smartphones}\n"
                "\\keywords{reading, typography, mobile devices, "
                "line spacing}"),
        ),
        children=[
            Title(children=[Text(text=
                "Does Generous Line Height Help? Reading Speed and "
                "Comfort on Phone Screens")]),
            Author(children=[Text(text="Rosa Salgado")]),
            Affiliation(children=[Text(text="University of Northfield")]),
            Author(children=[Text(text="Idris Ketterman")]),
            Affiliation(children=[Text(text="Lowmoor Design Studio")]),
            Abstract(children=[Text(text=
                "Phone interfaces often set body text with tight line "
                "spacing to fit more words on screen. We ran a "
                "within-subjects study with 36 participants who read "
                "three short articles, each set with a line height of "
                "1.2, 1.4 or 1.6 times the font size. Reading speed "
                "differed across conditions (F(2, 70) = 6.84, p = .002): "
                "the 1.4 setting was read about 5% faster than the "
                "tightest one, and participants rated it as most "
                "comfortable. Going from 1.4 to 1.6 brought no further "
                "gain. We discuss defaults for mobile reading "
                "interfaces.")]),

            _sec("Introduction", label="sec:intro"),
            _p("People read long texts on phones more than ever, yet "
               "layout defaults are tuned for screenshots rather than "
               "for reading. Line height is a cheap parameter to change: "
               "classic typographic advice favours generous leading for "
               "long lines ", Citation(keys=["brandt12"]),
               ", but phone lines are short, and the benefit is "
               "unclear. Prior work on small screens compared font "
               "sizes and column widths ", Citation(keys=["osei17"]),
               " rather than vertical spacing."),
            _p("We ask two questions:"),
            _ord_items(
                "Does line height change reading speed on a phone when "
                "comprehension is held constant?",
                "Which line height do readers prefer?",
            ),

            _sec("Related Work", label="sec:related"),
            _p("Studies of print typography found that very tight "
               "leading slows readers because the eye drifts to the "
               "neighbouring line ", Citation(keys=["brandt12"]),
               ". On screens the effect depends on line length: "
               "Lindgren and Aziz report that the optimum moves towards "
               "tighter spacing as lines get shorter ",
               Citation(keys=["lindgren15"]),
               ", which is the regime of phones. Work on mobile reading "
               "has focused on how text is delivered, for example "
               "rapid serial presentation, rather than on its static "
               "layout ", Citation(keys=["osei17", "nakano20"]),
               ". We complement it with a controlled test of one "
               "layout parameter."),

            _sec("Method", label="sec:method"),
            _sec("Participants and design", level=2),
            _p("We recruited 36 adults (20 women, 15 men, 1 not "
               "disclosed; ages 19 to 58, median 31) through a "
               "university mailing list. All read English as a first "
               "language and had normal or corrected vision. Each "
               "participant read three articles of about 450 words "
               "(Flesch reading ease 62 to 66) in one of the three "
               "line heights. Condition order and article assignment "
               "were counterbalanced with a Latin square."),
            _sec("Apparatus and procedure", level=2),
            _p("Texts were shown in a web page on a 6.1-inch phone at "
               "a 16 px serif font, with 32-character lines. "
               "Participants scrolled at their own pace; scroll events "
               "gave the reading time. After each article they "
               "answered four multiple-choice questions and rated "
               "comfort on a seven-point scale. Reading speed is "
               "words divided by reading time, ",
               _m(r"v=\frac{N}{t}\cdot 60"), ", in words per minute "
               "(wpm)."),
            _p("We analysed speed only for articles on which at least "
               "three of the four questions were answered correctly, "
               "which excluded 7 of 108 readings. The omnibus test "
               "was followed by paired comparisons with a Holm "
               "correction."),

            _sec("Results", label="sec:results"),
            _p("Comprehension was high and did not differ between "
               "conditions (about 3.4 of 4 questions in each). Mean "
               "reading speed is shown in Table ", _ref("tab:speed"),
               ". A repeated-measures ANOVA found a main effect of line "
               "height, ", _m(r"F(2,70)=6.84"), ", ", _m("p=.002"),
               ", ", _m(r"\eta_p^{2}=.16"), "."),
            Table(
                rows=[
                    ["Line height", "Speed (wpm)", "SD", "Comfort (1-7)"],
                    ["1.2", "231", "38", "4.6"],
                    ["1.4", "243", "41", "5.5"],
                    ["1.6", "240", "40", "5.2"],
                ],
                caption=("Mean reading speed and comfort by line height "
                         "(N = 36)."),
                label="tab:speed", alignment="lrrr", style="booktabs",
                header=True),
            _p("Relative to the 1.2 setting, the 1.4 setting was ",
               _m(r"(243-231)/231\approx 5\%"),
               " faster and the 1.6 setting ",
               _m(r"(240-231)/231\approx 4\%"),
               " faster. The two roomier settings did not differ from "
               "each other. Comfort followed the same order, and when "
               "asked to pick a favourite, 22 participants chose 1.4, "
               "9 chose 1.6 and 5 chose 1.2."),
            _p("Reading speed and comfort were only weakly related "
               "(Pearson ", _m("r=.21"), "), so the preference for "
               "1.4 is not simply a matter of reading faster."),

            _sec("Discussion", label="sec:disc"),
            _p("Our results support a modest increase over the tightest "
               "common setting. The gain is small in absolute terms, "
               "about 12 wpm, but it comes at the cost of roughly "
               "15% more vertical space and is free of any other "
               "interface change. We caution against extrapolating "
               "beyond short articles, 16 px type and 32-character "
               "lines; larger studies should vary these jointly. Our "
               "participants were also young and mostly university "
               "affiliated, and the three articles, although matched "
               "on length and difficulty, are a small sample of text."),
            _p("Design implications are straightforward:"),
            _items(
                "default to a line height near 1.4 for body text on "
                "phones;",
                "do not trade readability for density by going below "
                "1.2;",
                "offer the setting to readers with low vision, who "
                "were not part of our sample.",
            ),

            _sec("Conclusion", label="sec:concl"),
            _p("In a controlled study, a line height of 1.4 gave faster "
               "and more comfortable phone reading than 1.2, and 1.6 "
               "added nothing. We hope these numbers help practitioners "
               "set defensible defaults.", Footnote(children=[Text(text=
                   "Materials and anonymised data are available on "
                   "request from the first author.")])),
            _bib(
                ("brandt12", "Brandt, K. 2012. \\textit{Leading and "
                 "Legibility in Print}. Lowmoor Press, Lowmoor."),
                ("lindgren15", "Lindgren, E. and Aziz, N. 2015. Line "
                 "length and spacing on screens. \\textit{Proceedings of "
                 "the Example Symposium on Reading} (2015), 40--47."),
                ("nakano20", "Nakano, Y., Brook, T., and Adeyemi, F. "
                 "2020. Rapid serial presentation on small displays. "
                 "\\textit{Journal of Example Interfaces} 12, 1 (2020), "
                 "5--21."),
                ("osei17", "Osei, A. and Park, J. 2017. Font size and "
                 "column width for small-screen reading. "
                 "\\textit{Journal of Example Interfaces} 9, 3 (2017), "
                 "212--229."),
            ),
        ],
    )


# ============================================================ sn-jnl

def _wetland_rows():
    import math
    rows = [["Site", "In (mg/L)", "Out (mg/L)", "R (per cent)",
             "Residence (d)", "k (1/d)"]]
    for name, cin, cout, tau in (("A", 3.2, 1.9, 4.2), ("B", 4.8, 2.6, 5.1),
                                 ("C", 2.1, 1.5, 2.4)):
        r = (cin - cout) / cin
        k = -math.log(1 - r) / tau
        rows.append([name, f"{cin:.1f}", f"{cout:.1f}", f"{r * 100:.1f}",
                     f"{tau:.1f}", f"{k:.2f}"])
    return rows


def springer_nature_paper() -> Document:
    """Springer Nature journal article (sn-jnl), environmental science."""
    return Document(
        meta=_meta(
            documentclass="sn-jnl", class_options="sn-mathphys-num,pdflatex",
            title="Nitrate retention in restored headwater wetlands",
            author="E. Halvorsen",
            body_font_pt=10, line_spacing=1.0, paragraph_indent=True,
            packages=DEFAULT_PACKAGES + ["booktabs"],
            preamble_extras="\\AtBeginDocument{\\raggedbottom}",
            frontmatter_extras=(
                "\\author[1]{\\fnm{Elin} \\sur{Halvorsen}}\n"
                "\\author[2]{\\fnm{Kwame} \\sur{Boateng}}\n"
                "\\affil[1]{\\orgdiv{Department of Environmental Science}, "
                "\\orgname{University of Northfield}, \\city{Northfield}, "
                "\\country{Examplia}}\n"
                "\\affil[2]{\\orgname{Lowmoor Catchment Trust}, "
                "\\city{Lowmoor}, \\country{Examplia}}"),
        ),
        children=[
            Title(children=[Text(text=
                "Nitrate retention in restored headwater wetlands depends "
                "on residence time, not on wetland age")]),
            Abstract(children=[Text(text=
                "Restoring wetlands in agricultural headwaters is "
                "promoted as a way to cut nitrate export, but field "
                "evidence on how much they retain is mixed. We "
                "measured nitrate-nitrogen at the inlet and outlet of "
                "three restored wetlands over one hydrological year. "
                "Annual retention was 29 to 46% of inflow "
                "concentration. A first-order removal model with a "
                "single rate constant of 0.12 to 0.14 per day "
                "reproduced all three sites, which indicates that "
                "hydraulic residence time, rather than wetland age or "
                "area, controls retention. Managing outflow to "
                "lengthen residence time in the wet season is therefore "
                "the most direct lever for improving performance.")]),
            Keywords(children=[Text(text=
                "wetland restoration · nitrate · residence time · "
                "catchment management")]),

            _sec("Introduction", label="sec:intro"),
            _p("Nitrate leaching from fertilised fields degrades "
               "downstream water quality and drives eutrophication "
               "of estuaries ", Citation(keys=["lund16"]),
               ". Constructed and restored wetlands intercept "
               "drainage and remove nitrate by plant uptake and "
               "denitrification, the microbial reduction of nitrate "
               "to nitrogen gas. Reported removal ranges widely, from "
               "a few per cent to well over half of the inflowing "
               "load ", Citation(keys=["wei18", "lund16"]),
               ", and it is unclear which design variable explains "
               "the spread."),
            _p("Here we test whether a single parameter, the "
               "hydraulic residence time ", _m(r"\tau"),
               ", explains retention across three restored wetlands of "
               "different age and size in one catchment."),

            _sec("Methods", label="sec:methods"),
            _sec("Study sites", level=2),
            _p("The three wetlands (A to C) drain pasture and arable "
               "fields in a 14 km", ("2", ["superscript"]),
               " catchment. They were restored 3 years (A), 7 years "
               "(B) and 11 years (C) before the study, and cover "
               "0.8, 1.4 and 0.5 ha."),
            _sec("Sampling and analysis", level=2),
            _p("Inlet and outlet were sampled weekly from October to "
               "September with flow-proportional autosamplers. "
               "Nitrate-nitrogen was measured by ion chromatography, "
               "and flow by a calibrated V-notch weir. Residence time "
               "is the mean wetland water volume ", _m("V"),
               " divided by mean discharge ", _m("Q"), ". Retention "
               "is the relative drop in concentration,"),
            _eq(r"R=\frac{C_{\mathrm{in}}-C_{\mathrm{out}}}"
                r"{C_{\mathrm{in}}},\qquad \tau=\frac{V}{Q},",
                "eq:retention"),
            _p("and a plug-flow wetland with first-order removal "
               "predicts"),
            _eq(r"R=1-e^{-k\tau},\qquad "
                r"k=-\frac{\ln(1-R)}{\tau},", "eq:firstorder"),
            _p("where ", _m("k"), " is the removal rate "
               "constant in ", _m(r"\mathrm{d}^{-1}"), "."),

            _sec("Results", label="sec:results"),
            _p("All wetlands retained nitrate throughout the year, "
               "although retention fell during storm flows when ",
               _m(r"\tau"), " dropped below a day. Annual values are "
               "in Table ", _ref("tab:wetlands"), ". Retention "
               "ranged from 28.6% at site C to 45.8% at site B."),
            Table(
                rows=_wetland_rows(),
                caption=("Annual mean nitrate-nitrogen at inlet and "
                         "outlet, retention R, mean residence time "
                         "and rate constant k."),
                label="tab:wetlands", alignment="lrrrrr",
                style="booktabs", header=True),
            _p("Applying ", _ref("eq:firstorder", "eqref"),
               " to each site gives ", _m("k"), " between 0.12 and 0.14 ",
               _m(r"\mathrm{d}^{-1}"), ", a spread of less than 20% "
               "around the mean of 0.13, although the wetlands differ "
               "threefold in area and almost fourfold in age. Retention "
               "tracks residence time: the site with the longest ",
               _m(r"\tau"), " retained the most."),

            _sec("Discussion", label="sec:disc"),
            _p("The similar rate constants suggest that removal per "
               "unit time is a property of the catchment's "
               "temperature, carbon supply and flora, which the three "
               "sites share, rather than of the age of the wetland. "
               "This agrees with the view that wetland performance "
               "stabilises within a few years of restoration ",
               Citation(keys=["wei18"]), "."),
            _p("Two caveats apply. First, three sites cannot separate "
               "residence time from other site traits. Second, "
               "sampling was weekly, so short storm pulses are "
               "under-represented. Management implications are:"),
            _items(
                "keep outlets adjustable so that residence time can be "
                "raised in the wet season;",
                "design for a residence time above about 5 days, which "
                "gave 45% retention here;",
                "prioritise sites with a large share of the "
                "catchment's drainage over additional area.",
            ),

            _sec("Conclusions", label="sec:concl"),
            _p("Nitrate retention in three restored headwater "
               "wetlands followed a single first-order law in the "
               "residence time. Operating wetlands to maximise "
               "residence time is the most practical way to raise "
               "their performance.", Footnote(children=[Text(text=
                   "Retention is defined on concentrations; a load-based "
                   "estimate would also account for water lost to "
                   "evapotranspiration.")])),
            Section(level=1, numbered=False,
                    children=[Text(text="Acknowledgements")]),
            _p("We thank the landowners for access and the Lowmoor "
               "Catchment Trust for field support."),
            _bib(
                ("lund16", "Lundqvist, P., Mbeki, S.: Agricultural "
                 "nitrate and estuarine eutrophication. J. Example "
                 "Environ. Sci. \\textbf{24}, 311--325 (2016)"),
                ("wei18", "Wei, J., Santos, R., Dube, N.: Nitrate "
                 "removal by restored wetlands: a synthesis. Wetl. Ecol. "
                 "Examples \\textbf{9}, 77--94 (2018)"),
            ),
        ],
    )


# ================================================================ mnras

def mnras_paper() -> Document:
    """Monthly Notices of the Royal Astronomical Society letter-style paper."""
    return Document(
        meta=_meta(
            documentclass="mnras", class_options="fleqn,usenatbib",
            title="Starspot modulation of an M dwarf",
            author="I. Castellan",
            body_font_pt=10, line_spacing=1.0, paragraph_indent=True,
            packages=DEFAULT_PACKAGES + ["booktabs", "natbib"],
            preamble_extras=(
                "\\newenvironment{keyword}{\\begin{keywords}"
                "\\def\\sep{\\unskip; }}{\\end{keywords}}\n"
                "\\makeatletter\\let\\ktoldtable\\table"
                "\\let\\endktoldtable\\endtable"
                "\\renewenvironment{table}[1][]{\\ktoldtable}"
                "{\\endktoldtable}\\makeatother\n"
                "\\makeatletter\\AtBeginDocument{\\gdef\\@shortauthor"
                "{I. Castellan et al.}\\gdef\\@shorttitle{Starspot "
                "modulation of an M dwarf}}\\makeatother\n"
                "\\pubyear{2027}\n"
                "\\bibliographystyle{mnras}"),
        ),
        children=[
            Title(children=[Text(text=
                "Starspot modulation and the inclination of the young "
                "M dwarf KT 2134")]),
            Author(children=[
                Text(text="Irene Castellan, "), Text(text="1", marks=["superscript"]),
                Text(text=" Joao Marques, "), Text(text="1", marks=["superscript"]),
                Text(text=" Hana Okafor"), Text(text="2", marks=["superscript"])]),
            Affiliation(children=[
                Text(text="1", marks=["superscript"]),
                Text(text="Department of Physics and Astronomy, University "
                          "of Northfield, Northfield NF1 2AB, Examplia")]),
            Affiliation(children=[
                Text(text="2", marks=["superscript"]),
                Text(text="Lowmoor Observatory, Lowmoor, Examplia")]),
            Abstract(children=[
                Text(text="We analyse 27 d of space-based photometry of "
                     "the M dwarf KT 2134 and find a quasi-sinusoidal "
                     "modulation with a period of 2.41 "),
                _m(r"\pm"), Text(text=" 0.03 d and a peak-to-peak "
                     "amplitude of 1.8 per cent, which we attribute to "
                     "starspots carried round by stellar rotation. "
                     "Combining the period with a radius of 0.52 "),
                _m(r"\mathrm{R}_\odot"), Text(text=" and a projected "
                     "rotational velocity of 9.6 km s"),
                _m(r"^{-1}"), Text(text=" from high-resolution spectra, "
                     "we infer an equatorial velocity of 10.9 km s"),
                _m(r"^{-1}"), Text(text=" and an inclination of about 62"),
                _m(r"^{\circ}"), Text(text=". The fast rotation of a star "
                     "of 0.5 "), _m(r"\mathrm{M}_\odot"),
                Text(text=" points to an age of a few hundred Myr.")]),
            Keywords(children=[Text(text=
                "stars: rotation · stars: low-mass · starspots · "
                "techniques: photometric")]),

            _sec("Introduction", label="sec:intro"),
            _p("Low-mass stars spin down as they age, losing angular "
               "momentum through magnetised winds, so the rotation "
               "period of an M dwarf is a clock that can date a "
               "young field star ", Citation(keys=["varga19"], style="citep"),
               ". Dark starspots on the photosphere make the "
               "brightness vary with the rotation period, which is "
               "how most periods are measured ",
               Citation(keys=["moreau21"], style="citep"),
               ". If the radius is also known, the period gives the "
               "equatorial velocity, and comparison with the projected "
               "velocity ", _m(r"v\sin i"), " constrains the "
               "inclination ", _m("i"), " of the rotation axis, which "
               "matters for the orientation of any planetary system."),
            _p("KT 2134 is a nearby M dwarf with no published "
               "rotation period. We present its light curve and "
               "analyse it in this paper."),

            _sec("Observations", label="sec:obs"),
            _p("KT 2134 was observed continuously for 27 d at a "
               "2-min cadence. We used simple aperture photometry, "
               "removed points flagged for scattered light, and "
               "divided by a low-order polynomial fit per orbit. "
               "The resulting light curve has 17,420 points and a "
               "point-to-point scatter of 0.12 per cent. "
               "High-resolution spectra from a ground-based echelle "
               "spectrograph gave the stellar parameters in Table ",
               _ref("tab:star"), "."),
            Table(
                rows=[
                    ["Parameter", "Value"],
                    ["Effective temperature", "3450 ± 70 K"],
                    ["Radius", "0.52 ± 0.03 solar radii"],
                    ["Mass", "0.50 ± 0.04 solar masses"],
                    ["Projected rotation speed", "9.6 ± 0.8 km/s"],
                    ["Distance", "18.4 ± 0.2 pc"],
                ],
                caption="Adopted parameters of KT 2134.",
                label="tab:star", alignment="ll", style="booktabs",
                header=True),

            _sec("Rotation period", label="sec:period"),
            _p("We computed a Lomb--Scargle periodogram of the "
               "light curve. It has a single dominant peak at "
               "2.41 d with a false-alarm probability below ",
               _m(r"10^{-6}"), ", and a weaker peak at half that "
               "period, the harmonic expected from two spot groups on "
               "opposite hemispheres. Fitting a sinusoid to each "
               "half of the data gave 2.38 and 2.44 d, from which "
               "we adopt ", _m(r"P=2.41\pm0.03\,\mathrm{d}"), "."),
            _p("The amplitude changed by less than 10 per cent between "
               "the two halves, so the spot pattern was stable for "
               "about eleven rotations. This is typical of "
               "active M dwarfs, whose spots can live much longer "
               "than those on the Sun", Footnote(children=[Text(text=
                   "Individual solar spots last days to weeks.")]),
               " ", Citation(keys=["moreau21"], style="citep"), "."),

            _sec("Inclination", label="sec:incl"),
            _p("For a rigidly rotating star of radius ", _m("R"),
               " and period ", _m("P"),
               " the equatorial velocity is"),
            _eq(r"v_{\mathrm{eq}}=\frac{2\pi R}{P}"
                r"\simeq 50.6\,\frac{R/R_\odot}{P/\mathrm{d}}"
                r"\ \mathrm{km\,s^{-1}},", "eq:veq"),
            _p("which gives ", _m(r"v_{\mathrm{eq}}=10.9\,"
                                  r"\mathrm{km\,s^{-1}}"),
               " for our values. The projected velocity is "
               "smaller by a factor ", _m(r"\sin i"), ":"),
            _eq(r"\sin i=\frac{v\sin i}{v_{\mathrm{eq}}}"
                r"=\frac{9.6}{10.9}=0.88,", "eq:sini"),
            _p("so that ", _m(r"i\approx62^{\circ}"),
               ". Propagating the errors on ", _m("R"), ", ",
               _m("P"), " and ", _m(r"v\sin i"), " gives ",
               _m(r"\sin i=0.88^{+0.12}_{-0.09}"),
               ", which is consistent with an edge-on star "
               "at the 1-sigma level. The inclination is therefore "
               "poorly constrained and an edge-on geometry cannot be "
               "excluded."),

            _sec("Discussion and conclusions", label="sec:disc"),
            _p("A period of 2.4 d is short for a star of "
               "0.5 ", _m(r"\mathrm{M}_\odot"),
               ", since slow rotators in the field have periods "
               "of tens of days ", Citation(keys=["varga19"],
                                           style="citep"),
               ". This points to a young age, of the order of a few "
               "hundred Myr, although the calibration of M-dwarf "
               "ages is uncertain. Our main results are:"),
            _items(
                "KT 2134 rotates with a period of 2.41 d, stable over "
                "eleven rotations, with an uncertainty of 0.03 d;",
                "the equatorial velocity is 10.9 km/s, and the "
                "inclination is about 62 degrees but consistent with "
                "edge-on.",
            ),
            _p("Longer monitoring would show whether the spot pattern "
               "evolves, and a transit or radial-velocity search "
               "could test for planets aligned with the stellar "
               "equator."),
            Section(level=1, numbered=False,
                    children=[Text(text="Acknowledgements")]),
            _p("We thank the observers at Lowmoor Observatory. This "
               "work used public photometry from a fictional space "
               "mission."),
            Section(level=1, numbered=False,
                    children=[Text(text="Data availability")]),
            _p("The light curve and spectra are available from the "
               "corresponding author on reasonable request."),
            _bib(
                ("varga19|Lindqvist et~al.(2019)", "Lindqvist N., Dube K., "
                 "Hale L., 2019, J. Example Astron., 14, 101"),
                ("moreau21|Moreau et~al.(2021)", "Moreau C., Lund E., "
                 "Wei J., 2021, Example Astrophys. Lett., 3, 45"),
            ),
        ],
    )


# ================================================================ apa7

def _it(t):
    return (t, ["italic"])


def apa_paper() -> Document:
    """APA 7th edition student paper (psychology)."""
    return Document(
        meta=_meta(
            documentclass="apa7", class_options="man,natbib",
            title="Brief Expressive Writing and Test Anxiety",
            author="",
            body_font_pt=12, line_spacing=1.0, paragraph_indent=True,
            packages=DEFAULT_PACKAGES + ["booktabs"],
            frontmatter_extras=(
                "\\shorttitle{EXPRESSIVE WRITING AND TEST ANXIETY}\n"
                "\\authorsnames[1,1]{Maya Torrens, Samir Okonjo}\n"
                "\\authorsaffiliations{{Department of Psychology, "
                "University of Northfield}}\n"
                "\\leftheader{Torrens and Okonjo}\n"
                "\\authornote{Maya Torrens and Samir Okonjo, Department "
                "of Psychology, University of Northfield. Correspondence "
                "concerning this article should be addressed to Maya "
                "Torrens, Department of Psychology, University of "
                "Northfield, Northfield NF1 2AB, Examplia. Email: "
                "m.torrens@example.org}"),
        ),
        children=[
            Title(children=[Text(text=
                "Ten Minutes of Expressive Writing Before an Exam Reduces "
                "Test Anxiety in First-Year Students")]),
            Abstract(children=[Text(text=
                "Test anxiety impairs the performance of many "
                "students. Expressive writing about worries has been "
                "proposed as a brief intervention, but evidence from "
                "classroom settings is limited. In a randomized "
                "experiment, 96 first-year psychology students wrote "
                "for 10 min about their thoughts and feelings about an "
                "upcoming exam or about their morning routine. "
                "Students in the expressive writing condition reported "
                "lower test anxiety immediately before the exam than "
                "controls, with a medium effect. Exam scores were "
                "higher in the writing group, but the difference was "
                "not statistically significant. The results support "
                "short writing tasks as a low-cost way to reduce "
                "anxiety before assessments.")]),
            Keywords(children=[Text(text=
                "test anxiety · expressive writing · randomized "
                "experiment · higher education")]),

            _p("Test anxiety, the tendency to worry about evaluation "
               "and to feel tense before and during exams, is common "
               "among students and is associated with lower exam "
               "performance ", Citation(keys=["calder16"],
                                         style="citep"),
               ". Anxious students devote part of their working "
               "memory to worry, which leaves less capacity for the "
               "task itself ", Citation(keys=["nwosu18"], style="citep"),
               "."),
            _p("Expressive writing, in which people write about their "
               "deepest thoughts and feelings, offers a brief way to "
               "offload that worry. ",
               Citation(keys=["nwosu18"], style="citet"),
               " asked students to write before an exam and found "
               "better scores, but their sample came from a "
               "laboratory rather than a classroom. The present study "
               "tests the effect on anxiety and performance in a real "
               "course. We predicted that students who wrote about "
               "their exam worries would report less anxiety "
               "(Hypothesis 1) and obtain higher scores "
               "(Hypothesis 2) than students in a control condition."),

            Section(level=1, numbered=False,
                    children=[Text(text="Method")]),
            Section(level=2, numbered=False,
                    children=[Text(text="Participants")]),
            _p("Participants were 96 first-year students (",
               _it("M"), _m(r"_{\mathrm{age}}"), " = 19.2 years, ",
               _it("SD"), " = 1.4; 71% women) enrolled in an "
               "introductory psychology course at a large public "
               "university. They took part for course credit. A "
               "power analysis for a two-tailed independent-samples ",
               _it("t"), " test with ", _it("d"), " = 0.5, ",
               _m(r"\alpha=.05"), " and power of .80 gave a target of "
               "about 64 participants per group, so we enrolled 48 "
               "per group, as many as the course could provide, and "
               "accept a reduced power of about .68."),
            Section(level=2, numbered=False,
                    children=[Text(text="Materials and procedure")]),
            _p("Ten minutes before their first midterm, students "
               "were randomly assigned to one of two conditions. In "
               "the ", _it("expressive writing"), " condition they "
               "wrote about their thoughts and feelings about the "
               "exam; in the ", _it("control"), " condition they "
               "described their morning routine. Immediately afterward "
               "they completed the Test Anxiety Inventory, a 20-item "
               "scale with scores from 20 to 80. Higher scores mean "
               "more anxiety (Cronbach's ", _m(r"\alpha=.91"),
               " in this sample). The exam score was the percentage "
               "correct on the 60-item multiple-choice midterm."),
            Section(level=2, numbered=False,
                    children=[Text(text="Analysis")]),
            _p("Conditions were compared with independent-samples ",
               _it("t"), " tests. We report Cohen's ", _it("d"),
               ", computed with the pooled standard deviation,"),
            _eq(r"d=\frac{M_1-M_2}{s_p},\qquad "
                r"s_p=\sqrt{\frac{s_1^{2}+s_2^{2}}{2}},"),
            _p("which holds for groups of equal size."),

            Section(level=1, numbered=False,
                    children=[Text(text="Results")]),
            _p("Table ", _ref("tab:desc"), " shows the descriptive statistics. Test "
               "anxiety was lower in the expressive writing group "
               "(", _it("M"), " = 36.1, ", _it("SD"), " = 10.4) than "
               "in the control group (", _it("M"), " = 41.3, ",
               _it("SD"), " = 9.8), ", _it("t"), "(94) = 2.52, ",
               _it("p"), " = .013, ", _it("d"), " = 0.51, 95% CI "
               "[1.10, 9.30] for the difference. Hypothesis 1 was "
               "supported."),
            Table(
                rows=[
                    ["Measure", "Writing M", "Writing SD", "Control M",
                     "Control SD"],
                    ["Test anxiety (20-80)", "36.1", "10.4", "41.3",
                     "9.8"],
                    ["Exam score (percent correct)", "72.4", "11.2", "68.9", "12.0"],
                ],
                caption=("Descriptive statistics by condition (n = 48 per "
                         "group)."),
                label="tab:desc", alignment="lrrrr", style="booktabs",
                header=True, repeat_header=True),
            _p("Exam scores were higher in the expressive writing "
               "group, a difference of 3.5 percentage points, but it "
               "did not reach significance, ", _it("t"), "(94) = 1.48, ",
               _it("p"), " = .143, ", _it("d"), " = 0.30, 95% CI "
               "[", _m(r"-1.20"), ", 8.20]. Hypothesis 2 was not "
               "supported at the conventional level."),

            Section(level=1, numbered=False,
                    children=[Text(text="Discussion")]),
            _p("A single ten-minute writing task lowered self-reported "
               "test anxiety by about half a standard deviation. "
               "This is consistent with the idea that writing "
               "offloads worry ", Citation(keys=["nwosu18"],
                                          style="citep"),
               ". The effect on exam scores pointed in the expected "
               "direction but was small and uncertain, which fits "
               "our limited power; a larger trial would be needed "
               "to detect an effect of 0.3 standard deviations."),
            _p("The study has limitations. Participants came from a "
               "single course and were mostly women; anxiety was "
               "measured by self-report only; and students could "
               "not be blind to their condition. Instructors who wish "
               "to try the task need only set aside ten minutes before "
               "an exam", Footnote(children=[Text(text=
                   "Materials are available from the first author.")]),
               "."),
            _bib(
                ("calder16|Calder \\& Ibarra(2016)",
                 "Calder, R., \\& Ibarra, P. (2016). Test anxiety and "
                 "exam performance in undergraduates. \\textit{Journal "
                 "of Example Educational Psychology, 8}(2), 101--118."),
                ("nwosu18|Nwosu et~al.(2018)",
                 "Nwosu, C., Lindgren, E., \\& Haas, M. (2018). Writing "
                 "away worry before exams. \\textit{Example Psychological "
                 "Review, 12}(1), 33--47."),
            ),
        ],
    )


# ================================================================ scrartcl

def _figure_task_rows():
    tasks = [("Export data from the instrument", 0.5, 0.0),
             ("Re-plot with the new data", 1.5, 0.1),
             ("Restyle fonts and colours", 0.8, 0.1),
             ("Lay out the multi-panel figure", 0.5, 0.1),
             ("Check against the previous version", 0.2, 0.1)]
    rows = [["Task", "Before (h)", "After (h)"]]
    for name, a, b in tasks:
        rows.append([name, f"{a:.1f}", f"{b:.1f}"])
    rows.append(["Total per update", f"{sum(t[1] for t in tasks):.1f}",
                 f"{sum(t[2] for t in tasks):.1f}"])
    return rows


def koma_article() -> Document:
    """KOMA-Script article: a short technical field report."""
    return Document(
        meta=_meta(
            documentclass="scrartcl", class_options="a4paper,parskip=half",
            title="Reproducible figures in a small research group",
            author="Dana Whitlock",
            body_font_pt=11, line_spacing=1.1, paragraph_indent=False,
            packages=DEFAULT_PACKAGES + ["booktabs", "hyperref"],
            preamble_extras=(
                "\\subtitle{A field report from a four-person lab}\n"
                "\\date{March 2027}"),
        ),
        children=[
            Title(children=[Text(text=
                "Reproducible figures in a small research group")]),
            Author(children=[Text(text="Dana Whitlock")]),
            Abstract(children=[Text(text=
                "A four-person research group replaced its hand-edited "
                "figures with scripts that rebuild every plot from "
                "the raw data in one command. Setting this up took "
                "about 24 hours. Updating a figure now takes 0.4 hours "
                "instead of 3.5, so the investment pays back after "
                "eight updates. We describe the workflow, what went "
                "wrong and what we would do again.")]),

            _sec("Why bother?", label="sec:why"),
            _p("Our group publishes about a dozen papers a year, and "
               "almost every figure is redrawn at least three times: "
               "after a new measurement, after a reviewer comment and "
               "for the thesis. Until last year each redraw was done "
               "by hand in a graphics program. That was slow, and it "
               "was also fragile: nobody could say which data file a "
               "published figure had come from ",
               Citation(keys=["sandoval17"]), "."),
            _p("We set ourselves three goals:"),
            _ord_items(
                "every figure can be rebuilt from raw data with one "
                "command;",
                "the same style is applied to every figure in a "
                "document;",
                "a figure's history is recorded together with the "
                "data it came from.",
            ),

            _sec("The workflow", label="sec:workflow"),
            _sec("Scripts and folders", level=2),
            _p("Each paper has one folder with three subfolders: ",
               ("data", ["code"]), " for raw files that are never "
               "edited, ", ("scripts", ["code"]), " with one script per "
               "figure, and ", ("figures", ["code"]), " for the output. "
               "A single build file lists which script produces which "
               "figure and rebuilds only what has changed."),
            _sec("Version control", level=2),
            _p("Scripts and the build file live in version control, "
               "and every commit message names the figure it "
               "changes. The raw data are too large for the "
               "repository, so we store their checksums instead and "
               "verify them before a build.",
               Footnote(children=[Text(text=
                   "A 64-character checksum per file is enough to catch "
                   "a replaced or truncated data file.")])),
            _sec("A shared style", level=2),
            _p("One style file sets font size, line widths and colours "
               "for all plots. Figure width is fixed to the column "
               "width of the target journal, ",
               _m(r"w=8.6\,\mathrm{cm}"), " for a single column, so "
               "that text in a figure appears at the same size as the "
               "body text."),

            _sec("What it saved", label="sec:results"),
            _p("We timed the five steps of a typical figure update "
               "before and after the change, averaged over ten "
               "updates each (Table ", _ref("tab:time"), ")."),
            Table(
                rows=_figure_task_rows(),
                caption="Time for one figure update, in hours.",
                label="tab:time", alignment="lrr", style="booktabs",
                header=True),
            _p("The setup cost ", _m("C"), " was 24 h. If an update "
               "takes ", _m(r"t_{\mathrm{old}}"), " before and ",
               _m(r"t_{\mathrm{new}}"), " after, the break-even number "
               "of updates is"),
            _eq(r"N^{*}=\frac{C}{t_{\mathrm{old}}-t_{\mathrm{new}}}"
                r"=\frac{24}{3.5-0.4}\approx 7.7,", "eq:breakeven"),
            _p("so eight updates are enough, which one paper alone "
               "reaches. Equation ", _ref("eq:breakeven", "eqref"),
               " ignores the benefit that matters most to us, namely "
               "that reviewers' requests for a changed axis no longer "
               "cause dread."),

            _sec("What went wrong", label="sec:problems"),
            _items(
                "People kept editing exported figures by hand "
                "\u201cjust this once\u201d, which silently broke the link to "
                "the script;",
                "Two machines had different font versions, so the "
                "same script produced slightly different layouts;",
                "The build file grew into the only documentation of "
                "the analysis, and was read by nobody.",
            ),
            _p("We now forbid hand edits in the figures folder, "
               "pin font versions in the style file and write a "
               "short README per paper."),

            _sec("Recommendations", label="sec:recs"),
            _p("For a group of our size we recommend starting with "
               "one paper, not the whole archive, and keeping the "
               "style file under version control from the first day. "
               "Compare the time saved with your own numbers using "
               "the break-even formula above before you invest the "
               "first day."),
            _bib(
                ("sandoval17", "Sandoval, M., Eze, O.: Reproducible "
                 "research practices in small labs. J. Example Res. "
                 "Methods \\textbf{5}(1), 12--29 (2017)"),
            ),
        ],
    )
