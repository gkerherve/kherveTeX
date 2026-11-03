"""Research papers and notes across the sciences, with checked numbers."""
from __future__ import annotations

from ..example_helpers import _items, _meta, _ord_items, _p
from ..model import (
    Abstract, Affiliation, Author, Citation, CrossRef, DEFAULT_PACKAGES,
    Document, Footnote, Keywords, MathBlock, MathInline, RawLatex, Section,
    Table, Text, Theorem, Title,
)


def _sec(text: str, level: int = 1) -> Section:
    return Section(level=level, children=[Text(text=text)])


def _m(latex: str) -> MathInline:
    return MathInline(latex=latex)


def _eq(latex: str, label: str | None = None) -> MathBlock:
    return MathBlock(latex=latex, numbered=label is not None, label=label)


def _bib(*entries: tuple[str, str]) -> RawLatex:
    body = "\n".join(f"\\bibitem{{{k}}} {t}" for k, t in entries)
    return RawLatex(text="\\begin{thebibliography}{99}\n" + body
                         + "\n\\end{thebibliography}")


def _paper_meta(title: str, author: str, extra=()) -> object:
    # Libertine carries the Unicode sub/superscript digits (TiO₂, cm⁻¹)
    # that Latin Modern lacks; the article class has no keyword env.
    return _meta(title=title, author=author, body_font_family="libertine",
                 packages=DEFAULT_PACKAGES + ["booktabs", "hyperref",
                                              *extra],
                 preamble_extras=(
                     "\\newenvironment{keyword}{\\par\\medskip\\noindent"
                     "\\textbf{Keywords:} }{\\par\\medskip}\n"
                     "\\providecommand{\\sep}{\\unskip, }"))


def _tab(rows, caption, label, alignment, header=True) -> Table:
    return Table(rows=rows, caption=caption, label=label,
                 alignment=alignment, style="booktabs", header=header)


# ------------------------------------------------------------------ XPS

def xps_surface_study() -> Document:
    """Surface-science paper built around XPS peak fitting."""
    return Document(
        meta=_paper_meta("XPS of TiO2 thin films", "A. Surface"),
        children=[
            Title(children=[Text(text=
                "Oxygen vacancies and Ti³⁺ states in reduced anatase "
                "TiO₂ thin films probed by X-ray photoelectron "
                "spectroscopy")]),
            Author(children=[Text(text=
                "A. Surface, B. Vacuum and C. Synchrotron")]),
            Affiliation(children=[Text(text=
                "Department of Materials, Example University")]),
            Abstract(children=[Text(text=
                "Anatase TiO₂ films grown by atomic layer deposition were "
                "annealed in ultra-high vacuum between 300 and 700 °C and "
                "analysed in situ by monochromated Al Kα XPS. Peak fitting "
                "of the Ti 2p region with spin–orbit-constrained doublets "
                "on a Shirley background resolves a Ti³⁺ component 1.7 eV "
                "below Ti⁴⁺, whose fraction of the Ti 2p signal rises from "
                "2.1 % to 14.0 % with annealing temperature. The O 1s "
                "spectra show a concurrent growth of a hydroxyl / "
                "vacancy-adjacent component at 531.3 eV. An Arrhenius "
                "analysis of the Ti³⁺ fraction gives an apparent activation "
                "energy of 0.23 ± 0.01 eV for vacancy formation.")]),
            Keywords(children=[Text(text=
                "XPS · TiO₂ · oxygen vacancies · peak fitting · "
                "Shirley background")]),

            _sec("Introduction"),
            _p("Titanium dioxide is the archetypal photocatalyst, and "
               "its activity is governed to a large extent by point "
               "defects at the surface ",
               Citation(keys=["alder2003"]), ". Removal of lattice "
               "oxygen leaves two excess electrons that localise on "
               "neighbouring Ti sites, producing Ti³⁺ centres with a "
               "characteristic chemical shift in the Ti 2p spectrum ",
               Citation(keys=["brandt2010"]), ". Quantifying that "
               "component reliably requires a physically constrained fit; "
               "in this work we describe a protocol and apply it to a "
               "temperature series."),

            _sec("Experimental"),
            _sec("Sample preparation", 2),
            _p("Films of nominal thickness 30 nm were grown on Si(100) "
               "by thermal ALD from TiCl₄ and H₂O at 250 °C (600 cycles at "
               "0.5 Å per cycle) and crystallised to anatase by a 1 h "
               "anneal in air at 450 °C, confirmed by Raman spectroscopy "
               "(Eg mode at 144 cm⁻¹). Each film was then annealed for "
               "30 min in the analysis chamber at 300, 400, 500, 600 or "
               "700 °C and cooled to room temperature before measurement."),
            _sec("XPS acquisition", 2),
            _items(
                "Monochromated Al Kα (hν = 1486.6 eV), 400 µm spot",
                "Pass energy 20 eV for core levels, 150 eV for surveys",
                "Charge neutraliser on; energy scale referenced to "
                "adventitious C 1s at 284.8 eV",
                "Base pressure < 5 × 10⁻¹⁰ mbar during acquisition",
            ),
            _sec("Peak fitting", 2),
            _p("Each component was modelled with a pseudo-Voigt line "
               "shape, a Gaussian–Lorentzian sum with mixing parameter ",
               _m(r"\eta"), " and full width at half maximum ",
               _m(r"\beta"), ":"),
            _eq(r"I(E) = A\left[\eta\,\frac{1}{1+4\left(\frac{E-E_0}"
                r"{\beta}\right)^2} + (1-\eta)\,\exp\!\left(-4\ln 2"
                r"\left(\frac{E-E_0}{\beta}\right)^2\right)\right]",
                "eq:pv"),
            _p("The inelastic background was removed with the iterative "
               "Shirley algorithm ", Citation(keys=["shirley1972"]),
               ", in which the background at binding energy ", _m("E"),
               " is proportional to the integrated peak area on the "
               "low-binding-energy side of ", _m("E"), ":"),
            _eq(r"B(E) = B_{\text{low}} + (B_{\text{high}}-B_{\text{low}})"
                r"\,\frac{\int_{E_{\text{low}}}^{E} [I(E')-B(E')]\,dE'}"
                r"{\int_{E_{\text{low}}}^{E_{\text{high}}} "
                r"[I(E')-B(E')]\,dE'}.", "eq:shirley"),
            _p("For the Ti 2p doublet the 2p₁/₂ component was tied to "
               "2p₃/₂ with a spin–orbit splitting of 5.72 eV and an "
               "area ratio fixed at the degeneracy ratio"),
            _eq(r"\frac{A(2p_{1/2})}{A(2p_{3/2})} = "
                r"\frac{2j_{1/2}+1}{2j_{3/2}+1} = \frac{2}{4} = "
                r"\frac{1}{2}.", "eq:ratio"),
            _p("The 2p₁/₂ width was left free: Coster–Kronig broadening "
               "makes it roughly twice that of 2p₃/₂. Atomic "
               "concentrations follow from the fitted areas ", _m("A_i"),
               " and the relative sensitivity factors ", _m("S_i"),
               " (Scofield cross-sections corrected for transmission and "
               "inelastic mean free path):"),
            _eq(r"x_i = \frac{A_i / S_i}{\sum_j A_j / S_j}.", "eq:quant"),

            _sec("Results"),
            _p("Table ", CrossRef(label="tab:ti2p"),
               " lists the fitted Ti 2p₃/₂ parameters. The Ti⁴⁺ position "
               "is stable to within 0.07 eV across the series, confirming "
               "that charge referencing is not responsible for the "
               "apparent new component. The Ti³⁺ peak sits 1.7 eV below "
               "Ti⁴⁺ throughout. If every Ti³⁺ ion is charge-compensated "
               "by half an oxygen vacancy, a Ti³⁺ fraction ", _m("f"),
               " corresponds to the stoichiometry "
               "TiO", _m(r"_{2-f/2}"),
               ", given as δ = f/2 in the last column."),
            _tab([
                ["Anneal (°C)", "Ti⁴⁺ (eV)", "Ti³⁺ (eV)",
                 "FWHM Ti⁴⁺", "f (pct)", "δ"],
                ["as-grown", "458.72", "—",      "0.98", "< 1",  "< 0.005"],
                ["300",      "458.70", "457.00", "0.99", "2.1",  "0.011"],
                ["400",      "458.69", "456.99", "1.01", "4.8",  "0.024"],
                ["500",      "458.68", "456.98", "1.03", "7.9",  "0.040"],
                ["600",      "458.66", "456.96", "1.06", "11.2", "0.056"],
                ["700",      "458.65", "456.95", "1.09", "14.0", "0.070"],
            ], "Ti 2p₃/₂ fit results (Shirley background, pseudo-Voigt, "
               "η = 0.3). Positions and widths in eV; f is the Ti³⁺ share of the "
               "total Ti 2p area in per cent, and δ is the vacancy "
               "content in TiO₂₋δ.",
               "tab:ti2p", "lrrrrr"),
            _p("The O 1s envelope requires three components: lattice "
               "O²⁻ at 530.0 eV, hydroxyl / vacancy-adjacent oxygen at "
               "531.3 eV and adsorbed H₂O at 532.6 eV (Table ",
               CrossRef(label="tab:o1s"), "). The lattice peak lies "
               "71.3 eV above Ti 2p₃/₂ of Ti⁴⁺, as expected for anatase."),
            _tab([
                ["Component", "BE (eV)", "FWHM (eV)", "Area 300 °C",
                 "Area 700 °C"],
                ["O–Ti (lattice)", "530.0", "1.10", "88.5", "79.2"],
                ["OH / defect",    "531.3", "1.45", "9.1",  "18.3"],
                ["H₂O (ads.)",     "532.6", "1.60", "2.4",  "2.5"],
            ], "O 1s component analysis (areas in per cent of the O 1s "
               "total).", "tab:o1s", "lrrrr"),

            _sec("Discussion"),
            _p("Assuming the Ti³⁺ fraction is proportional to the "
               "equilibrium vacancy concentration, a plot of ",
               _m(r"\ln f"), " against ", _m("1/T"),
               " is linear (", _m("R^2 = 0.992"), ") with slope"),
            _eq(r"\frac{d\ln f}{d(1/T)} = -\frac{E_a}{k_B}"
                r"\quad\Rightarrow\quad E_a = 0.23 \pm 0.01\ \text{eV}.",
                "eq:arrhenius"),
            _p("This value is far below the bulk vacancy formation "
               "energy predicted by hybrid DFT (≈ 4 eV), so the "
               "fraction measured here cannot be an equilibrium bulk "
               "property. It is more naturally read as the barrier for "
               "oxygen release from the surface in vacuum, with the "
               "reducing UHV environment and the entropy of the "
               "released O₂ lowering the effective cost."),
            _p("The information depth of the measurement, taken as three "
               "inelastic mean free paths of the Ti 2p photoelectrons "
               "(kinetic energy ≈ 1030 eV), is"),
            _eq(r"d = 3\lambda\cos\theta \approx 3 \times 2.1\ "
                r"\text{nm} \times \cos 0^\circ \approx 6\ \text{nm},",
                "eq:depth"),
            _p("so the Ti³⁺ signal originates from roughly the outermost "
               "16 anatase unit-cell layers (c = 9.5 Å, four TiO₂ layers "
               "per cell) of a 30 nm film. Angle-resolved measurements "
               "would discriminate surface from sub-surface vacancies."),

            _sec("Conclusions"),
            _items(
                "A constrained Ti 2p fit reliably separates Ti³⁺ at "
                "−1.7 eV from Ti⁴⁺.",
                "The Ti³⁺ fraction rises monotonically to 14.0 % at "
                "700 °C, i.e. TiO₁.₉₃.",
                "Vacancy formation has an apparent activation energy "
                "of 0.23 eV.",
            ),

            _sec("Acknowledgements", 1),
            _p("We thank the example beamline staff for support and the "
               "Example Research Council for funding."),
            _bib(
                ("alder2003", "R. Alder, \\emph{J. Illustr. Surf. Sci.} "
                              "\\textbf{48}, 53 (2003)."),
                ("brandt2010", "M. Brandt \\emph{et al.}, "
                               "\\emph{Example Appl. Surf. Anal.} "
                               "\\textbf{257}, 887 (2010)."),
                ("shirley1972", "D. Shirling, \\emph{Example Phys. Rev. B} "
                                "\\textbf{5}, 4709 (1972)."),
            ),
        ],
    )


# ------------------------------------------------------------ XRD / films

def xrd_nanoparticles() -> Document:
    """Materials characterisation: XRD, Scherrer, Williamson–Hall."""
    return Document(
        meta=_paper_meta("XRD of ZnO nanoparticles", "D. Crystal"),
        children=[
            Title(children=[Text(text=
                "Crystallite size and lattice strain in sol–gel ZnO "
                "nanoparticles from X-ray diffraction line-profile "
                "analysis")]),
            Author(children=[Text(text="D. Crystal and E. Rietveld")]),
            Affiliation(children=[Text(text=
                "School of Chemistry, Example University")]),
            Abstract(children=[Text(text=
                "ZnO nanoparticles were synthesised by a sol–gel route "
                "and calcined at 400, 600 and 800 °C. Powder X-ray "
                "diffraction confirms single-phase wurtzite (P6₃mc) with "
                "a = 3.2498 Å and c = 5.2066 Å. Crystallite sizes from the "
                "Scherrer equation (12–39 nm) are compared with a "
                "Williamson–Hall analysis (17–48 nm) that separates size "
                "and microstrain contributions to the line broadening; "
                "the microstrain falls from 2.3 × 10⁻³ to 0.4 × 10⁻³ and "
                "the grain-growth activation energy is about "
                "32 kJ mol⁻¹.")]),
            Keywords(children=[Text(text=
                "XRD · Scherrer · Williamson–Hall · ZnO · nanoparticles")]),

            _sec("Introduction"),
            _p("Line broadening in powder diffraction carries information "
               "on both the size of coherently scattering domains and on "
               "inhomogeneous strain ", Citation(keys=["klein1974"]),
               ". Separating the two requires analysing the angular "
               "dependence of the broadening."),

            _sec("Theory"),
            _p("Bragg's law relates the interplanar spacing ",
               _m("d_{hkl}"), " to the diffraction angle:"),
            _eq(r"n\lambda = 2 d_{hkl} \sin\theta.", "eq:bragg"),
            _p("For a hexagonal lattice with parameters ", _m("a"),
               " and ", _m("c"), ","),
            _eq(r"\frac{1}{d_{hkl}^2} = \frac{4}{3}\,"
                r"\frac{h^2+hk+k^2}{a^2} + \frac{l^2}{c^2}.", "eq:hex"),
            _p("The Scherrer equation estimates the volume-weighted mean "
               "crystallite size ", _m(r"D"), " from the "
               "instrument-corrected line width ", _m(r"\beta"),
               " (FWHM in radians of ", _m(r"2\theta"), "):"),
            _eq(r"D = \frac{K\lambda}{\beta\cos\theta},\qquad "
                r"\beta = \sqrt{\beta_{\text{obs}}^2 - "
                r"\beta_{\text{inst}}^2},", "eq:scherrer"),
            _p("with shape factor ", _m("K = 0.9"), ". Including a "
               "microstrain ", _m(r"\varepsilon"),
               " gives the Williamson–Hall relation"),
            _eq(r"\beta\cos\theta = \frac{K\lambda}{D} + "
                r"4\varepsilon\sin\theta,", "eq:wh"),
            _p("so that a plot of ", _m(r"\beta\cos\theta"), " against ",
               _m(r"4\sin\theta"), " has intercept ",
               _m(r"K\lambda/D"), " and slope ", _m(r"\varepsilon"), "."),

            _sec("Methods"),
            _ord_items(
                "Zinc acetate dihydrate (0.5 M) dissolved in ethanol at "
                "60 °C; diethanolamine added 1:1 as stabiliser.",
                "Gel dried at 120 °C for 12 h and ground in an agate "
                "mortar.",
                "Calcined 2 h in air at 400, 600 or 800 °C (5 °C/min).",
                "XRD: Cu Kα₁ (λ = 1.5406 Å), 2θ = 20–80°, step 0.01°. "
                "A LaB₆ standard (NIST SRM 660c) gave a constant "
                "instrumental FWHM of 0.08° over this range.",
            ),

            _sec("Results"),
            _p("All reflections in Table ", CrossRef(label="tab:peaks"),
               " index to wurtzite ZnO; the d-spacings follow from "
               "Eq. ", CrossRef(label="eq:hex", kind="eqref"),
               " with the refined lattice parameters below. Peaks "
               "narrow strongly with calcination temperature, and the "
               "high-angle reflections are broadened more than the low-"
               "angle ones, the signature of microstrain."),
            _tab([
                ["(hkl)", "2θ (°)", "d (Å)", "FWHM 400 °C (°)",
                 "FWHM 600 °C (°)", "FWHM 800 °C (°)"],
                ["(100)", "31.77", "2.814", "0.663", "0.366", "0.216"],
                ["(002)", "34.42", "2.603", "0.644", "0.382", "0.219"],
                ["(101)", "36.25", "2.476", "0.680", "0.385", "0.220"],
                ["(102)", "47.54", "1.911", "0.752", "0.446", "0.238"],
                ["(110)", "56.60", "1.625", "0.826", "0.466", "0.256"],
                ["(103)", "62.86", "1.477", "0.885", "0.491", "0.266"],
            ], "Indexed reflections of wurtzite ZnO and observed "
               "FWHM (not corrected for instrumental width).",
               "tab:peaks", "lrrrrr"),
            _p("Refined lattice parameters at 800 °C are ",
               _m(r"a = 3.2498(3)\ \text{Å}"), " and ",
               _m(r"c = 5.2066(5)\ \text{Å}"), ", giving ",
               _m(r"c/a = 1.602"), ", slightly below the ideal hexagonal "
               "close-packed value ", _m(r"\sqrt{8/3} = 1.633"),
               ", as is usual for wurtzite. Table ",
               CrossRef(label="tab:size"), " gives the Scherrer sizes "
               "(mean ± standard deviation over the six reflections) "
               "and the Williamson–Hall results."),
            _tab([
                ["Calcination (°C)", "D Scherrer (nm)", "D W–H (nm)",
                 "ε (×10⁻³)", "R² of W–H fit"],
                ["400", "11.8 ± 1.0", "16.8", "2.32", "0.959"],
                ["600", "21.0 ± 1.7", "29.2", "1.23", "0.929"],
                ["800", "39.2 ± 1.9", "48.3", "0.44", "0.990"],
            ], "Crystallite size and microstrain from line-profile "
               "analysis (K = 0.9).", "tab:size", "lrrrr"),

            _sec("Discussion"),
            _p("Scherrer sizes are systematically smaller than W–H "
               "values because the Scherrer approach attributes all "
               "broadening to size, including the strain contribution "
               "that grows with angle. The two converge as strain "
               "relaxes: the microstrain falls by a factor of five "
               "between 400 and 800 °C, consistent with annealing of "
               "grain-boundary defects. Taking the W–H sizes, isothermal "
               "grain growth from an initial size ", _m("D_0"),
               " follows"),
            _eq(r"D^n - D_0^n = k_0\, t\, \exp\!\left(-\frac{Q}{RT}"
                r"\right),", "eq:growth"),
            _p("and with ", _m("n = 2"), ", ", _m(r"D_0 = 5\ \text{nm}"),
               " (the dried gel) and the common 2 h hold, the three "
               "calcination temperatures give ",
               _m(r"Q \approx 32\ \text{kJ mol}^{-1}"),
               ". With only three temperatures this value is "
               "indicative; it is low compared with bulk Zn or O "
               "diffusion, as expected for surface-diffusion-controlled "
               "coarsening of loosely agglomerated particles."),

            _sec("Conclusion"),
            _p("Line-profile analysis of sol–gel ZnO shows crystallite "
               "growth from 17 to 48 nm and strain relief from 2.3 × "
               "10⁻³ to 0.4 × 10⁻³ between 400 and 800 °C. Scherrer and "
               "W–H sizes converge once strain becomes negligible."),
            _bib(
                ("klein1974", "H. Klein and L. Alexandrov, "
                              "\\emph{Powder Diffraction Procedures}, "
                              "2nd ed. (Example Press, 1974)."),
            ),
        ],
    )


# ------------------------------------------------------------------ DFT

def dft_study() -> Document:
    """Computational chemistry / DFT paper with convergence tables."""
    return Document(
        meta=_paper_meta("DFT study of CO on Pt(111)", "F. Kuhn"),
        children=[
            Title(children=[Text(text=
                "A density-functional study of CO adsorption on Pt(111): "
                "site preference, dispersion and the “CO/Pt puzzle”")]),
            Author(children=[Text(text="F. Kuhn and G. Schamm")]),
            Affiliation(children=[Text(text=
                "Department of Chemistry, Example University")]),
            Abstract(children=[Text(text=
                "We revisit the long-standing discrepancy between DFT "
                "and experiment for CO on Pt(111), where generalised-"
                "gradient functionals wrongly favour the threefold fcc "
                "hollow over the observed atop site. Using plane-wave "
                "calculations with PBE, RPBE, BEEF-vdW and the hybrid "
                "HSE06 we show that the site ordering follows the "
                "position of the CO 2π* level, and that in our hands "
                "HSE06 restores the atop preference by 0.09 eV. The "
                "calculated atop C–O stretch of 2081 cm⁻¹ is within "
                "10 cm⁻¹ of the measured value.")]),
            Keywords(children=[Text(text=
                "DFT · adsorption · Pt(111) · CO · hybrid functionals")]),

            _sec("Introduction"),
            _p("Kohn–Sham density-functional theory ",
               Citation(keys=["kuhn1965"]),
               " is the workhorse of surface chemistry, yet the simple "
               "case of CO on Pt(111) remains a known failure ",
               Citation(keys=["feldmann2001"]), ": GGA functionals "
               "overbind CO and place the molecule in a high-coordination "
               "site, whereas experiment finds atop adsorption at low "
               "coverage."),

            _sec("Computational details"),
            _p("The Kohn–Sham equations"),
            _eq(r"\left[-\frac{\hbar^2}{2m}\nabla^2 + v_{\text{ext}}"
                r"(\mathbf r) + v_{\text H}[n](\mathbf r) + "
                r"v_{\text{xc}}[n](\mathbf r)\right]\psi_i(\mathbf r) "
                r"= \varepsilon_i\,\psi_i(\mathbf r)", "eq:ks"),
            _p("were solved self-consistently with the density ",
               _m(r"n(\mathbf r) = \sum_i^{\text{occ}} "
                  r"|\psi_i(\mathbf r)|^2"),
               ". Adsorption energies are defined as"),
            _eq(r"E_{\text{ads}} = E_{\text{CO/Pt}} - E_{\text{Pt}} - "
                r"E_{\text{CO(g)}},", "eq:eads"),
            _p("so that negative values denote exothermic binding. "
               "Zero-point energies are not included."),
            _items(
                "Code: plane-wave PAW, cutoff 450 eV; PBE lattice "
                "constant of Pt 3.97 Å (HSE06: 3.92 Å; experiment 3.92 Å)",
                "Slab: 4-layer p(2×2) Pt(111) (0.25 ML CO), bottom two "
                "layers fixed, 15 Å vacuum, dipole correction",
                "k-points: 8×8×1 Monkhorst–Pack, Methfessel–Paxton "
                "smearing 0.1 eV",
                "Forces converged to 0.02 eV/Å",
                "HSE06: single points at PBE geometries on a 3-layer "
                "slab with a 4×4×1 mesh, since hybrid calculations on "
                "metals are costly",
            ),
            _sec("Convergence", 2),
            _p("Table ", CrossRef(label="tab:conv"), " shows that the "
               "450 eV, 8×8×1 setting is converged to 2 meV against "
               "the largest basis tested."),
            _tab([
                ["Cutoff (eV)", "k-mesh", "E(ads), atop (eV)", "Δ (meV)"],
                ["350", "6×6×1",   "−1.612", "31"],
                ["400", "6×6×1",   "−1.628", "15"],
                ["450", "8×8×1",   "−1.641", "2"],
                ["500", "10×10×1", "−1.643", "—"],
            ], "Convergence of the atop adsorption energy (PBE); Δ is "
               "the difference to the last row.",
               "tab:conv", "llrr"),

            _sec("Results"),
            _p("Table ", CrossRef(label="tab:eads"), " lists the "
               "adsorption energies. All three semilocal functionals "
               "prefer the hollow sites, by 0.16 eV (PBE) down to "
               "0.04 eV (BEEF-vdW), while HSE06 reverses the order."),
            _tab([
                ["Functional", "atop", "bridge", "hcp", "fcc",
                 "E(fcc) − E(atop)"],
                ["PBE",      "−1.64", "−1.72", "−1.78", "−1.80", "−0.16"],
                ["RPBE",     "−1.29", "−1.31", "−1.35", "−1.36", "−0.07"],
                ["BEEF-vdW", "−1.43", "−1.44", "−1.46", "−1.47", "−0.04"],
                ["HSE06",    "−1.52", "−1.47", "−1.44", "−1.43", "+0.09"],
                ["Expt.", "−1.3 to −1.5", "", "", "", "atop"],
            ], "Adsorption energies (eV) at 0.25 ML.",
               "tab:eads", "lrrrrr"),
            _p("Within the Blyholder picture the bond is described by "
               "5σ donation and 2π* back-donation. In a simple "
               "Newns–Anderson estimate the back-donation energy is"),
            _eq(r"E_{\text{back}} \approx -\,2f\,\frac{V_{2\pi^*}^2}"
                r"{\varepsilon_{2\pi^*}-\varepsilon_d},", "eq:newns"),
            _p("where ", _m(r"\varepsilon_d"), " is the d-band centre, ",
               _m("f"), " the d-band filling and ", _m(r"V_{2\pi^*}"),
               " the coupling matrix element. GGAs place ",
               _m(r"\varepsilon_{2\pi^*}"), " too low, which "
               "enlarges ", _m(r"|E_{\text{back}}|"),
               " and over-stabilises the multi-fold sites where "
               "back-donation is strongest. The hybrid functional lifts "
               "2π* and removes this bias."),
            _sec("Vibrational analysis", 2),
            _p("The C–O stretch frequency from the harmonic "
               "approximation is ",
               _m(r"\tilde\nu = \frac{1}{2\pi c}\sqrt{k/\mu}"),
               ", with reduced mass ", _m(r"\mu = 6.86\ \text{u}"),
               ". HSE06 gives 2081 cm⁻¹ for atop CO, i.e. a force "
               "constant of 1.75 kN/m, compared with the IRAS value of "
               "2090 cm⁻¹; PBE gives 2037 cm⁻¹."),

            _sec("Discussion"),
            _p("The energy differences between sites are of order "
               "0.1 eV, comparable to the spread between functionals, so "
               "the conclusion should be read with care: hybrid "
               "functionals also tend to exaggerate the d-band width of "
               "metals, and our HSE06 results use a thinner slab than "
               "the semilocal ones. A random-phase approximation "
               "calculation would be the natural independent check."),

            _sec("Conclusions"),
            _p("The CO/Pt puzzle is largely a self-interaction artefact: "
               "a hybrid functional corrects the 2π* position and "
               "restores the atop preference in these calculations."),
            _bib(
                ("kuhn1965", "F. Kuhn and G. Schamm, "
                             "\\emph{Example Phys. Rev.} "
                             "\\textbf{140}, A1133 (1965)."),
                ("feldmann2001", "P. Feldmann \\emph{et al.}, "
                                 "\\emph{J. Example Phys. Chem. B} "
                                 "\\textbf{105}, 4018 (2001)."),
            ),
        ],
    )


# ------------------------------------------------------- biomedical / RCT

def clinical_trial() -> Document:
    """Biomedical IMRaD paper: randomised controlled trial."""
    return Document(
        meta=_paper_meta("Randomised controlled trial", "H. Medic"),
        children=[
            Title(children=[Text(text=
                "Effect of a 12-week supervised exercise programme on "
                "HbA1c in adults with type 2 diabetes: a randomised "
                "controlled trial")]),
            Author(children=[Text(text=
                "H. Medic, I. Statistician and J. Nurse, "
                "on behalf of the MOVE-T2D investigators")]),
            Affiliation(children=[Text(text=
                "Department of Primary Care, Example University")]),
            Abstract(children=[Text(text=
                "Background: Structured exercise improves glycaemic "
                "control, but effect sizes in routine care are uncertain. "
                "Methods: 240 adults with type 2 diabetes (HbA1c 7.0–10.0 "
                "%) were randomised 1:1 to supervised exercise or usual "
                "care. The primary outcome was change in HbA1c at 12 "
                "weeks, analysed by intention to treat. Results: HbA1c "
                "fell by 0.62 % with exercise versus 0.11 % with usual "
                "care (adjusted difference −0.51 %; 95 % CI −0.70 to "
                "−0.32; p < 0.001). Conclusions: Supervised exercise "
                "produces a clinically meaningful reduction in HbA1c. "
                "Trial registration: ISRCTN00000000.")]),
            Keywords(children=[Text(text=
                "type 2 diabetes · exercise · RCT · HbA1c")]),

            _sec("Introduction"),
            _p("Type 2 diabetes affects more than 500 million adults "
               "worldwide ", Citation(keys=["atlas2021"]),
               ". Guidelines recommend 150 minutes of moderate activity "
               "per week, but adherence outside trials is poor. We "
               "tested whether a supervised programme delivered in "
               "routine primary care lowers HbA1c."),

            _sec("Methods"),
            _sec("Design and participants", 2),
            _p("Parallel-group, assessor-blinded randomised trial at "
               "four centres, reported according to the CONSORT 2010 "
               "statement ", Citation(keys=["schaefer2010"]),
               ". Randomisation was 1:1, computer-generated in blocks "
               "of 4 and 6, stratified by centre, with allocation "
               "concealed in sealed web-based envelopes."),
            _items(
                "Inclusion: age 40–75 y, type 2 diabetes for ≥ 1 y, "
                "HbA1c 7.0–10.0 %, stable medication for 3 months",
                "Exclusion: insulin therapy, unstable angina, "
                "eGFR < 30 mL/min/1.73 m²",
            ),
            _sec("Interventions", 2),
            _p("The exercise arm attended three supervised 60-minute "
               "sessions per week (aerobic and resistance training at "
               "moderate to vigorous intensity); usual care participants "
               "received standard advice and continued their usual "
               "routine."),
            _sec("Sample size", 2),
            _p("To detect a difference ", _m(r"\Delta = 0.4\,\%"),
               " with SD ", _m(r"\sigma = 0.9\,\%"),
               ", two-sided ", _m(r"\alpha = 0.05"), " and power 90 %:"),
            _eq(r"n = \frac{2\,(z_{1-\alpha/2}+z_{1-\beta})^2\,\sigma^2}"
                r"{\Delta^2} = \frac{2(1.96+1.28)^2(0.9)^2}{0.4^2} "
                r"\approx 107", "eq:n"),
            _p("per arm; inflating for 10 % attrition gives ",
               _m(r"107/0.9 \approx 119"), ", so 120 per arm were "
               "enrolled."),
            _sec("Statistical analysis", 2),
            _p("The primary analysis used ANCOVA on the intention-to-"
               "treat population, adjusting for baseline and centre:"),
            _eq(r"Y_{i,12} = \beta_0 + \beta_1\,\text{Tx}_i + "
                r"\beta_2\,Y_{i,0} + \sum_c \gamma_c\,\text{Centre}_{ic}"
                r" + \epsilon_i,", "eq:ancova"),
            _p("where ", _m(r"\beta_1"), " is the adjusted treatment "
               "effect. Missing data were handled by multiple "
               "imputation (", _m("m = 50"), ") under "
               "missing-at-random, and the results were combined with "
               "Rubin's rules. The binary secondary outcome (HbA1c "
               "< 7 %, non-completers counted as failures) is "
               "summarised by the risk difference and the number needed "
               "to treat."),

            _sec("Results"),
            _p("Of 351 adults assessed, 111 were excluded (64 did not "
               "meet the criteria, 38 declined and 9 had other reasons) "
               "and 240 were randomised, 120 per arm (Table ",
               CrossRef(label="tab:flow"), "). Follow-up was 90 % in the "
               "exercise arm and 93 % in the usual-care arm; all "
               "randomised participants were analysed."),
            _tab([
                ["Stage", "Exercise", "Usual care"],
                ["Randomised", "120", "120"],
                ["Withdrew before first session", "6", "0"],
                ["Withdrew after starting", "3", "5"],
                ["Relocated", "2", "2"],
                ["Adverse event (knee injury)", "1", "0"],
                ["Lost contact", "0", "1"],
                ["Assessed at week 12", "108", "112"],
                ["Analysed (intention to treat)", "120", "120"],
            ], "CONSORT participant flow after randomisation.",
               "tab:flow", "lcc"),
            _p("Baseline characteristics were balanced between arms "
               "(Table ", CrossRef(label="tab:base"), ")."),
            _tab([
                ["Characteristic", "Exercise (n = 120)",
                 "Usual care (n = 120)"],
                ["Age, y, mean (SD)", "58.4 (8.1)", "59.1 (7.9)"],
                ["Female, n (pct)", "53 (44)", "49 (41)"],
                ["BMI, kg/m², mean (SD)", "31.2 (4.6)", "30.8 (4.9)"],
                ["Diabetes duration, y, mean (SD)", "7.2 (4.8)",
                 "6.9 (5.1)"],
                ["HbA1c, per cent, mean (SD)", "8.12 (0.81)",
                 "8.09 (0.78)"],
                ["Metformin, n (pct)", "104 (87)", "107 (89)"],
            ], "Baseline characteristics.", "tab:base", "lcc"),
            _p("Table ", CrossRef(label="tab:out"), " gives the "
               "outcomes at 12 weeks. The adjusted HbA1c difference "
               "was −0.51 percentage points (95 % CI −0.70 to −0.32); "
               "a complete-case sensitivity analysis gave −0.55 "
               "(−0.75 to −0.35)."),
            _tab([
                ["Outcome", "Exercise", "Usual care",
                 "Adj. difference (CI)", "p"],
                ["HbA1c (change, per cent)", "−0.62", "−0.11",
                 "−0.51 (−0.70, −0.32)", "< 0.001"],
                ["Fasting glucose (mmol/L)", "−0.9", "−0.2",
                 "−0.7 (−1.1, −0.3)", "< 0.001"],
                ["Weight (kg)", "−2.1", "−0.4", "−1.7 (−2.6, −0.8)",
                 "< 0.001"],
                ["VO₂max (mL/kg/min)", "+3.4", "+0.3", "+3.1 (2.2, 4.0)",
                 "< 0.001"],
            ], "Primary and secondary outcomes at 12 weeks (mean change "
               "from baseline).", "tab:out", "lrrrr"),
            _p("HbA1c below 7 % was reached by 37 of 120 (30.8 %) "
               "participants with exercise and 14 of 120 (11.7 %) with "
               "usual care. The risk difference was 19.2 percentage "
               "points (95 % CI 9.1 to 29.3), so"),
            _eq(r"\text{NNT} = \frac{1}{\text{ARR}} = \frac{1}{0.192} "
                r"= 5.2 \;\to\; 6,", "eq:nnt"),
            _p("rounded up as is conventional (95 % CI 4 to 11). Nine "
               "musculoskeletal complaints were reported with exercise "
               "and three with usual care; no serious adverse events "
               "were related to the intervention."),

            _sec("Discussion"),
            _p("The observed effect exceeds the 0.3–0.4 % threshold "
               "usually considered clinically relevant, and the "
               "confidence interval excludes it from below. Limitations "
               "include the short follow-up and the impossibility of "
               "blinding participants; whether the benefit persists "
               "after supervision ends requires longer follow-up."),
            _sec("Declarations", 2),
            _items(
                "Ethics: approved by the regional ethics committee "
                "(REC 00/XX/0000); all participants gave written consent.",
                "Data availability: de-identified data available on "
                "reasonable request.",
                "Competing interests: none declared.",
            ),
            _bib(
                ("atlas2021", "Example Diabetes Federation, "
                              "\\emph{Global Diabetes Atlas}, 10th ed. "
                              "(2021)."),
                ("schaefer2010", "K. Schaefer, D. Altmann and D. Moore, "
                                 "\\emph{Example Med. J.} "
                                 "\\textbf{340}, c332 (2010)."),
            ),
        ],
    )


# ------------------------------------------------------------ physics

def quantum_notes() -> Document:
    """Theoretical physics: perturbation theory worked through."""
    return Document(
        meta=_paper_meta("Perturbation theory", "K. Dirk"),
        children=[
            Title(children=[Text(text=
                "Time-independent perturbation theory and the "
                "anharmonic oscillator")]),
            Author(children=[Text(text="K. Dirk")]),
            Affiliation(children=[Text(text=
                "Advanced Quantum Mechanics, Lecture 7")]),

            _sec("Setting up the problem"),
            _p("We seek eigenstates of ", _m(r"H = H_0 + \lambda V"),
               " where the spectrum of ", _m("H_0"), " is known, ",
               _m(r"H_0|n^{(0)}\rangle = E_n^{(0)}|n^{(0)}\rangle"),
               " with non-degenerate levels, and ", _m(r"\lambda"),
               " is small. Expanding"),
            _eq(r"E_n = E_n^{(0)} + \lambda E_n^{(1)} + \lambda^2 "
                r"E_n^{(2)} + \cdots,\qquad |n\rangle = |n^{(0)}\rangle "
                r"+ \lambda|n^{(1)}\rangle + \cdots", "eq:expand"),
            _p("in the Schrödinger equation and collecting powers of ",
               _m(r"\lambda"), " gives"),
            _eq(r"E_n^{(1)} = \langle n^{(0)}|V|n^{(0)}\rangle,", "eq:e1"),
            _eq(r"E_n^{(2)} = \sum_{m\neq n}\frac{|\langle m^{(0)}|V|"
                r"n^{(0)}\rangle|^2}{E_n^{(0)}-E_m^{(0)}}.", "eq:e2"),
            _p("Note that ", CrossRef(label="eq:e2", kind="eqref"),
               " is always negative for the ground state: second-order "
               "corrections push the lowest level down."),
            Theorem(kind="remark", title="Parity", children=[Text(text=
                "If H₀ and V have definite parity, the first-order "
                "shift of a state of definite parity vanishes for any "
                "odd V, because the integrand is odd.")]),

            _sec("The quartic oscillator"),
            _p("Take ", _m(r"H_0 = \hbar\omega(a^\dagger a + \tfrac12)"),
               " and ", _m(r"V = x^4"), " with ",
               _m(r"x = \sqrt{\hbar/2m\omega}\,(a + a^\dagger)"),
               ". Using ", _m(r"a|n\rangle = \sqrt n|n-1\rangle"),
               " one finds"),
            _eq(r"\langle n|(a+a^\dagger)^4|n\rangle = 6n^2 + 6n + 3,",
                "eq:x4"),
            _p("so the first-order shift is"),
            _eq(r"E_n^{(1)} = \frac{3\hbar^2}{4m^2\omega^2}"
                r"\left(2n^2 + 2n + 1\right).", "eq:shift"),
            _p("The non-zero off-diagonal elements connect ",
               _m(r"n"), " to ", _m(r"n\pm2"), " and ", _m(r"n\pm4"),
               ". For the ground state, in units ",
               _m(r"\hbar=m=\omega=1"), ", the only non-zero elements "
               "are ", _m(r"\langle 2|x^4|0\rangle = 3\sqrt2/2"),
               " and ", _m(r"\langle 4|x^4|0\rangle = \sqrt6/2"),
               ", so by ", CrossRef(label="eq:e2", kind="eqref"),
               " the second-order shift is ",
               _m(r"-\frac{9/2}{2} - \frac{3/2}{4} = -\frac{21}{8}"),
               ". Restoring units,"),
            _eq(r"E_0 = \frac{\hbar\omega}{2} + \frac{3\lambda\hbar^2}"
                r"{4m^2\omega^2} - \frac{21\lambda^2\hbar^3}{8m^4"
                r"\omega^5} + \mathcal O(\lambda^3).", "eq:e0"),
            _p("Table ", CrossRef(label="tab:quartic"), " compares the "
               "series with the numerically exact ground-state energy "
               "(diagonalisation in 80 oscillator states)."),
            Table(rows=[
                ["λ", "Exact", "First order", "Second order",
                 "Third order"],
                ["0.01", "0.50726", "0.50750", "0.50724", "0.50726"],
                ["0.05", "0.53264", "0.53750", "0.53094", "0.53354"],
                ["0.1",  "0.55915", "0.57500", "0.54875", "0.56956"],
                ["0.5",  "0.69618", "0.87500", "0.21875", "2.82031"],
            ], caption="Ground-state energy of H = p²/2 + x²/2 + λx⁴ "
                       "(ħ = m = ω = 1). The third-order coefficient is "
                       "333/16.",
               label="tab:quartic", alignment="lrrrr", style="booktabs",
               header=True),
            _p("For small ", _m(r"\lambda"), " each order improves the "
               "result, but at ", _m(r"\lambda=0.5"), " the series "
               "diverges: the partial sums oscillate and grow."),

            _sec("Degenerate case"),
            _p("If ", _m(r"E^{(0)}"), " is ", _m("g"),
               "-fold degenerate, diagonalise ", _m("V"),
               " within the degenerate subspace:"),
            _eq(r"\det\left[\langle n_i^{(0)}|V|n_j^{(0)}\rangle - "
                r"E^{(1)}\delta_{ij}\right] = 0.", "eq:secular"),
            _p("The linear Stark effect in hydrogen ",
               _m("n = 2"), " is the classic example: the field mixes ",
               _m("2s"), " and ", _m("2p_0"),
               ", with ", _m(r"\langle 2s|z|2p_0\rangle = -3a_0"),
               ", so the two mixed states are shifted by ",
               _m(r"\pm 3 e a_0 \mathcal E"), " while ",
               _m(r"2p_{\pm1}"), " are unshifted."),
            Theorem(kind="example", title="Coupled oscillators", children=[
                Text(text="For the 2D isotropic oscillator perturbed by "
                          "λxy, the first excited level (energy 2ħω) is "
                          "twofold degenerate. In the basis |1,0⟩, "
                          "|0,1⟩ the perturbation matrix is "
                          "(ħ/2mω) times the 2×2 matrix with zeros on the "
                          "diagonal and ones off it, so the first-order "
                          "shifts are ±ħ/2mω. This agrees with the exact "
                          "normal-mode frequencies "
                          "ω² ± λ/m expanded to first order.")]),

            _sec("Validity"),
            _p("The series is asymptotic, not convergent. Dyson's "
               "argument ", Citation(keys=["dyson1952"]),
               " shows that for ", _m(r"\lambda < 0"),
               " the potential is unbounded below, so ",
               _m(r"E(\lambda)"), " cannot be analytic at ",
               _m(r"\lambda = 0"), ", and the coefficients grow "
               "factorially. Optimal truncation is at the smallest "
               "term, where the error is of the order of that term."),

            _sec("Problems"),
            _ord_items(
                "Show that the first-order shift for V = x³ vanishes "
                "for every n.",
                "For V = κx show that the second-order shift is "
                "−κ²/(2mω²) for every n, and that it equals the exact "
                "shift obtained by completing the square.",
                "For V = x³, in units ħ = m = ω = 1, show that the second-order "
                "ground-state shift is −11/8.",
                "Find the first-order splitting of the n = 2 level of "
                "the 2D isotropic oscillator under λxy.",
            ),
            _bib(
                ("dyson1952", "F. Dysen, \\emph{Example Phys. Rev.} "
                              "\\textbf{85}, 631 (1952)."),
            ),
        ],
    )


# ------------------------------------------------------ electrochemistry

def battery_paper() -> Document:
    """Electrochemistry / energy materials paper."""
    return Document(
        meta=_paper_meta("Li-ion cathode study", "L. Volta"),
        children=[
            Title(children=[Text(text=
                "Al-doped LiNi₀.₈Mn₀.₁Co₀.₁O₂ cathodes with improved "
                "cycling stability at 4.4 V")]),
            Author(children=[Text(text="L. Volta, M. Farrady and N. Nernst")]),
            Affiliation(children=[Text(text=
                "Energy Materials Group, Example University")]),
            Abstract(children=[Text(text=
                "Ni-rich layered oxides offer high capacity but suffer "
                "from capacity fade above 4.3 V. We show that 1 mol % Al "
                "doping of NMC811 raises capacity retention after 300 "
                "cycles at 1C from 71.3 % to 89.1 %, and reduces the "
                "growth of the charge-transfer resistance by a factor of "
                "three. Galvanostatic intermittent titration shows that "
                "Li⁺ diffusion is unaffected by doping.")]),
            Keywords(children=[Text(text=
                "lithium-ion battery · NMC811 · doping · impedance · GITT")]),

            _sec("Introduction"),
            _p("The energy density of a cell scales with the product of "
               "specific capacity and average voltage,"),
            _eq(r"E = \int_0^{Q} V(q)\,dq \approx Q\,\bar V,", "eq:energy"),
            _p("which motivates Ni-rich cathodes ",
               Citation(keys=["mantel2020"]), ". Their drawback is the "
               "H2→H3 phase transition near 4.2 V, which collapses the "
               "c-axis, cracks secondary particles and exposes fresh "
               "surface to the electrolyte."),

            _sec("Experimental"),
            _items(
                "Co-precipitation of Ni₀.₈Mn₀.₁Co₀.₁(OH)₂, Al(NO₃)₃ "
                "added to 1 mol %",
                "Lithiation with LiOH·H₂O (5 % excess), 750 °C, "
                "12 h, O₂ flow",
                "Electrodes: 90:5:5 active:C65:PVDF, 10 mg/cm²",
                "CR2032 half-cells vs Li, 1 M LiPF₆ in EC:EMC 3:7; "
                "cycled between 2.8 and 4.4 V (1C = 200 mA/g)",
            ),

            _sec("Results and discussion"),
            _sec("Structure and cycling", 2),
            _p("Rietveld refinement shows a well-ordered layered "
               "structure for both powders, with an intensity ratio ",
               _m(r"I_{003}/I_{104}"), " of 1.62 (undoped) and 1.58 "
               "(doped), both above the usual 1.2 threshold for low "
               "Li/Ni mixing. Table ", CrossRef(label="tab:cycle"),
               " summarises the electrochemical performance."),
            _tab([
                ["Sample", "Q 0.1C", "ICE", "Q 5C", "Q₁ 1C", "Q₃₀₀ 1C",
                 "Retention"],
                ["NMC811", "214", "88.1", "142", "188", "134", "71.3"],
                ["Al-NMC811", "209", "89.4", "151", "184", "164", "89.1"],
            ], "Electrochemical performance, 2.8–4.4 V. Capacities Q in mAh/g "
               "(Q₁ and Q₃₀₀: first and 300th cycle at 1C); ICE, the initial "
               "Coulombic efficiency, and retention Q₃₀₀/Q₁ in per cent.", "tab:cycle", "lrrrrrr"),
            _p("Aluminium is electrochemically inactive, which explains "
               "the 2 % lower initial capacity of the doped material "
               "(209 against 214 mAh/g), but the doped cathode wins "
               "after prolonged cycling."),
            _sec("Impedance", 2),
            _p("Nyquist spectra were fitted to a Randles circuit with "
               "Warburg element:"),
            _eq(r"Z(\omega) = R_s + \frac{R_{ct} + Z_W}{1 + j\omega "
                r"C_{dl}(R_{ct}+Z_W)},\qquad Z_W = \frac{\sigma_W}"
                r"{\sqrt\omega}(1-j).", "eq:randles"),
            _p("After 300 cycles ", _m("R_{ct}"),
               " grew from 18 to 142 Ω for undoped and from 16 to "
               "54 Ω for doped material, an increase of 124 Ω against "
               "38 Ω, i.e. a factor 3.3 smaller."),
            _sec("Diffusion", 2),
            _p("From GITT, the chemical diffusion coefficient is ",
               Citation(keys=["weber1977"]), ":"),
            _eq(r"\tilde D = \frac{4}{\pi\tau}\left(\frac{m_B V_M}"
                r"{M_B S}\right)^2\left(\frac{\Delta E_s}"
                r"{\Delta E_\tau}\right)^2,", "eq:gitt"),
            _p("where ", _m(r"\tau"), " is the pulse length, ",
               _m("m_B"), ", ", _m("M_B"), " and ", _m("V_M"),
               " the mass, molar mass and molar volume of the active "
               "material, ", _m("S"), " the electrode–electrolyte "
               "area and ", _m(r"\Delta E_s"), " and ",
               _m(r"\Delta E_\tau"), " the steady-state and transient "
               "voltage changes. This yields ",
               _m(r"\tilde D \approx 3\times10^{-11}"),
               " cm²/s for both materials at 50 % state of charge."),
            _sec("Thermodynamics", 2),
            _p("The open-circuit voltage relates to the Gibbs energy "
               "via ", _m(r"\Delta G = -nFE"),
               ", and its temperature coefficient gives the entropy "
               "change and hence the reversible heat:"),
            _eq(r"\Delta S = nF\left(\frac{\partial E}{\partial T}"
                r"\right)_p.", "eq:entropy"),

            _sec("Conclusions"),
            _p("Al doping suppresses the H2→H3 phase transition and "
               "surface reconstruction, giving 89.1 % retention at "
               "4.4 V without compromising rate capability (151 against "
               "142 mAh/g at 5C)."),
            _bib(
                ("mantel2020", "A. Mantel, \\emph{Example Energy Commun.} "
                               "\\textbf{11}, 1550 (2020)."),
                ("weber1977", "W. Weber and R. Hughes, "
                              "\\emph{J. Example Electrochem. Soc.} "
                              "\\textbf{124}, 1569 (1977)."),
            ),
        ],
    )


# ----------------------------------------------------------- ecology / stats

def ecology_field_study() -> Document:
    """Ecology field study with mixed models and diversity indices."""
    return Document(
        meta=_paper_meta("Pollinator diversity", "O. Darwen"),
        children=[
            Title(children=[Text(text=
                "Wildflower margins increase pollinator diversity on "
                "arable farms: a three-year paired-field study")]),
            Author(children=[Text(text="O. Darwen and P. Wallis")]),
            Affiliation(children=[Text(text=
                "Department of Ecology, Example University")]),
            Abstract(children=[Text(text=
                "We surveyed pollinators on 24 paired fields (sown "
                "wildflower margin vs conventional grass margin) over "
                "three summers. Margins increased Shannon diversity by "
                "0.41 (95 % CI 0.28–0.54) and bumblebee abundance by "
                "a factor of 2.3. Effects strengthened with margin age: "
                "the margin advantage grew by 20 % per year "
                "(Margin × Year interaction, p = 0.003).")]),
            Keywords(children=[Text(text=
                "pollinators · agri-environment · biodiversity · GLMM")]),

            _sec("Introduction"),
            _p("Insect pollinators have declined across Europe ",
               Citation(keys=["pitt2010"]),
               ". Agri-environment schemes fund flower-rich margins, "
               "but evidence for their effect on diversity is mixed."),

            _sec("Methods"),
            _sec("Survey design", 2),
            _p("Each of 24 farms contributed one treatment and one "
               "control field ≥ 500 m apart. Pollinators were recorded "
               "along fixed 100 m transects (6 visits per year for "
               "three years, 10:00–16:00, > 15 °C, wind below Beaufort "
               "4), giving 864 transect walks and about 43 000 "
               "individuals of 58 taxa."),
            _sec("Diversity indices", 2),
            _p("With ", _m("p_i"), " the proportion of individuals in "
               "species ", _m("i"), " of ", _m("S"), " species:"),
            _eq(r"H' = -\sum_{i=1}^{S} p_i \ln p_i,\qquad "
                r"D = 1 - \sum_{i=1}^{S} p_i^2,\qquad "
                r"J' = \frac{H'}{\ln S}.", "eq:div"),
            _sec("Statistical model", 2),
            _p("Abundance counts were modelled with a negative-binomial "
               "GLMM with farm (", _m("i"), ") and field within farm (",
               _m("j"), ") as random intercepts and year ", _m("t"),
               " centred on the second summer:"),
            _eq(r"\log \mu_{ijt} = \beta_0 + \beta_1\,\text{Margin}_{ij}"
                r" + \beta_2\,\text{Year}_t + \beta_3\,(\text{Margin}"
                r"\times\text{Year})_{ijt} + u_i + v_{ij},\quad "
                r"u_i\sim\mathcal N(0,\sigma_u^2).", "eq:glmm"),
            _p("so that ", _m(r"e^{\beta_1}"), " is the abundance ratio "
               "in the middle year. Diversity indices, which are "
               "continuous, used the same structure with a Gaussian "
               "response. The six endpoints in Table ",
               CrossRef(label="tab:eco"),
               " were corrected with the Holm procedure."),

            _sec("Results"),
            _tab([
                ["Metric", "Control", "Margin", "Ratio / diff.", "p"],
                ["Total abundance", "31.2", "68.9", "×2.21", "< 0.001"],
                ["Bumblebees", "8.4", "19.3", "×2.30", "< 0.001"],
                ["Hoverflies", "12.1", "22.7", "×1.88", "< 0.001"],
                ["Species richness", "9.8", "15.4", "+5.6", "< 0.001"],
                ["Shannon H'", "1.72", "2.13", "+0.41", "< 0.001"],
                ["Pielou J'", "0.75", "0.78", "+0.03", "0.21"],
            ], "Mean per transect walk, pooled over years.",
               "tab:eco", "lrrrr"),
            _p("The Margin × Year interaction was positive (",
               _m(r"\beta_3 = 0.18 \pm 0.06"), ", ", _m("p = 0.003"),
               "), indicating that the margin advantage multiplied by ",
               _m(r"e^{0.18} = 1.20"), " per year as sown species "
               "established."),

            _sec("Discussion"),
            _p("Evenness was unchanged (Pielou J' rose by only 0.03), "
               "so the diversity gain comes from additional species "
               "rather than redistribution. "
               "Landscape context was not controlled", Footnote(children=[
                   Text(text="Semi-natural habitat within 1 km ranged "
                             "from 3 % to 21 %.")]),
               ", which may explain between-farm variance "
               "(", _m(r"\hat\sigma_u = 0.34"), ")."),
            _bib(
                ("pitt2010", "S. G. Pitt \\emph{et al.}, \\emph{Example "
                             "Trends Ecol. Evol.} \\textbf{25}, 345 "
                             "(2010)."),
            ),
        ],
    )
