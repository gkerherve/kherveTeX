"""One example for each thesis class: mimosis, hepthesis, suftesi, toptesi, disser, elegantbook."""
from __future__ import annotations

from ..model import (
    Abstract, Author, Citation, CrossRef, DEFAULT_PACKAGES, Document,
    Footnote, Keywords, MathBlock, MathInline, RawLatex, Section, Table,
    Text, Theorem, Title,
)
from ..example_helpers import _items, _meta, _ord_items, _p


def _sec(text, level=1, label=None):
    return Section(level=level, children=[Text(text=text)], label=label)


def _m(latex):
    return MathInline(latex=latex)


def _eq(latex, label=None):
    return MathBlock(latex=latex, numbered=label is not None, label=label)


def _bib(*entries):
    body = "\n".join(f"\\bibitem{{{k}}} {t}" for k, t in entries)
    return RawLatex(text="\\begin{thebibliography}{99}\n" + body
                         + "\n\\end{thebibliography}")


def _thesis_meta(cls, title, author, **kw):
    kw.setdefault("packages", DEFAULT_PACKAGES + ["booktabs", "hyperref"])
    return _meta(documentclass=cls, title=title, author=author,
                 body_font_pt=11, line_spacing=1.0, paragraph_indent=True,
                 **kw)



def _toc():
    return RawLatex(text="\\tableofcontents")


# ------------------------------------------------------------ mimosis
def mimosis_thesis() -> Document:
    return Document(
        meta=_thesis_meta("mimosis", "Persistent Currents of Cold Atoms in a Ring Lattice",
                          "Elena Marchetti", class_options="oneside,openany"),
        children=[
            Title(children=[Text(text="Persistent Currents of Cold Atoms in a Ring Lattice")]),
            Author(children=[Text(text="Elena Marchetti")]),
            Abstract(children=[Text(text=
                "Rings of ultracold atoms are a clean testbed for superfluid flow. "
                "This thesis studies a Bose-Einstein condensate of 87Rb loaded into "
                "a ring-shaped optical lattice with 24 sites, and asks how long a "
                "quantized circulation survives when the lattice depth is raised. "
                "We derive a Bose-Hubbard description of the ring, measure the "
                "decay of the winding number with time, and find lifetimes that "
                "grow from 0.4 s to 5.2 s as the depth goes from 2 to 10 recoil "
                "energies. The decay is explained by thermally activated phase "
                "slips across the weakest link of the ring.")]),
            _toc(),

            _sec("Introduction", label="ch:intro"),
            _sec("Why rings?", 2),
            _p("A superfluid in a ring can carry a flow that never stops. Whereas a "
               "stirred cup of water comes to rest within seconds, the wave function "
               "of a condensate must return to itself after one trip around the ring, "
               "so the circulation is quantized in units of ", _m(r"\hbar/m"),
               " per unit radius. Such persistent currents have been observed in "
               "helium and, more recently, in dilute atomic gases ",
               Citation(keys=["ramanathan2011", "moulder2012"]), "."),
            _p("The ring lattice added in this work breaks the ring into ",
               _m("N=24"), " sites. It turns the continuous superfluid into a chain "
               "of weakly coupled condensates, in which a phase slip becomes a "
               "discrete, countable event."),
            _sec("Contributions", 2),
            _p("The main results of this thesis are the following:"),
            _ord_items(
                "a Bose-Hubbard model of the ring whose parameters are fixed by a "
                "band-structure calculation rather than fitted;",
                "a measurement of the winding-number lifetime as a function of "
                "lattice depth (Table 3.1);",
                "a thermal phase-slip model that reproduces the lifetimes within "
                "their uncertainty.",
            ),
            _sec("Outline", 2),
            _p("Chapter ", CrossRef(label="ch:theory"), " derives the lattice "
               "Hamiltonian and the energy barrier for a phase slip. Chapter ",
               CrossRef(label="ch:exp"), " describes the apparatus and the lifetime "
               "measurements and compares them with theory."),

            _sec("Theory of the ring lattice", label="ch:theory"),
            _sec("Bose-Hubbard model", 2),
            _p("For a lattice deep enough that only the lowest band is populated, "
               "the atoms are described by the Bose-Hubbard Hamiltonian"),
            _eq(r"\hat H = -J\sum_{j=1}^{N}\left(\hat a_{j+1}^{\dagger}\hat a_j + "
                r"\mathrm{h.c.}\right) + \frac{U}{2}\sum_{j=1}^{N}\hat n_j(\hat n_j-1),",
                "eq:bh"),
            _p("where ", _m("J"), " is the tunnelling amplitude between neighbouring "
               "sites, ", _m("U"), " the on-site interaction, and sites are "
               "identified modulo ", _m("N"), ". For ", _m("U/J"),
               " small, the mean-field ansatz ",
               _m(r"\psi_j=\sqrt{n}\,e^{i\varphi_j}"), " turns Eq. (",
               CrossRef(label="eq:bh", kind="ref"), ") into a classical chain of "
               "phases, and a current-carrying state has ",
               _m(r"\varphi_{j+1}-\varphi_j = 2\pi w/N"),
               " with integer winding number ", _m("w"), "."),
            _sec("Energy barrier for a phase slip", 2),
            _p("The energy per site of the state with winding ", _m("w"), " is ",
               _m(r"E(w) = -2Jn\cos(2\pi w/N)"), ", so the current is ",
               _m(r"I_w = (2\pi Jn/\hbar N)\sin(2\pi w/N)"),
               ". The state is metastable as long as the phase step stays "
               "below ", _m(r"\pi/2"), ", i.e. for ", _m("w<N/4"), ". We write the barrier as"),
            _eq(r"\Delta E(w) = 2Jn\left[\cos\frac{2\pi (w-1)}{N} - "
                r"\cos\frac{2\pi w}{N}\right] \approx \frac{4\pi J n}{N}\,"
                r"\sin\frac{2\pi w}{N}\,\sin\frac{\pi}{N}.", "eq:barrier"),
            _p("The barrier shrinks with ", _m("J"),
               ", which falls exponentially with lattice depth ", _m("V_0"),
               ". The simple estimate below, valid for ", _m(r"V_0 \gtrsim 2E_r"),
               ", shows the trend that the experiment tests:"),
            _eq(r"\frac{J}{E_r} \simeq \frac{4}{\sqrt{\pi}}\left(\frac{V_0}{E_r}\right)^{3/4}"
                r"e^{-2\sqrt{V_0/E_r}}.", "eq:jfit"),
            _p("Here ", _m("E_r"), " is the photon recoil energy of the lattice light. "
               "Equation ", CrossRef(label="eq:jfit", kind="eqref"),
               " is the Mathieu-equation asymptote",
               Footnote(children=[Text(text="See any treatment of the lowest band of "
                                       "the Mathieu equation for the full expression.")]),
               "; the numerical values used below come from the exact band structure."),

            _sec("Experiment and results", label="ch:exp"),
            _sec("Apparatus", 2),
            _p("A condensate of about ", _m(r"4\times 10^{4}"), " atoms of ",
               _m(r"^{87}\mathrm{Rb}"), " is prepared in a magnetic trap and "
               "transferred to a ring-shaped dipole potential of radius 20 micrometresm. A "
               "24-site lattice is imprinted with a digital micromirror device. The "
               "winding number is read out by releasing the atoms and imaging the "
               "central hole, whose size scales with the circulation."),
            _sec("Measured lifetimes", 2),
            _p("We prepare ", _m("w=1"), " by a short rotation of the lattice and "
               "hold the atoms for a variable time before readout. Each lifetime "
               "below is the 1/e time of the surviving fraction, obtained from "
               "at least 40 repetitions per hold time (Table ",
               CrossRef(label="tab:life"), ")."),
            Table(rows=[
                ["Depth V0 (Er)", "J/h (Hz)", "Barrier (nK)", "Lifetime (s)"],
                ["2", "41.0", "8.2", "0.4 ± 0.1"],
                ["4", "17.5", "17.9", "1.1 ± 0.2"],
                ["6", "7.6", "29.4", "2.4 ± 0.3"],
                ["8", "3.4", "40.6", "3.7 ± 0.5"],
                ["10", "1.5", "52.3", "5.2 ± 0.7"],
            ], caption="Winding-number lifetime of the w = 1 state against "
                       "lattice depth.", label="tab:life", alignment="rrrr",
               style="booktabs", header=True),
            _p("The lifetime grows roughly linearly with the barrier, as expected "
               "for a thermally activated process with an attempt rate "
               "of order 1 Hz at the temperature of 22 nK. A fit of ",
               _m(r"\tau = \tau_0\exp(\Delta E/k_B T)"), " gives ", _m(r"\tau_0 = 0.09\pm0.03\ \mathrm{s}"),
               "."),
            _sec("Conclusion", 2),
            _p("A deeper ring lattice stabilizes persistent flow by suppressing "
               "tunnelling across the weakest link, with lifetimes that follow the "
               "activated form of Eq. ", CrossRef(label="eq:barrier", kind="eqref"),
               ". Raising the lattice depth beyond 10 recoil energies would push "
               "the lifetime past the 8 s vacuum limit of the present apparatus.",
               Footnote(children=[Text(text="The vacuum lifetime of the trap is "
                                       "about 8 s.")])),
            _bib(("ramanathan2011",
                  "A. Ramanathan et al., ``Superflow in a toroidal Bose-Einstein "
                  "condensate: an atom circuit with a tunable weak link'' (example "
                  "reference), Example Phys. Rev. 106, 130401 (2011)."),
                 ("moulder2012",
                  "S. Moulder et al., ``Quantized supercurrent decay in an annular "
                  "Bose-Einstein condensate'' (example reference), Example Phys. "
                  "Rev. 86, 013629 (2012).")),
        ],
    )


# ---------------------------------------------------------- hepthesis
def hep_thesis() -> Document:
    return Document(
        meta=_thesis_meta("hepthesis",
                          "Search for a Heavy Dijet Resonance at 13 TeV",
                          "Tomas Veldkamp", class_options="oneside,openany"),
        children=[
            Title(children=[Text(text="Search for a Heavy Dijet Resonance "
                                      "at 13 TeV")]),
            Author(children=[Text(text="Tomas Veldkamp")]),
            Abstract(children=[Text(text=
                "A search is presented for a narrow resonance decaying to two "
                "jets, using 138 inverse femtobarns of proton-proton collisions "
                "at a centre-of-mass energy of 13 TeV recorded by a fictional "
                "general-purpose detector. The dijet invariant-mass spectrum is "
                "fitted with a smooth background function and no significant "
                "excess is found; the largest local deviation is 2.1 standard "
                "deviations at 4.3 TeV. Upper limits on the production "
                "cross-section times acceptance are set for masses between 2 "
                "and 8 TeV, and a benchmark excited-quark model is excluded "
                "below 6.4 TeV at 95% confidence level.")]),
            _toc(),

            _sec("Introduction", label="ch:intro"),
            _p("The Standard Model describes the strong interaction through "
               "quantum chromodynamics (QCD), whose dominant signature at a "
               "hadron collider is the production of pairs of jets. A new "
               "particle with a mass of several TeV that couples to quarks or "
               "gluons would appear as a localized bump in the dijet invariant "
               "mass ", _m("m_{jj}"), " on top of a steeply falling QCD "
               "spectrum ", Citation(keys=["frisch2018", "okafor2020"]), "."),
            _p("This thesis reports a search for such a bump. The analysis "
               "is purely data-driven in its background estimate, which makes "
               "it sensitive to any resonance whose width is small compared "
               "with the detector resolution of about 3% in ", _m("m_{jj}"),
               "."),

            _sec("Analysis strategy", label="ch:strategy"),
            _sec("Event selection", 2),
            _p("Events are selected with a single-jet trigger that is fully "
               "efficient above a leading-jet transverse momentum of ",
               _m(r"p_T = 500\ \mathrm{GeV}"), ". The two leading jets must "
               "satisfy ", _m(r"|\eta|<2.5"), " and a rapidity separation ",
               _m(r"|y^{*}| = |y_1-y_2|/2 < 0.6"), ", which suppresses "
               "t-channel QCD scattering. The selection yields ",
               _m(r"4.7\times10^{7}"), " events above ", _m(r"m_{jj}=1.8\ "
               r"\mathrm{TeV}"), "."),
            _sec("Background fit", 2),
            _p("The smooth QCD spectrum is described by the dijet function"),
            _eq(r"\frac{\mathrm{d}\sigma}{\mathrm{d}m_{jj}} = p_0\,"
                r"\frac{(1-x)^{p_1}}{x^{p_2+p_3\ln x}},\qquad "
                r"x = \frac{m_{jj}}{\sqrt{s}},", "eq:dijet"),
            _p("where ", _m("p_0"), " is a normalization and ",
               _m(r"p_{1,2,3}"), " are free shape parameters. A signal "
               "of mass ", _m("m_X"), " is then tested with a profile "
               "likelihood ratio. The expected signal significance in the "
               "Gaussian limit is approximately ",
               _m(r"Z\simeq S/\sqrt{B}"), ", where ", _m("S"), " and ",
               _m("B"), " are the signal and background counts in the "
               "window around ", _m("m_X"), "; Eq. ",
               CrossRef(label="eq:dijet", kind="eqref"),
               " sets ", _m("B"), "."),
            _sec("Systematic uncertainties", 2),
            _p("Table ", CrossRef(label="tab:syst"), " lists the dominant "
               "uncertainties on the signal yield, evaluated at ",
               _m(r"m_X=4\ \mathrm{TeV}"), "."),
            Table(rows=[
                ["Source", "Uncertainty on signal"],
                ["Jet energy scale", "4.0"],
                ["Jet energy resolution", "1.5"],
                ["Luminosity", "1.7"],
                ["Parton distribution functions", "2.2"],
                ["Total", "5.4"],
            ], caption="Systematic uncertainties on the signal yield (in per cent) "
                       "for a 4 TeV resonance, added in quadrature in the last row.",
               label="tab:syst", alignment="lr", style="booktabs",
               header=True),

            _sec("Results", label="ch:results"),
            _p("No significant deviation from the background-only hypothesis "
               "is seen. The largest excess, around 4.3 TeV, has a local "
               "significance of 2.1 standard deviations, which becomes 0.8 "
               "once the look-elsewhere effect is included",
               Footnote(children=[Text(text="The look-elsewhere correction "
                                       "uses 1000 background-only pseudo-"
                                       "experiments.")]),
               ". Observed 95% confidence-level limits on the cross-section "
               "times acceptance are given in Table ",
               CrossRef(label="tab:limits"), "."),
            Table(rows=[
                ["Mass (TeV)", "Expected limit (fb)", "Observed limit (fb)"],
                ["2.0", "210", "185"],
                ["4.0", "6.8", "7.9"],
                ["6.0", "0.62", "0.58"],
                ["8.0", "0.31", "0.33"],
            ], caption="Expected and observed 95 per cent CL upper limits on the "
                       "cross-section times acceptance.",
               label="tab:limits", alignment="rrr", style="booktabs",
               header=True),
            _p("Comparing the observed limit with the predicted cross-section "
               "excludes the benchmark excited-quark model for masses below "
               "6.4 TeV, an improvement of 0.9 TeV over the partial dataset."),

            _sec("Conclusion", label="ch:concl"),
            _p("A search for dijet resonances in 138 inverse femtobarns found "
               "data compatible with the Standard Model. The dominant "
               "systematic uncertainty is the jet energy scale; improving it "
               "is the most direct route to a stronger limit with the full "
               "dataset of the high-luminosity run."),
            _bib(("frisch2018",
                  "M. Frisch et al., ``Dijet resonance searches at hadron "
                  "colliders'' (example reference), Example Phys. Rep. 58, 1 "
                  "(2018)."),
                 ("okafor2020",
                  "N. Okafor and L. Brandt, ``A data-driven dijet background "
                  "function'' (example reference), Example J. Phys. 47, 112 "
                  "(2020).")),
        ],
    )


# ------------------------------------------------------------ suftesi
def suftesi_thesis() -> Document:
    return Document(
        meta=_thesis_meta("suftesi",
                          "Ports of Call: Mediterranean Cities in Travel Writing",
                          "Giulia Ferraresi",
                          class_options="oneside,openany"),
        children=[
            Title(children=[Text(text="Ports of Call: Mediterranean Cities "
                                      "in Travel Writing")]),
            Author(children=[Text(text="Giulia Ferraresi")]),
            Abstract(children=[Text(text=
                "This thesis reads six nineteenth-century travel narratives "
                "of the Mediterranean to ask how port cities were made "
                "legible to a northern readership. It argues that the "
                "harbour, rather than the monument, is the organizing image "
                "of these texts, and that the travellers' descriptions of "
                "markets, quarantine and languages record a commercial "
                "cosmopolitanism that later national histories erased.")]),
            _toc(),

            _sec("Introduction", label="ch:intro"),
            _sec("The harbour as a vantage point", 2),
            _p("Travel writing on the Mediterranean is usually read for its "
               "ruins. Yet the writers examined here arrive by sea, and the "
               "first thing they describe is not a temple but a waterfront "
               "crowded with ships, customs sheds and interpreters ",
               Citation(keys=["moretti2009", "bianchi2014"]), ". The "
               "approach from the water fixes a particular point of view: "
               "the city is seen whole, from outside, before it is entered."),
            _sec("Corpus and method", 2),
            _p("The corpus consists of six narratives, listed in Table ",
               CrossRef(label="tab:corpus"), ", chosen because each devotes "
               "at least one chapter to a single port. The method is close "
               "reading, supported by a simple count of the commercial "
               "vocabulary in each text."),
            Table(rows=[
                ["Narrative (fictional)", "Year", "Port studied", "Chapters"],
                ["Letters from the Levant", "1838", "Smyrna", "3"],
                ["A Season at Trieste", "1846", "Trieste", "2"],
                ["Notes on Alexandria", "1851", "Alexandria", "4"],
                ["The Adriatic Shore", "1859", "Venice", "2"],
                ["Southern Passages", "1867", "Naples", "3"],
                ["The White City", "1872", "Algiers", "2"],
            ], caption="The corpus: six invented narratives used as "
                       "illustrative sources.", label="tab:corpus",
               alignment="llll", style="booktabs", header=True),

            _sec("The market and the quarantine", label="ch:market"),
            _p("Two scenes recur in almost every narrative: the market, where "
               "languages are heard together, and the lazaretto, where "
               "travellers wait out the quarantine. They are opposite "
               "experiences of the same city, one open and one enclosed.",
               Footnote(children=[Text(text="The quarantine lasted between "
                                       "ten and forty days, depending on the "
                                       "port of departure.")])),
            Theorem(kind="definition", title="Cosmopolitan scene",
                    children=[Text(text="A passage in which three or more "
                                   "languages or communities are described "
                                   "as sharing one public space.")]),
            _p("By this definition the narratives contain 41 cosmopolitan "
               "scenes in about 1,900 pages, a density that falls "
               "sharply in the two last texts of the corpus. The change "
               "tracks the hardening of national categories after 1860, and "
               "supports the argument of the introduction."),
            _sec("Conclusion", label="ch:concl"),
            _p("Reading from the harbour changes what counts as evidence: "
               "the customs list becomes as eloquent as the cathedral. "
               "Further work could extend the corpus to Greek and Arabic "
               "sources, which would test whether the same vantage point "
               "organizes accounts written from the shore."),
            _bib(("moretti2009",
                  "L. Moretti, \\emph{Il porto e la penna} (example "
                  "reference), Editrice Esempio, Bologna, 2009."),
                 ("bianchi2014",
                  "R. Bianchi, ``Waterfront narratives'' (example "
                  "reference), \\emph{Example Journal of Cultural History} "
                  "22 (2014), 31--58.")),
        ],
    )


# ------------------------------------------------------------ toptesi
# toptesi sets Italian captions; this thesis is written in English.
_TOP_EN = r"""\setdefaultlanguage{english}"""

def toptesi_thesis() -> Document:
    return Document(
        meta=_thesis_meta("toptesi",
                          "Regenerative Braking Control for a Light Electric Vehicle",
                          "Marco Delvaux", preamble_extras=_TOP_EN),
        children=[
            Title(children=[Text(text="Regenerative Braking Control for a "
                                      "Light Electric Vehicle")]),
            Author(children=[Text(text="Marco Delvaux")]),
            Abstract(children=[Text(text=
                "This thesis designs and tests a regenerative braking "
                "controller for a 250 kg electric quadricycle with a 4 kW "
                "in-wheel motor. A slip-based blending law divides the "
                "braking demand between the motor and the friction brakes. "
                "In simulation over a 12 km urban cycle the controller "
                "recovers 14.8 per cent of the traction energy and raises the "
                "range from 62 to 71 km, with no loss of stopping distance "
                "below 8 m from 30 km/h.")]),
            _toc(),

            _sec("Introduction", label="ch:intro"),
            _p("Light electric vehicles spend most of their energy "
               "accelerating a small mass repeatedly, so the share that can "
               "be recovered when braking is large ",
               Citation(keys=["rossi2017", "haddad2019"]), ". The difficulty "
               "is that the motor can brake only within the limits of its "
               "torque and of the battery's charge acceptance, while the "
               "driver expects the same pedal feel as with friction brakes."),
            _p("The objective is a controller that maximizes the recovered "
               "energy subject to three constraints: the battery current "
               "limit, the wheel-slip limit and the stopping distance."),
            _sec("Specifications", 2),
            _ord_items("Recover at least 12 per cent of the traction energy "
                       "on the urban cycle.",
                       "Stop from 30 km/h in no more than 8 m.",
                       "Keep the battery charge current below 40 A."),

            _sec("Vehicle model and controller", label="ch:model"),
            _sec("Longitudinal dynamics", 2),
            _p("With vehicle mass ", _m("m"), ", wheel radius ", _m("r"),
               " and braking force ", _m("F_b"), ", the speed ", _m("v"),
               " obeys"),
            _eq(r"m\,\dot v = -F_b - \tfrac{1}{2}\rho C_d A\,v^{2} - "
                r"C_{rr}\,m g,", "eq:long"),
            _p("where ", _m(r"\rho"), " is the air density, ", _m("C_d A"),
               " the drag area and ", _m("C_{rr}"), " the rolling "
               "resistance coefficient. The braking force splits into a "
               "regenerative part and a friction part,"),
            _eq(r"F_b = F_{\mathrm{reg}} + F_{\mathrm{fric}},\qquad "
                r"F_{\mathrm{reg}} = \min\!\left(\beta F_{\mathrm{dem}},\ "
                r"\frac{T_{\max}}{r}\right),", "eq:blend"),
            _p("with demand ", _m(r"F_{\mathrm{dem}}"), ", motor torque "
               "limit ", _m(r"T_{\max}=95\ \mathrm{N\,m}"),
               " and blending gain ", _m(r"\beta\in[0,1]"), ". Equation ",
               CrossRef(label="eq:blend", kind="eqref"),
               " sends as much braking as possible to the motor, and the "
               "friction brakes supply the remainder."),
            _sec("Parameters", 2),
            Table(rows=[
                ["Parameter", "Value", "Unit"],
                ["Vehicle mass", "250", "kg"],
                ["Wheel radius", "0.26", "m"],
                ["Peak motor power", "4.0", "kW"],
                ["Peak motor torque", "95", "N m"],
                ["Battery charge limit", "40", "A"],
            ], caption="Vehicle and drive parameters used in the "
                       "simulations.", label="tab:params",
               alignment="lrl", style="booktabs", header=True),

            _sec("Simulation results", label="ch:results"),
            _p("The controller was tested on a 12 km urban cycle with 38 "
               "stops. Table ", CrossRef(label="tab:results"),
               " compares the vehicle without recovery, a fixed "
               "blending gain and the proposed slip-based law."),
            Table(rows=[
                ["Strategy", "Energy recovered (per cent)", "Range (km)",
                 "Stop from 30 km/h (m)"],
                ["No recovery", "0", "62", "6.9"],
                ["Fixed gain 0.5", "9.7", "67", "7.4"],
                ["Slip-based law", "14.8", "71", "7.6"],
            ], caption="Urban-cycle results for three braking strategies.",
               label="tab:results", alignment="lrrr", style="booktabs",
               header=True),
            _p("The slip-based law meets all three specifications: it "
               "recovers 14.8 per cent of the energy, against the 12 per cent "
               "target, and stops in 7.6 m, inside the 8 m limit. The peak "
               "charge current was 37 A."),
            _sec("Conclusion", label="ch:concl"),
            _p("A simple blending law, limited by torque and slip, adds 9 km "
               "of range to a light electric vehicle without changing the "
               "braking distance noticeably. The next step is a "
               "road test on the prototype, with the battery temperature "
               "included in the charge limit."),
            _bib(("rossi2017",
                  "F. Rossi and A. Lund, ``Regenerative braking in small "
                  "electric vehicles'' (example reference), \\emph{Example "
                  "Trans. Vehicular Eng.} 12 (2017), 220--231."),
                 ("haddad2019",
                  "S. Haddad, ``Brake blending under slip constraints'' "
                  "(example reference), \\emph{Example Control Letters} 5 "
                  "(2019), 88--95.")),
        ],
    )


# ------------------------------------------------------------- disser
def disser_thesis() -> Document:
    return Document(
        meta=_thesis_meta("disser",
                          "Spectral Estimation for Short Time Series",
                          "Ivan P. Sokolov",
                          preamble_extras=r"\def\contentsname{Contents}\def\bibname{References}\defaulthyphenchar=`\-\AtBeginDocument{\hyphenchar\font=`\-}"),
        children=[
            Title(children=[Text(text="Spectral Estimation for Short "
                                      "Time Series")]),
            Author(children=[Text(text="Ivan P. Sokolov")]),
            Abstract(children=[Text(text=
                "The thesis studies the estimation of the power spectrum "
                "from records of fewer than 100 samples. A regularized "
                "autoregressive estimator is proposed and shown to reduce "
                "the mean squared error of the peak frequency by 31 per cent "
                "against the periodogram on synthetic signals.")]),
            _toc(),

            _sec("Introduction", label="ch:intro"),
            _p("Many measured signals are short: a clinical recording, a "
               "single seasonal cycle, a transient in a power line. For "
               "such records the periodogram has a frequency resolution "
               "of about ", _m("1/N"), " and large variance ",
               Citation(keys=["ivanov2012", "petrova2016"]), ". "
               "This work reduces the variance by fitting a low-order "
               "autoregressive (AR) model with a smoothness penalty."),
            _sec("Aim and tasks", 2),
            _p("The aim is an estimator of the peak frequency that "
               "remains accurate for ", _m("N<100"), " samples. The tasks are:"),
            _ord_items("derive the penalized AR estimator;",
                       "compare it with the periodogram on synthetic data;",
                       "state when the penalty helps and when it does not."),

            _sec("Penalized autoregressive estimator", label="ch:method"),
            _p("Let ", _m("x_1,\\dots,x_N"), " be a zero-mean record. "
               "An AR model of order ", _m("p"), " predicts"),
            _eq(r"x_t = \sum_{k=1}^{p} a_k\,x_{t-k} + \varepsilon_t,"
                r"\qquad \varepsilon_t\sim\mathcal N(0,\sigma^{2}),",
                "eq:ar"),
            _p("and the spectrum follows from the coefficients:"),
            _eq(r"S(f) = \frac{\sigma^{2}}"
                r"{\left|1-\sum_{k=1}^{p} a_k\,e^{-2\pi i k f}\right|^{2}}.",
                "eq:spec"),
            _p("The coefficients minimize the penalized least squares "
               "criterion"),
            _eq(r"\hat a = \arg\min_a \sum_{t=p+1}^{N}\Bigl(x_t-\sum_k "
                r"a_k x_{t-k}\Bigr)^2 + \lambda\sum_{k=1}^{p} k^{2}a_k^{2},",
                "eq:pen"),
            _p("where ", _m(r"\lambda"), " controls the penalty. For ",
               _m(r"\lambda=0"), " Eq. ", CrossRef(label="eq:pen", kind="eqref"),
               " is ordinary least squares; the weight ", _m("k^2"),
               " shrinks high-lag coefficients more strongly."),
            Theorem(kind="proposition",
                    children=[Text(text="For ")] + [MathInline(latex=r"\lambda>0")]
                    + [Text(text=" the penalized estimator is unique and "
                            "stable, that is, all poles of Eq. "),
                       CrossRef(label="eq:spec", kind="eqref"),
                       Text(text=" lie inside the unit circle for any "
                            "record with nonzero energy.")]),

            _sec("Numerical experiments", label="ch:exp"),
            _p("We generated 2000 records of length ", _m("N"), " from a "
               "sinusoid at ", _m("f_0=0.173"), " with unit-variance noise, "
               "and estimated the peak frequency by each method. Table ",
               CrossRef(label="tab:mse"), " gives the root mean squared "
               "error, in units of ", _m("10^{-3}"), " cycles per sample."),
            Table(rows=[
                ["N", "Periodogram", "AR, lambda = 0", "AR, penalized"],
                ["32", "9.8", "7.9", "6.1"],
                ["64", "5.2", "4.3", "3.6"],
                ["96", "3.5", "3.0", "2.4"],
            ], caption="Root mean squared error of the peak frequency "
                       "(units of 0.001 cycles per sample).",
               label="tab:mse", alignment="lrrr", style="booktabs",
               header=True),
            _p("The penalized estimator has the smallest error for every "
               "length, with the largest gain, 38 per cent against the "
               "periodogram, at ", _m("N=32"), ". On average the gain is "
               "31 per cent."),
            _sec("Conclusion", label="ch:concl"),
            _p("A smoothness penalty on autoregressive coefficients gives "
               "a stable spectral estimator that is more accurate than the "
               "periodogram for short records. Choosing ",
               _m(r"\lambda"), " automatically remains open."),
            _bib(("ivanov2012",
                  "P. Ivanov, \\emph{Short Record Spectral Analysis} (example "
                  "reference), Example Press, 2012."),
                 ("petrova2016",
                  "A. Petrova and K. Lind, Penalized AR models (example "
                  "reference), \\emph{Example Signal Proc.} 9 (2016), "
                  "14--27.")),
        ],
    )


# -------------------------------------------------------- elegantbook
# ElegantBook always loads biblatex, so its citations need a .bib file;
# filecontents writes it from the document itself.
_ELEGANT_BIB = r"""\begin{filecontents*}{refs.bib}
@article{kalman1960x, author={Kalman, R.}, title={On controllability (example reference)},
  journal={Example Control Review}, volume={3}, pages={1--12}, year={1960}}
@book{brandt2010, author={Brandt, L.}, title={Linear Systems by Example (example reference)},
  publisher={Example Press}, year={2010}}
\end{filecontents*}
\addbibresource{refs.bib}"""

def elegant_book() -> Document:
    return Document(
        meta=_thesis_meta("elegantbook",
                          "A Short Course on Linear Dynamical Systems",
                          "Hanna Lindqvist",
                          preamble_extras=_ELEGANT_BIB),
        children=[
            Title(children=[Text(text="A Short Course on Linear "
                                      "Dynamical Systems")]),
            Author(children=[Text(text="Hanna Lindqvist")]),
            RawLatex(text="\\frontmatter"),
            _toc(),
            RawLatex(text="\\mainmatter"),

            _sec("Linear systems", label="ch:lin"),
            _sec("State-space models", 2),
            _p("A continuous-time linear system with state ", _m(r"x(t)\in"
               r"\mathbb R^n"), " and input ", _m("u(t)"), " is written"),
            _eq(r"\dot x(t) = A\,x(t) + B\,u(t),\qquad y(t) = C\,x(t),",
                "eq:ss"),
            _p("where ", _m("A"), ", ", _m("B"), " and ", _m("C"),
               " are constant matrices. With ", _m("u=0"), " the solution "
               "is ", _m(r"x(t)=e^{At}x(0)"), ", so the behaviour is "
               "governed by the eigenvalues of ", _m("A"), "."),
            _sec("Stability", 2),
            Theorem(kind="definition", title="Asymptotic stability",
                    children=[Text(text="The origin of ")] +
                    [MathInline(latex=r"\dot x=Ax")] +
                    [Text(text=" is asymptotically stable if "
                          "every solution tends to zero as t grows.")]),
            Theorem(kind="theorem", title="Eigenvalue test",
                    children=[Text(text="The system ")] +
                    [MathInline(latex=r"\dot x=Ax")] +
                    [Text(text=" is asymptotically stable if and only if "
                          "every eigenvalue of A has a negative real part.")]),
            Theorem(kind="proof", children=[Text(text=
                "Write A in Jordan form. Each Jordan block contributes terms "
                "of the form t^k exp(lambda t), which vanish as t grows if "
                "and only if the real part of lambda is negative.")]),
            _p("For example, the matrix ",
               _m(r"A=\begin{pmatrix}0&1\\-2&-3\end{pmatrix}"),
               " has eigenvalues ", _m("-1"), " and ", _m("-2"),
               ", so it is stable, in agreement with Table ",
               CrossRef(label="tab:ex"), "."),
            Table(rows=[
                ["System", "Eigenvalues", "Behaviour"],
                ["Spring-damper, light damping", "-0.2 +- 3.0i", "decaying oscillation"],
                ["Spring-damper, heavy damping", "-1, -2", "monotone decay"],
                ["Inverted pendulum, open loop", "+3.1, -3.1", "unstable"],
            ], caption="Three small systems and their eigenvalues.",
               label="tab:ex", alignment="lll", style="booktabs",
               header=True),

            _sec("Controllability and feedback", label="ch:ctrl"),
            _p("The input ", _m("u"), " can steer the system anywhere only "
               "if the pair ", _m("(A,B)"), " is controllable ",
               Citation(keys=["kalman1960x", "brandt2010"]), ". The test is "
               "an algebraic rank condition."),
            Theorem(kind="theorem", title="Kalman rank test",
                    children=[Text(text="The pair (A,B) is controllable if "
                                   "and only if the controllability matrix has full rank:")]),
            _eq(r"\operatorname{rank}\begin{pmatrix}B & AB & A^{2}B & "
                r"\cdots & A^{n-1}B\end{pmatrix} = n.", "eq:kalman"),
            _p("When Eq. ", CrossRef(label="eq:kalman", kind="eqref"),
               " holds, the feedback ", _m("u=-Kx"), " can place the "
               "eigenvalues of ", _m("A-BK"), " anywhere in the complex "
               "plane, which turns the unstable pendulum of Table ",
               CrossRef(label="tab:ex"), " into a stable one."),
            RawLatex(text="\\printbibliography[heading=bibintoc]"),
        ],
    )
