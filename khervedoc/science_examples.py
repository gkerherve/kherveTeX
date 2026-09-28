"""Scientific examples shown under Examples > Scientific.

Each is a realistic, multi-page research document written the way a
working scientist would: real equations, fitted-parameter tables,
uncertainty budgets and a short bibliography — so a new user sees how
their own field's paper looks in KherveTeX, not a lorem-ipsum stub.
"""
from __future__ import annotations

import re

from .example_helpers import _items, _meta, _ord_items, _p
from .model import (
    Abstract, Author, Citation, CrossRef, DEFAULT_PACKAGES, Document,
    Footnote, Keywords, MathBlock, MathInline, RawLatex, Section, Table,
    Text, Title,
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
                "A. Surface¹, B. Vacuum¹, C. Synchrotron² — "
                "¹Department of Materials, ²Diamond Light Source")]),
            Abstract(children=[Text(text=
                "Anatase TiO₂ films grown by atomic layer deposition were "
                "annealed in ultra-high vacuum between 300 and 700 °C and "
                "analysed in situ by monochromated Al Kα XPS. Peak fitting "
                "of the Ti 2p region with spin–orbit-constrained doublets "
                "on a Shirley background resolves a Ti³⁺ component shifted "
                "by −1.7 eV from Ti⁴⁺, whose fraction rises from 2 % to "
                "14 % with annealing temperature. The O 1s spectra show a "
                "concurrent growth of a hydroxyl / defect component at "
                "531.3 eV. An Arrhenius analysis yields an apparent "
                "activation energy of 0.62 ± 0.05 eV for vacancy formation.")]),
            Keywords(children=[Text(text=
                "XPS · TiO₂ · oxygen vacancies · peak fitting · "
                "Shirley background")]),

            _sec("Introduction"),
            _p("Titanium dioxide is the archetypal photocatalyst, and "
               "its activity is governed to a large extent by point "
               "defects at the surface ",
               Citation(keys=["diebold2003"]), ". Removal of lattice "
               "oxygen leaves two excess electrons that localise on "
               "neighbouring Ti sites, producing Ti³⁺ centres with a "
               "characteristic chemical shift in the Ti 2p spectrum ",
               Citation(keys=["biesinger2010"]), ". Quantifying that "
               "component reliably requires a physically constrained fit; "
               "in this work we describe a protocol and apply it to a "
               "temperature series."),

            _sec("Experimental"),
            _sec("Sample preparation", 2),
            _p("Films of nominal thickness 30 nm were grown on Si(100) "
               "by thermal ALD from TiCl₄ and H₂O at 250 °C (600 cycles) "
               "and crystallised to anatase by a 1 h anneal in air at "
               "450 °C, confirmed by Raman (144 cm⁻¹ E_g mode)."),
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
               "shape, a Gaussian–Lorentzian product with mixing "
               "parameter ", _m(r"\eta"), ":"),
            _eq(r"I(E) = A\left[\eta\,\frac{1}{1+4\left(\frac{E-E_0}"
                r"{\beta}\right)^2} + (1-\eta)\,\exp\!\left(-4\ln 2"
                r"\left(\frac{E-E_0}{\beta}\right)^2\right)\right]",
                "eq:pv"),
            _p("The inelastic background was removed with the iterative "
               "Shirley algorithm ", Citation(keys=["shirley1972"]),
               ", in which the background at energy ", _m("E"),
               " is proportional to the integrated peak area at lower "
               "binding energy:"),
            _eq(r"B(E) = B_{\text{low}} + (B_{\text{high}}-B_{\text{low}})"
                r"\,\frac{\int_{E}^{E_{\text{high}}} [I(E')-B(E')]\,dE'}"
                r"{\int_{E_{\text{low}}}^{E_{\text{high}}} "
                r"[I(E')-B(E')]\,dE'}.", "eq:shirley"),
            _p("For the Ti 2p doublet the 2p₁/₂ component was tied to "
               "2p₃/₂ with a spin–orbit splitting of 5.72 eV and an "
               "area ratio fixed at the degeneracy ratio"),
            _eq(r"\frac{A(2p_{1/2})}{A(2p_{3/2})} = "
                r"\frac{2j_{1/2}+1}{2j_{3/2}+1} = \frac{1}{2}.", "eq:ratio"),
            _p("Atomic concentrations follow from the fitted areas and "
               "the Scofield relative sensitivity factors ",
               _m(r"S_i"), ":"),
            _eq(r"x_i = \frac{A_i / S_i}{\sum_j A_j / S_j}.", "eq:quant"),

            _sec("Results"),
            _p("Table ", CrossRef(label="tab:ti2p"),
               " lists the fitted Ti 2p₃/₂ parameters. The Ti⁴⁺ position "
               "is stable to within 0.05 eV across the series, confirming "
               "that charge referencing is not responsible for the "
               "apparent new component."),
            Table(rows=[
                ["Anneal (°C)", "Ti⁴⁺ BE (eV)", "Ti³⁺ BE (eV)",
                 "FWHM Ti⁴⁺ (eV)", "Ti³⁺ fraction (%)"],
                ["as-grown", "458.72", "—",      "0.98", "< 1"],
                ["300",      "458.70", "457.02", "0.99", "2.1"],
                ["400",      "458.69", "457.00", "1.01", "4.8"],
                ["500",      "458.68", "456.98", "1.03", "7.9"],
                ["600",      "458.66", "456.97", "1.06", "11.2"],
                ["700",      "458.65", "456.95", "1.09", "14.0"],
            ], caption="Ti 2p₃/₂ fit results (Shirley background, "
                       "pseudo-Voigt, η = 0.3).",
               label="tab:ti2p", alignment="lrrrr", style="booktabs"),
            _p("The O 1s envelope requires three components: lattice "
               "O²⁻ at 530.0 eV, OH / O-vacancy-adjacent at 531.3 eV and "
               "adsorbed H₂O at 532.6 eV (Table ",
               CrossRef(label="tab:o1s"), ")."),
            Table(rows=[
                ["Component", "BE (eV)", "FWHM (eV)", "Area 300 °C (%)",
                 "Area 700 °C (%)"],
                ["O–Ti (lattice)", "530.0", "1.10", "88.5", "79.2"],
                ["OH / defect",    "531.3", "1.45", "9.1",  "18.3"],
                ["H₂O (ads.)",     "532.6", "1.60", "2.4",  "2.5"],
            ], caption="O 1s component analysis.", label="tab:o1s",
               alignment="lrrrr", style="booktabs"),

            _sec("Discussion"),
            _p("Assuming the Ti³⁺ fraction is proportional to the "
               "equilibrium vacancy concentration, an Arrhenius plot of ",
               _m(r"\ln x_{\mathrm{Ti^{3+}}}"), " against ", _m("1/T"),
               " is linear (", _m("R^2 = 0.991"), ") with slope"),
            _eq(r"\frac{d\ln x}{d(1/T)} = -\frac{E_a}{k_B}"
                r"\quad\Rightarrow\quad E_a = 0.62 \pm 0.05\ \text{eV}.",
                "eq:arrhenius"),
            _p("This value is smaller than the bulk vacancy formation "
               "energy predicted by hybrid DFT (≈ 4 eV), as expected for "
               "a surface process assisted by the reducing UHV "
               "environment and by the entropy of released O₂."),
            _p("The information depth of the measurement, taken as three "
               "inelastic mean free paths, is"),
            _eq(r"d = 3\lambda\cos\theta \approx 3 \times 2.1\ "
                r"\text{nm} \times \cos 0^\circ \approx 6\ \text{nm},",
                "eq:depth"),
            _p("so the Ti³⁺ signal originates from the outermost ~20 "
               "atomic layers. Angle-resolved measurements would "
               "discriminate surface from sub-surface vacancies."),

            _sec("Conclusions"),
            _items(
                "A constrained Ti 2p fit reliably separates Ti³⁺ at "
                "−1.7 eV from Ti⁴⁺.",
                "Ti³⁺ fraction rises monotonically to 14 % at 700 °C.",
                "Vacancy formation has an apparent activation energy "
                "of 0.62 eV.",
            ),

            _sec("Acknowledgements", 1),
            _p("We thank the Diamond Light Source for beamtime "
               "(proposal SI00000) and the EPSRC for funding."),
            _bib(
                ("diebold2003", "U. Diebold, \\emph{Surf. Sci. Rep.} "
                                "\\textbf{48}, 53 (2003)."),
                ("biesinger2010", "M. C. Biesinger \\emph{et al.}, "
                                  "\\emph{Appl. Surf. Sci.} \\textbf{257}, "
                                  "887 (2010)."),
                ("shirley1972", "D. A. Shirley, \\emph{Phys. Rev. B} "
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
            Author(children=[Text(text="D. Crystal, E. Rietveld")]),
            Abstract(children=[Text(text=
                "ZnO nanoparticles were synthesised by a sol–gel route "
                "and calcined at 400–800 °C. Powder X-ray diffraction "
                "confirms single-phase wurtzite (P6₃mc). Crystallite "
                "sizes obtained from the Scherrer equation (14–46 nm) "
                "are compared with a Williamson–Hall analysis that "
                "separates size and microstrain contributions to the "
                "line broadening.")]),
            Keywords(children=[Text(text=
                "XRD · Scherrer · Williamson–Hall · ZnO · nanoparticles")]),

            _sec("Introduction"),
            _p("Line broadening in powder diffraction carries information "
               "on both the size of coherently scattering domains and on "
               "inhomogeneous strain ", Citation(keys=["klug1974"]),
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
            _p("The Scherrer equation estimates the mean crystallite "
               "size ", _m(r"D"), " from the instrument-corrected "
               "integral breadth ", _m(r"\beta"), ":"),
            _eq(r"D = \frac{K\lambda}{\beta\cos\theta},\qquad "
                r"\beta = \sqrt{\beta_{\text{obs}}^2 - "
                r"\beta_{\text{inst}}^2},", "eq:scherrer"),
            _p("with shape factor ", _m("K = 0.9"), ". Including a "
               "microstrain ", _m(r"\varepsilon"),
               " gives the Williamson–Hall relation"),
            _eq(r"\beta\cos\theta = \frac{K\lambda}{D} + "
                r"4\varepsilon\sin\theta,", "eq:wh"),
            _p("so that a plot of ", _m(r"\beta\cos\theta"), " vs ",
               _m(r"4\sin\theta"), " has intercept ",
               _m(r"K\lambda/D"), " and slope ", _m(r"\varepsilon"), "."),

            _sec("Methods"),
            _ord_items(
                "Zinc acetate dihydrate (0.5 M) dissolved in ethanol at "
                "60 °C; diethanolamine added 1:1 as stabiliser.",
                "Gel dried at 120 °C for 12 h and ground in an agate "
                "mortar.",
                "Calcined 2 h in air at 400, 600 or 800 °C (5 °C/min).",
                "XRD: Cu Kα₁ (λ = 1.5406 Å), 2θ = 20–80°, step 0.01°, "
                "LaB₆ (NIST SRM 660c) for instrumental broadening.",
            ),

            _sec("Results"),
            Table(rows=[
                ["(hkl)", "2θ (°)", "d (Å)", "FWHM 400 °C (°)",
                 "FWHM 800 °C (°)"],
                ["(100)", "31.77", "2.814", "0.612", "0.198"],
                ["(002)", "34.42", "2.603", "0.590", "0.191"],
                ["(101)", "36.25", "2.476", "0.628", "0.205"],
                ["(102)", "47.54", "1.911", "0.701", "0.228"],
                ["(110)", "56.60", "1.625", "0.742", "0.244"],
                ["(103)", "62.86", "1.477", "0.801", "0.262"],
            ], caption="Indexed reflections of wurtzite ZnO.",
               label="tab:peaks", alignment="lrrrr", style="booktabs"),
            _p("Refined lattice parameters at 800 °C are ",
               _m(r"a = 3.2498(3)\ \text{Å}"), " and ",
               _m(r"c = 5.2066(5)\ \text{Å}"), ", giving ",
               _m(r"c/a = 1.602"), ", close to the ideal ",
               _m(r"\sqrt{8/3} = 1.633"), "."),
            Table(rows=[
                ["Calcination (°C)", "D Scherrer (nm)", "D W–H (nm)",
                 "ε (×10⁻³)", "R²"],
                ["400", "14.2", "17.8", "2.41", "0.962"],
                ["600", "26.5", "29.3", "1.12", "0.978"],
                ["800", "45.8", "48.1", "0.37", "0.954"],
            ], caption="Size and strain from Eqs. (4) and (5).",
               label="tab:size", alignment="lrrrr", style="booktabs"),

            _sec("Discussion"),
            _p("Scherrer sizes are systematically smaller than W–H "
               "values because the Scherrer approach attributes all "
               "broadening to size. The strain relaxes by a factor of "
               "six on calcination, consistent with annealing of "
               "grain-boundary defects. Grain growth follows"),
            _eq(r"D^n - D_0^n = k_0\, t\, \exp\!\left(-\frac{Q}{RT}"
                r"\right),", "eq:growth"),
            _p("and with ", _m("n = 2"), " we obtain ",
               _m(r"Q \approx 48\ \text{kJ mol}^{-1}"), "."),

            _sec("Conclusion"),
            _p("Line-profile analysis of sol–gel ZnO shows crystallite "
               "growth from 18 to 48 nm and strain relief between 400 "
               "and 800 °C. Values from Scherrer and W–H converge once "
               "strain becomes negligible."),
            _bib(
                ("klug1974", "H. P. Klug and L. E. Alexander, "
                             "\\emph{X-Ray Diffraction Procedures}, 2nd ed. "
                             "(Wiley, 1974)."),
            ),
        ],
    )


# ------------------------------------------------------------------ DFT

def dft_study() -> Document:
    """Computational chemistry / DFT paper with convergence tables."""
    return Document(
        meta=_paper_meta("DFT study of CO on Pt(111)", "F. Kohn"),
        children=[
            Title(children=[Text(text=
                "A density-functional study of CO adsorption on Pt(111): "
                "site preference, dispersion and the “CO/Pt puzzle”")]),
            Author(children=[Text(text="F. Kohn, G. Sham")]),
            Abstract(children=[Text(text=
                "We revisit the long-standing discrepancy between DFT "
                "and experiment for CO on Pt(111), where generalised-"
                "gradient functionals wrongly favour the fcc hollow over "
                "the observed atop site. Using plane-wave calculations "
                "with PBE, RPBE, BEEF-vdW and the hybrid HSE06 we show "
                "that the site ordering is controlled by the position "
                "of the CO 2π* level, and that HSE06 restores the "
                "experimental preference by 0.09 eV.")]),
            Keywords(children=[Text(text=
                "DFT · adsorption · Pt(111) · CO · hybrid functionals")]),

            _sec("Introduction"),
            _p("Kohn–Sham density-functional theory ",
               Citation(keys=["kohn1965"]),
               " is the workhorse of surface chemistry, yet the simple "
               "case of CO on Pt(111) remains a known failure ",
               Citation(keys=["feibelman2001"]), "."),

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
            _p("so that negative values denote exothermic binding."),
            _items(
                "Code: plane-wave PAW, cutoff 450 eV",
                "Slab: 4-layer p(2×2) Pt(111), bottom two layers fixed, "
                "15 Å vacuum, dipole correction",
                "k-points: 8×8×1 Monkhorst–Pack, Methfessel–Paxton "
                "smearing 0.1 eV",
                "Forces converged to 0.02 eV/Å",
            ),
            _sec("Convergence", 2),
            Table(rows=[
                ["Cutoff (eV)", "k-mesh", "E(ads), atop (eV)", "Δ (meV)"],
                ["350", "6×6×1",  "−1.612", "31"],
                ["400", "6×6×1",  "−1.628", "15"],
                ["450", "8×8×1",  "−1.641", "2"],
                ["500", "10×10×1", "−1.643", "—"],
            ], caption="Convergence of the atop adsorption energy (PBE).",
               label="tab:conv", alignment="llrr", style="booktabs"),

            _sec("Results"),
            Table(rows=[
                ["Functional", "atop", "bridge", "hcp", "fcc",
                 "E(fcc) − E(atop)"],
                ["PBE",      "−1.64", "−1.72", "−1.78", "−1.80", "−0.16"],
                ["RPBE",     "−1.29", "−1.31", "−1.35", "−1.36", "−0.07"],
                ["BEEF-vdW", "−1.43", "−1.44", "−1.46", "−1.47", "−0.04"],
                ["HSE06",    "−1.52", "−1.47", "−1.44", "−1.43", "+0.09"],
                ["Expt.",    "−1.4 to −1.5", "", "", "", "atop"],
            ], caption="Adsorption energies (eV) at 0.25 ML.",
               label="tab:eads", alignment="lrrrrr", style="booktabs"),
            _p("Within the Blyholder picture the bond is described by "
               "5σ donation and 2π* back-donation. A Newns–Anderson "
               "estimate of the chemisorption energy is"),
            _eq(r"\Delta E_{d} \approx -2(1-f)\frac{V^2}"
                r"{|\varepsilon_{2\pi^*}-\varepsilon_d|} - "
                r"2(f)\frac{V'^2}{|\varepsilon_d - \varepsilon_{5\sigma}|}"
                r" + \alpha V^2,", "eq:newns"),
            _p("where ", _m(r"\varepsilon_d"), " is the d-band centre. "
               "GGAs place 2π* too low, over-stabilising multi-fold sites "
               "where back-donation is stronger."),
            _sec("Vibrational analysis", 2),
            _p("The C–O stretch frequency from the harmonic approximation "
               "is ", _m(r"\tilde\nu = \frac{1}{2\pi c}\sqrt{k/\mu}"),
               ". HSE06 gives 2081 cm⁻¹ for atop CO, compared with the "
               "IRAS value of 2090 cm⁻¹."),

            _sec("Conclusions"),
            _p("The CO/Pt puzzle is a self-interaction artefact: "
               "hybrid functionals correct the 2π* position and "
               "restore the atop preference."),
            _bib(
                ("kohn1965", "W. Kohn and L. J. Sham, \\emph{Phys. Rev.} "
                             "\\textbf{140}, A1133 (1965)."),
                ("feibelman2001", "P. J. Feibelman \\emph{et al.}, "
                                  "\\emph{J. Phys. Chem. B} \\textbf{105}, "
                                  "4018 (2001)."),
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
                "H. Medic, I. Statistician, J. Nurse — "
                "on behalf of the MOVE-T2D investigators")]),
            Abstract(children=[Text(text=
                "Background: Structured exercise improves glycaemic "
                "control, but effect sizes in routine care are uncertain. "
                "Methods: 240 adults with T2D (HbA1c 7.0–10.0 %) were "
                "randomised 1:1 to supervised exercise or usual care. "
                "The primary outcome was change in HbA1c at 12 weeks. "
                "Results: HbA1c fell by 0.62 % with exercise versus "
                "0.11 % with usual care (difference −0.51 %; 95 % CI "
                "−0.70 to −0.32; p < 0.001). Conclusions: Supervised "
                "exercise produces a clinically meaningful reduction in "
                "HbA1c. Trial registration: ISRCTN00000000.")]),
            Keywords(children=[Text(text=
                "type 2 diabetes · exercise · RCT · HbA1c")]),

            _sec("Introduction"),
            _p("Type 2 diabetes affects over 500 million adults "
               "worldwide ", Citation(keys=["idf2021"]),
               ". Guidelines recommend 150 minutes of moderate activity "
               "per week, but adherence outside trials is poor."),

            _sec("Methods"),
            _sec("Design and participants", 2),
            _p("Parallel-group, assessor-blinded RCT at four centres, "
               "reported according to CONSORT 2010 ",
               Citation(keys=["consort2010"]), "."),
            _items(
                "Inclusion: age 40–75 y, T2D ≥ 1 y, HbA1c 7.0–10.0 %, "
                "stable medication for 3 months",
                "Exclusion: insulin therapy, unstable angina, "
                "eGFR < 30 mL/min/1.73 m²",
            ),
            _sec("Sample size", 2),
            _p("To detect a difference ", _m(r"\Delta = 0.4\,\%"),
               " with SD ", _m(r"\sigma = 0.9\,\%"),
               ", two-sided ", _m(r"\alpha = 0.05"), " and power 90 %:"),
            _eq(r"n = \frac{2\,(z_{1-\alpha/2}+z_{1-\beta})^2\,\sigma^2}"
                r"{\Delta^2} = \frac{2(1.96+1.28)^2(0.9)^2}{0.4^2} "
                r"\approx 107", "eq:n"),
            _p("per arm; 120 per arm allows for 10 % attrition."),
            _sec("Statistical analysis", 2),
            _p("The primary analysis used ANCOVA on the intention-to-"
               "treat population, adjusting for baseline and centre:"),
            _eq(r"Y_{i,12} = \beta_0 + \beta_1\,\text{Tx}_i + "
                r"\beta_2\,Y_{i,0} + \sum_c \gamma_c\,\text{Centre}_{ic}"
                r" + \epsilon_i.", "eq:ancova"),
            _p("Missing data were handled by multiple imputation "
               "(", _m("m = 50"), ") under missing-at-random."),

            _sec("Results"),
            Table(rows=[
                ["Characteristic", "Exercise (n = 120)",
                 "Usual care (n = 120)"],
                ["Age, y, mean (SD)", "58.4 (8.1)", "59.1 (7.9)"],
                ["Female, n (%)", "53 (44)", "49 (41)"],
                ["BMI, kg/m², mean (SD)", "31.2 (4.6)", "30.8 (4.9)"],
                ["Diabetes duration, y", "7.2 (4.8)", "6.9 (5.1)"],
                ["HbA1c, %, mean (SD)", "8.12 (0.81)", "8.09 (0.78)"],
                ["Metformin, n (%)", "104 (87)", "107 (89)"],
            ], caption="Baseline characteristics.", label="tab:base",
               alignment="lcc", style="booktabs"),
            Table(rows=[
                ["Outcome", "Exercise", "Usual care",
                 "Adj. difference (95 % CI)", "p"],
                ["HbA1c (%)", "−0.62", "−0.11", "−0.51 (−0.70, −0.32)",
                 "< 0.001"],
                ["Fasting glucose (mmol/L)", "−0.9", "−0.2",
                 "−0.7 (−1.1, −0.3)", "0.001"],
                ["Weight (kg)", "−2.1", "−0.4", "−1.7 (−2.6, −0.8)",
                 "< 0.001"],
                ["VO₂max (mL/kg/min)", "+3.4", "+0.3", "+3.1 (2.2, 4.0)",
                 "< 0.001"],
            ], caption="Primary and secondary outcomes at 12 weeks.",
               label="tab:out", alignment="lrrrr", style="booktabs"),
            _p("The number needed to treat for one participant to reach "
               "HbA1c < 7 % was ",
               _m(r"\text{NNT} = 1/\text{ARR} = 1/(0.31-0.12) \approx 5"),
               "."),

            _sec("Discussion"),
            _p("The observed effect exceeds the 0.3–0.4 % threshold "
               "usually considered clinically relevant. Limitations "
               "include the short follow-up and the impossibility of "
               "blinding participants."),
            _sec("Declarations", 2),
            _items(
                "Ethics: approved by the regional ethics committee "
                "(REC 00/XX/0000); all participants gave written consent.",
                "Data availability: de-identified data available on "
                "reasonable request.",
                "Competing interests: none declared.",
            ),
            _bib(
                ("idf2021", "International Diabetes Federation, "
                            "\\emph{IDF Diabetes Atlas}, 10th ed. (2021)."),
                ("consort2010", "K. F. Schulz, D. G. Altman, D. Moher, "
                                "\\emph{BMJ} \\textbf{340}, c332 (2010)."),
            ),
        ],
    )


# ------------------------------------------------------------ physics

def quantum_notes() -> Document:
    """Theoretical physics: perturbation theory worked through."""
    return Document(
        meta=_paper_meta("Perturbation theory", "K. Dirac"),
        children=[
            Title(children=[Text(text=
                "Time-independent perturbation theory and the "
                "anharmonic oscillator")]),
            Author(children=[Text(text="K. Dirac — Advanced Quantum "
                                       "Mechanics, Lecture 7")]),

            _sec("Setting up the problem"),
            _p("We seek eigenstates of ", _m(r"H = H_0 + \lambda V"),
               " where the spectrum of ", _m("H_0"), " is known, ",
               _m(r"H_0|n^{(0)}\rangle = E_n^{(0)}|n^{(0)}\rangle"),
               ", and ", _m(r"\lambda"), " is small. Expanding"),
            _eq(r"E_n = E_n^{(0)} + \lambda E_n^{(1)} + \lambda^2 "
                r"E_n^{(2)} + \cdots,\qquad |n\rangle = |n^{(0)}\rangle "
                r"+ \lambda|n^{(1)}\rangle + \cdots", "eq:expand"),
            _p("and collecting powers of ", _m(r"\lambda"), " gives"),
            _eq(r"E_n^{(1)} = \langle n^{(0)}|V|n^{(0)}\rangle,", "eq:e1"),
            _eq(r"E_n^{(2)} = \sum_{m\neq n}\frac{|\langle m^{(0)}|V|"
                r"n^{(0)}\rangle|^2}{E_n^{(0)}-E_m^{(0)}}.", "eq:e2"),
            _p("Note that ", CrossRef(label="eq:e2", kind="eqref"),
               " is always negative for the ground state: second-order "
               "corrections push the lowest level down."),

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
               ". For the ground state the second-order result is"),
            _eq(r"E_0 = \frac{\hbar\omega}{2} + \frac{3\lambda\hbar^2}"
                r"{4m^2\omega^2} - \frac{21\lambda^2\hbar^3}{8m^4"
                r"\omega^5} + \mathcal O(\lambda^3).", "eq:e0"),

            _sec("Degenerate case"),
            _p("If ", _m(r"E^{(0)}"), " is ", _m("g"),
               "-fold degenerate, diagonalise ", _m("V"),
               " within the degenerate subspace:"),
            _eq(r"\det\left[\langle n_i^{(0)}|V|n_j^{(0)}\rangle - "
                r"E^{(1)}\delta_{ij}\right] = 0.", "eq:secular"),
            _p("The linear Stark effect in hydrogen ",
               _m("n = 2"), " is the classic example: the field mixes ",
               _m("2s"), " and ", _m("2p_0"),
               ", splitting them by ", _m(r"\pm 3 e a_0 \mathcal E"), "."),

            _sec("Validity"),
            _p("The series is asymptotic, not convergent — Dyson's "
               "argument ", Citation(keys=["dyson1952"]),
               " shows that for ", _m(r"\lambda < 0"),
               " the potential is unbounded below, so ",
               _m(r"E(\lambda)"), " cannot be analytic at ",
               _m(r"\lambda = 0"), ". Optimal truncation is at the "
               "smallest term."),

            _sec("Problems"),
            _ord_items(
                "Compute the first-order shift for V = x³. Why does it "
                "vanish?",
                "Derive the second-order shift for V = x³ and compare "
                "with the exact result for V = κx.",
                "Apply degenerate perturbation theory to a 2D isotropic "
                "oscillator perturbed by λxy.",
            ),
            _bib(
                ("dyson1952", "F. J. Dyson, \\emph{Phys. Rev.} "
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
            Author(children=[Text(text="L. Volta, M. Faraday, N. Nernst")]),
            Abstract(children=[Text(text=
                "Ni-rich layered oxides offer high capacity but suffer "
                "from capacity fade above 4.3 V. We show that 1 mol % Al "
                "doping of NMC811 raises capacity retention after 300 "
                "cycles at 1C from 71 % to 89 %, and reduces the charge-"
                "transfer resistance growth by a factor of three. "
                "Galvanostatic intermittent titration shows that Li⁺ "
                "diffusion is unaffected by doping.")]),
            Keywords(children=[Text(text=
                "lithium-ion battery · NMC811 · doping · impedance · GITT")]),

            _sec("Introduction"),
            _p("The energy density of a cell scales with the product of "
               "specific capacity and average voltage,"),
            _eq(r"E = \int_0^{Q} V(q)\,dq \approx Q\,\bar V,", "eq:energy"),
            _p("which motivates Ni-rich cathodes ",
               Citation(keys=["manthiram2020"]), "."),

            _sec("Experimental"),
            _items(
                "Co-precipitation of Ni₀.₈Mn₀.₁Co₀.₁(OH)₂, Al(NO₃)₃ "
                "added to 1 mol %",
                "Lithiation with LiOH·H₂O (5 % excess), 750 °C, "
                "12 h, O₂ flow",
                "Electrodes: 90:5:5 active:C65:PVDF, 10 mg/cm²",
                "CR2032 half-cells vs Li, 1 M LiPF₆ in EC:EMC 3:7",
            ),

            _sec("Results and discussion"),
            _sec("Cycling", 2),
            Table(rows=[
                ["Sample", "Q₁ at 0.1C (mAh/g)", "ICE (%)",
                 "Q at 5C (mAh/g)", "Retention 300 cyc (%)"],
                ["NMC811", "214", "88.1", "142", "71.2"],
                ["Al-NMC811", "209", "89.4", "151", "89.0"],
            ], caption="Electrochemical performance, 2.8–4.4 V.",
               label="tab:cycle", alignment="lrrrr", style="booktabs"),
            _sec("Impedance", 2),
            _p("Nyquist spectra were fitted to a Randles circuit with "
               "Warburg element:"),
            _eq(r"Z(\omega) = R_s + \frac{R_{ct} + Z_W}{1 + j\omega "
                r"C_{dl}(R_{ct}+Z_W)},\qquad Z_W = \frac{\sigma_W}"
                r"{\sqrt\omega}(1-j).", "eq:randles"),
            _p("After 300 cycles ", _m("R_{ct}"),
               " grew from 18 to 142 Ω for undoped and from 16 to "
               "54 Ω for doped material."),
            _sec("Diffusion", 2),
            _p("From GITT, the chemical diffusion coefficient is ",
               Citation(keys=["weppner1977"])),
            _eq(r"\tilde D = \frac{4}{\pi\tau}\left(\frac{m_B V_M}"
                r"{M_B S}\right)^2\left(\frac{\Delta E_s}"
                r"{\Delta E_\tau}\right)^2,", "eq:gitt"),
            _p("yielding ", _m(r"\tilde D \sim 10^{-10}"),
               " cm²/s for both materials at 50 % state of charge."),
            _sec("Thermodynamics", 2),
            _p("The open-circuit voltage relates to the Gibbs energy "
               "via ", _m(r"\Delta G = -nFE"),
               ", and its temperature coefficient gives the entropic "
               "heat:"),
            _eq(r"\Delta S = nF\left(\frac{\partial E}{\partial T}"
                r"\right)_p.", "eq:entropy"),

            _sec("Conclusions"),
            _p("Al doping suppresses the H2→H3 phase transition and "
               "surface reconstruction, giving 89 % retention at 4.4 V "
               "without compromising rate capability."),
            _bib(
                ("manthiram2020", "A. Manthiram, \\emph{Nat. Commun.} "
                                  "\\textbf{11}, 1550 (2020)."),
                ("weppner1977", "W. Weppner and R. A. Huggins, "
                                "\\emph{J. Electrochem. Soc.} "
                                "\\textbf{124}, 1569 (1977)."),
            ),
        ],
    )


# ----------------------------------------------------------- ecology / stats

def ecology_field_study() -> Document:
    """Ecology field study with mixed models and diversity indices."""
    return Document(
        meta=_paper_meta("Pollinator diversity", "O. Darwin"),
        children=[
            Title(children=[Text(text=
                "Wildflower margins increase pollinator diversity on "
                "arable farms: a three-year paired-field study")]),
            Author(children=[Text(text="O. Darwin, P. Wallace")]),
            Abstract(children=[Text(text=
                "We surveyed pollinators on 24 paired fields (sown "
                "wildflower margin vs conventional grass margin) over "
                "three summers. Margins increased Shannon diversity by "
                "0.41 (95 % CI 0.28–0.54) and bumblebee abundance by "
                "a factor of 2.3. Effects strengthened with margin age.")]),
            Keywords(children=[Text(text=
                "pollinators · agri-environment · biodiversity · GLMM")]),

            _sec("Introduction"),
            _p("Insect pollinators have declined across Europe ",
               Citation(keys=["potts2010"]),
               ". Agri-environment schemes fund flower-rich margins, "
               "but evidence for their effect on diversity is mixed."),

            _sec("Methods"),
            _sec("Survey design", 2),
            _p("Each farm contributed one treatment and one control "
               "field ≥ 500 m apart. Pollinators were recorded along "
               "fixed 100 m transects (6 visits per year, 10:00–16:00, "
               "> 15 °C, wind < Beaufort 4)."),
            _sec("Diversity indices", 2),
            _p("With ", _m("p_i"), " the proportion of individuals in "
               "species ", _m("i"), " of ", _m("S"), " species:"),
            _eq(r"H' = -\sum_{i=1}^{S} p_i \ln p_i,\qquad "
                r"D = 1 - \sum_{i=1}^{S} p_i^2,\qquad "
                r"J' = \frac{H'}{\ln S}.", "eq:div"),
            _sec("Statistical model", 2),
            _p("Abundance counts were modelled with a negative-binomial "
               "GLMM with farm as random intercept:"),
            _eq(r"\log \mu_{ijt} = \beta_0 + \beta_1\,\text{Margin}_{ij}"
                r" + \beta_2\,\text{Year}_t + \beta_3\,(\text{Margin}"
                r"\times\text{Year})_{ijt} + u_i,\quad u_i\sim\mathcal N"
                r"(0,\sigma_u^2).", "eq:glmm"),

            _sec("Results"),
            Table(rows=[
                ["Metric", "Control", "Margin", "Ratio / diff.", "p"],
                ["Total abundance", "31.2", "68.9", "×2.21", "< 0.001"],
                ["Bumblebees", "8.4", "19.3", "×2.30", "< 0.001"],
                ["Hoverflies", "12.1", "22.7", "×1.88", "< 0.001"],
                ["Species richness", "9.8", "15.4", "+5.6", "< 0.001"],
                ["Shannon H'", "1.72", "2.13", "+0.41", "< 0.001"],
                ["Pielou J'", "0.75", "0.78", "+0.03", "0.21"],
            ], caption="Mean per transect walk, pooled over years.",
               label="tab:eco", alignment="lrrrr", style="booktabs"),
            _p("The Margin × Year interaction was positive (",
               _m(r"\beta_3 = 0.18 \pm 0.05"), ", ", _m("p = 0.002"),
               "), indicating accumulating benefit as sown species "
               "established."),

            _sec("Discussion"),
            _p("Evenness was unchanged, so the diversity gain comes "
               "from additional species rather than redistribution. "
               "Landscape context was not controlled", Footnote(children=[
                   Text(text="Semi-natural habitat within 1 km ranged "
                             "from 3 % to 21 %.")]),
               ", which may explain between-farm variance "
               "(", _m(r"\hat\sigma_u = 0.34"), ")."),
            _bib(
                ("potts2010", "S. G. Potts \\emph{et al.}, \\emph{Trends "
                              "Ecol. Evol.} \\textbf{25}, 345 (2010)."),
            ),
        ],
    )


# --------------------------------------------------------- grant proposal

def grant_proposal() -> Document:
    """Research grant proposal with work packages, Gantt and budget."""
    return Document(
        meta=_paper_meta("Grant proposal", "Q. Principal"),
        children=[
            Title(children=[Text(text=
                "SOLAR-CAT: Defect-engineered photocatalysts for "
                "solar hydrogen — Research Grant Proposal")]),
            Author(children=[Text(text=
                "Principal Investigator: Q. Principal · "
                "Co-Investigators: R. Coinvest, S. Partner")]),

            _sec("Summary"),
            _p("Green hydrogen from direct solar water splitting could "
               "decarbonise heavy industry, but photocatalysts remain "
               "limited to < 1 % solar-to-hydrogen (STH) efficiency. "
               "SOLAR-CAT will combine in-situ spectroscopy, machine-"
               "learned defect models and high-throughput synthesis to "
               "reach 3 % STH in a 1 m² panel within 36 months."),

            _sec("Objectives"),
            _ord_items(
                "O1 — Map the link between oxygen-vacancy density and "
                "carrier lifetime in doped SrTiO₃.",
                "O2 — Train a surrogate model predicting STH from "
                "synthesis parameters (target MAE < 0.2 %).",
                "O3 — Demonstrate a 1 m² panel with ≥ 3 % STH over "
                "1000 h outdoor operation.",
            ),

            _sec("State of the art and ambition"),
            _p("The efficiency is the product of absorption, "
               "separation and surface-reaction yields:"),
            _eq(r"\eta_{\text{STH}} = \frac{r_{\text{H}_2}\times"
                r"\Delta G^\circ}{P_{\text{sun}}\times A} = "
                r"\eta_{\text{abs}}\,\eta_{\text{sep}}\,\eta_{\text{cat}},",
                "eq:sth"),
            _p("with ", _m(r"\Delta G^\circ = 237\ \text{kJ mol}^{-1}"),
               ". Al-doped SrTiO₃ reaches near-unity quantum efficiency "
               "in the UV ", Citation(keys=["takata2020"]),
               "; SOLAR-CAT extends this to visible light."),

            _sec("Work plan"),
            Table(rows=[
                ["WP", "Title", "Lead", "Months", "Person-months"],
                ["WP1", "Synthesis & doping", "Principal", "1–24", "30"],
                ["WP2", "In-situ spectroscopy", "Coinvest", "4–30", "24"],
                ["WP3", "Machine-learning models", "Partner", "6–33", "18"],
                ["WP4", "Panel demonstrator", "Principal", "18–36", "20"],
                ["WP5", "Management & dissemination", "Principal",
                 "1–36", "6"],
            ], caption="Work packages.", label="tab:wp",
               alignment="lllcr", style="booktabs"),
            Table(rows=[
                ["WP", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8",
                 "Q9", "Q10", "Q11", "Q12"],
                ["WP1", "■", "■", "■", "■", "■", "■", "■", "■",
                 "", "", "", ""],
                ["WP2", "", "■", "■", "■", "■", "■", "■", "■", "■",
                 "■", "", ""],
                ["WP3", "", "", "■", "■", "■", "■", "■", "■", "■",
                 "■", "■", ""],
                ["WP4", "", "", "", "", "", "■", "■", "■", "■", "■",
                 "■", "■"],
                ["WP5", "■", "■", "■", "■", "■", "■", "■", "■", "■",
                 "■", "■", "■"],
            ], caption="Gantt chart (quarters).", label="tab:gantt",
               alignment="lcccccccccccc"),

            _sec("Milestones and deliverables"),
            Table(rows=[
                ["#", "Milestone", "Month", "Verification"],
                ["M1", "Library of 200 doped compositions", "12",
                 "Database released"],
                ["M2", "Surrogate model MAE < 0.2 %", "24",
                 "Blind test set"],
                ["M3", "1 m² panel ≥ 3 % STH", "33",
                 "Independent certification"],
            ], caption="Milestones.", label="tab:ms", alignment="llcl",
               style="booktabs"),

            _sec("Risk management"),
            Table(rows=[
                ["Risk", "Likelihood", "Impact", "Mitigation"],
                ["Visible absorption insufficient", "Medium", "High",
                 "Fallback: tandem with BiVO₄"],
                ["Model under-performs", "Medium", "Medium",
                 "Active learning; more DFT data"],
                ["Panel degradation", "Low", "High",
                 "Encapsulation study in WP4"],
            ], caption="Risk register.", label="tab:risk",
               alignment="lccl", style="booktabs"),

            _sec("Budget"),
            Table(rows=[
                ["Category", "Year 1 (£k)", "Year 2 (£k)", "Year 3 (£k)",
                 "Total (£k)"],
                ["Staff", "210", "215", "220", "645"],
                ["Equipment", "180", "20", "10", "210"],
                ["Consumables", "35", "40", "30", "105"],
                ["Travel & dissemination", "8", "10", "14", "32"],
                ["Indirect (80 % FEC)", "—", "—", "—", "594"],
                ["Total", "", "", "", "1586"],
            ], caption="Budget summary.", label="tab:budget",
               alignment="lrrrr", style="booktabs"),

            _sec("Impact and pathways"),
            _items(
                "Academic: open data (FAIR) and open-source models",
                "Industrial: partnership with a panel manufacturer for "
                "scale-up",
                "Societal: public engagement via a solar-fuels exhibit",
                "Training: 2 PDRAs and 3 PhD students",
            ),
            _bib(
                ("takata2020", "T. Takata \\emph{et al.}, \\emph{Nature} "
                               "\\textbf{581}, 411 (2020)."),
            ),
        ],
    )


# ------------------------------------------------------- reviewer response

def response_to_reviewers() -> Document:
    """Point-by-point rebuttal letter for a manuscript revision."""
    return Document(
        meta=_paper_meta("Response to reviewers", "A. Surface"),
        children=[
            Title(children=[Text(text="Response to Reviewers")]),
            Author(children=[Text(text=
                "Manuscript APSUSC-D-26-01234 — “Oxygen vacancies and "
                "Ti³⁺ states in reduced anatase TiO₂ thin films”")]),
            _p("Dear Editor,"),
            _p("We thank you and the reviewers for the careful reading "
               "of our manuscript. We have addressed every comment "
               "below. Reviewer comments are in ", ("bold", ["bold"]),
               ", our responses in plain text, and changes to the "
               "manuscript are ", ("highlighted in italics", ["italic"]),
               ". Page and line numbers refer to the revised version."),

            _sec("Reviewer 1"),
            _p(("Comment 1.1 — The Ti³⁺ component could be an artefact "
                "of differential charging. Please justify.", ["bold"])),
            _p("We agree this must be excluded. We repeated the "
               "measurements with the flood gun at three emission "
               "currents; the Ti⁴⁺–Ti³⁺ separation varied by < 0.03 eV "
               "(new Table S2). In addition, the Ti³⁺ fraction is "
               "reversible upon re-oxidation in 10⁻⁶ mbar O₂, which "
               "charging artefacts would not be."),
            _p(("Added (p. 6, l. 142): “The chemical shift was invariant "
                "to neutraliser settings within 0.03 eV (Table S2).”",
                ["italic"])),
            _p(("Comment 1.2 — Why is the Lorentzian fraction fixed "
                "at 0.3?", ["bold"])),
            _p("Leaving ", _m(r"\eta"), " free led to strong "
               "correlation with the FWHM (", _m(r"|\rho| = 0.94"),
               "). We now report a sensitivity analysis over ",
               _m(r"\eta \in [0.2, 0.4]"),
               "; the Ti³⁺ fraction changes by at most 0.6 %."),

            _sec("Reviewer 2"),
            _p(("Comment 2.1 — The activation energy seems low. Compare "
                "with the literature.", ["bold"])),
            _p("We have added a comparison with three previous "
               "studies (new Table 3) and discussed the role of the "
               "UHV chemical potential of oxygen, ",
               _m(r"\Delta\mu_O(T,p)"), ", which lowers the effective "
               "formation energy."),
            _p(("Comment 2.2 — Minor: typo in Eq. (3).", ["bold"])),
            _p("Corrected, thank you."),

            _sec("Summary of changes"),
            Table(rows=[
                ["Section", "Change", "Prompted by"],
                ["Methods", "Charging control experiments", "R1.1"],
                ["Methods", "Sensitivity analysis on η", "R1.2"],
                ["Discussion", "Literature comparison, Table 3", "R2.1"],
                ["Eq. (3)", "Typo corrected", "R2.2"],
                ["SI", "New Tables S2–S3", "R1.1, R1.2"],
            ], caption="", alignment="lll", style="booktabs"),
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
        meta=_paper_meta("Standard operating procedure", "Lab manager"),
        children=[
            Title(children=[Text(text=
                "SOP-CHEM-014: Preparation of Piranha solution and "
                "cleaning of silicon substrates")]),
            Author(children=[Text(text=
                "Version 3.1 · Approved by: T. Safety · Review due: "
                "September 2027")]),

            _sec("Purpose and scope"),
            _p("This SOP describes the preparation and use of Piranha "
               "solution (3:1 H₂SO₄ : H₂O₂) to remove organic residues "
               "from Si wafers. It applies to all users of fume hood "
               "FH-3 in the Materials Chemistry laboratory."),

            _sec("Hazards"),
            Table(rows=[
                ["Hazard", "Severity", "Likelihood", "Risk", "Control"],
                ["Violent exotherm / explosion with organics", "5", "2",
                 "10", "Never mix with solvents; small volumes"],
                ["Severe chemical burns", "4", "2", "8",
                 "Face shield, acid apron, neoprene gloves"],
                ["Pressure build-up in closed vessel", "5", "1", "5",
                 "Never cap; label and leave to cool open"],
                ["Spill", "3", "2", "6", "Spill kit at FH-3; bund tray"],
            ], caption="Risk assessment (risk = severity × likelihood, "
                       "1–25).", label="tab:risk",
               alignment="lcccl", style="booktabs"),

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
                "acid. The mixture will reach ~120 °C.",
                "Immerse wafers with PTFE tweezers for 15 min.",
                "Rinse in three successive DI-water baths, then "
                "blow dry with N₂.",
                "Allow the solution to cool completely (≥ 2 h) in the "
                "open beaker before disposal.",
            ),
            _p("The heat released on mixing can be estimated from the "
               "enthalpy of dilution; for 30 mL of acid the temperature "
               "rise is roughly"),
            _eq(r"\Delta T \approx \frac{n\,|\Delta H_{\text{dil}}|}"
                r"{m\,c_p} \approx \frac{0.54 \times 45\,000}{56 \times "
                r"2.0} \approx 2\times 10^2\ \text{K (upper bound)},",
                "eq:heat"),
            _p("which is why peroxide must be added slowly."),

            _sec("Waste disposal"),
            _p("Cooled Piranha is collected in the labelled vented "
               "container “Piranha waste — do not cap tightly”. Never "
               "pour into the general acid-waste drum."),

            _sec("Emergency procedures"),
            _items(
                "Skin contact: drench in safety shower ≥ 15 min, remove "
                "contaminated clothing, call first aider.",
                "Eye contact: eyewash ≥ 15 min, seek medical attention.",
                "Spill > 50 mL: evacuate, call emergency number 2222.",
            ),

            _sec("Record of training"),
            Table(rows=[
                ["Name", "Trained by", "Date", "Signature"],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ], caption="", alignment="llll"),
        ],
    )


def _tables_escaped(factory):
    """Table cells are emitted verbatim, so %, & and # written as prose
    would break the tabular; escape them once here rather than in every
    cell literal."""
    def build() -> Document:
        doc = factory()
        for block in doc.children:
            if isinstance(block, Table):
                block.rows = [[re.sub(r"(?<!\\)([%&#])", r"\\\1", c)
                               for c in row] for row in block.rows]
        return doc
    build.__name__ = factory.__name__
    build.__doc__ = factory.__doc__
    return build


SCIENCE_EXAMPLES: list[tuple[str, callable]] = [
    ("&XPS surface-science paper",          _tables_escaped(xps_surface_study)),
    ("X&RD / nanomaterials paper",          _tables_escaped(xrd_nanoparticles)),
    ("&DFT computational study",            _tables_escaped(dft_study)),
    ("&Battery / electrochemistry paper",   _tables_escaped(battery_paper)),
    ("&Clinical trial (CONSORT)",           _tables_escaped(clinical_trial)),
    ("&Ecology field study",                _tables_escaped(ecology_field_study)),
    ("&Quantum mechanics lecture",          _tables_escaped(quantum_notes)),
    ("&Grant proposal (work packages)",     _tables_escaped(grant_proposal)),
    ("Res&ponse to reviewers",              _tables_escaped(response_to_reviewers)),
    ("Lab &SOP / risk assessment",          _tables_escaped(lab_sop)),
]
