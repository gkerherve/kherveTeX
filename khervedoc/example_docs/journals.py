"""Publisher templates: Elsevier, IEEE, APS RevTeX and ACS, ready for a submission."""
from __future__ import annotations

from ..example_helpers import _items, _meta, _ord_items, _p  # noqa: F401
from ..model import (
    Abstract, Affiliation, Author, Correspondence, Citation, CrossRef, DEFAULT_PACKAGES, Document,
    Footnote, InlineRaw, Keywords, List as ListNode, ListItem, MathBlock, MathInline, RawLatex, Section,
    Table, Text, Title,
)


def _sec(text: str, level: int = 1, numbered: bool = True) -> Section:
    return Section(level=level, children=[Text(text=text)], numbered=numbered)


def _m(latex: str) -> MathInline:
    return MathInline(latex=latex)


def _bib(*entries: tuple[str, str]) -> RawLatex:
    body = "\n".join(f"\\bibitem{{{k}}} {t}" for k, t in entries)
    return RawLatex(text="\\begin{thebibliography}{99}\n" + body
                         + "\n\\end{thebibliography}")


def _no_amsmath() -> list[str]:
    return [p for p in DEFAULT_PACKAGES if p != "amsmath"]


# --------------------------------------------------------- Elsevier journal

def elsevier_preprint() -> Document:
    """Elsevier preprint (elsarticle, single column, double-spaced, line
    numbers) with highlights, graphical abstract and the declarations
    Elsevier journals ask for."""
    front = (
        "\\author[agri]{Priya Raman\\corref{cor1}}\n"
        "\\ead{priya.raman@example.edu}\n"
        "\\author[agri,tech]{Tomas Lindqvist}\n"
        "\\author[tech]{Amara Okafor}\n"
        "\\cortext[cor1]{Corresponding author.}\n"
        "\\address[agri]{Department of Biosystems Engineering, "
        "Northern Lakes University, Aldermere, Country}\n"
        "\\address[tech]{Institute for Sensor Technology, "
        "Aldermere Polytechnic, Aldermere, Country}\n\n"
        "\\begin{highlights}\n"
        "\\item A 3 USD capacitive probe is calibrated in three soil textures.\n"
        "\\item One quadratic model fits all textures with RMSE of 0.019 "
        "m$^3$\\,m$^{-3}$.\n"
        "\\item Texture-specific models reduce the error by up to 37\\%.\n"
        "\\item Temperature drift is below 0.004 m$^3$\\,m$^{-3}$ over 15 K.\n"
        "\\end{highlights}\n\n"
        "\\begin{graphicalabstract}\n"
        "\\fbox{\\parbox[c][3.2cm][c]{0.92\\textwidth}{\\centering\n"
        "Graphical abstract placeholder: replace with a figure of at least "
        "531\\,$\\times$\\,1328 pixels (height\\,$\\times$\\,width), "
        "readable at 5\\,$\\times$\\,13 cm.}}\n"
        "\\end{graphicalabstract}"
    )
    return Document(
        meta=_meta(
            documentclass="elsarticle",
            class_options="preprint",
            body_font_family="libertine",
            body_font_pt=12,
            title="Calibration of a low-cost capacitive soil-moisture probe "
                  "across three soil textures",
            author="Priya Raman, Tomas Lindqvist, Amara Okafor",
            line_spacing=1.0,
            margin_bottom_cm=3.2,
            packages=DEFAULT_PACKAGES + ["hyperref", "lineno", "booktabs"],
            frontmatter_extras=front,
            preamble_extras=(
                "\\journal{Computers and Electronics in Agriculture}\n"
                ""
                "\\bibliographystyle{elsarticle-num}"),
        ),
        children=[
            Title(children=[Text(text=
                "Calibration of a low-cost capacitive soil-moisture probe "
                "across three soil textures")]),
            # The PDF takes the author block from the document settings
            # (frontmatter_extras); this line keeps the names visible here.
            Author(children=[Text(text=
                "Priya Raman, Tomas Lindqvist, Amara Okafor")]),
            Abstract(children=[Text(text=
                "Low-cost capacitive probes make dense soil-moisture "
                "networks affordable, but their output depends on soil "
                "texture and temperature. We calibrated 12 probes against "
                "oven-dry gravimetric measurements in a sand, a loam and a "
                "clay soil (144 samples in total). A quadratic relation "
                "between probe voltage and volumetric water content gave "
                "root-mean-square errors (RMSE) of 0.012, 0.015 and 0.021 "
                "m³ m⁻³ for the three soils, and 0.019 m³ m⁻³ for a single "
                "pooled model. Between 278 and 293 K the temperature drift "
                "stayed below 0.004 m³ m⁻³. Texture-specific calibration is "
                "therefore advisable when the error budget is below "
                "0.02 m³ m⁻³.")]),
            Keywords(children=[Text(text=
                "soil moisture · capacitive sensor · calibration · "
                "low-cost instrumentation · precision agriculture")]),

            RawLatex(text="\\linenumbers"),
            _sec("Introduction"),
            _p(
                "Irrigation scheduling needs soil-moisture data at the scale "
                "of a field, which means tens or hundreds of probes rather "
                "than one. Commercial time-domain reflectometry probes cost "
                "several hundred dollars each, while capacitive probes built "
                "around a 555 timer cost about 3 USD; their price has "
                "opened the door to dense networks ",
                Citation(keys=["Nakamura2021", "Berg2019"], style="cite"),
                ". The cost is paid in accuracy: the factory calibration "
                "is a straight line between air and water, and the probes "
                "respond to soil bulk density, salinity and temperature as "
                "well as to water ",
                Citation(keys=["Berg2019"], style="cite"), ".",
            ),
            _p(
                "This paper answers a practical question: how much is "
                "gained by calibrating for each soil texture, compared with "
                "a single calibration for all soils? We describe the "
                "calibration procedure (Section ",
                CrossRef(label="sec:methods", kind="ref"),
                "), report the errors for three contrasting soils "
                "(Section ", CrossRef(label="sec:results", kind="ref"),
                ") and discuss the temperature effect and the limits of the "
                "approach (Section ",
                CrossRef(label="sec:discussion", kind="ref"), ").",
            ),

            Section(level=1, label="sec:methods",
                    children=[Text(text="Materials and methods")]),
            _sec("Probe and soils", level=2),
            _p(
                "Twelve identical probes were read with a 12-bit analogue-"
                "to-digital converter at 3.3 V. Three soils were sampled "
                "from the top 20 cm of experimental plots: a sand (92% "
                "sand), a loam (41% sand, 38% silt) and a clay (58% clay). "
                "Each soil was air-dried, sieved to 2 mm and packed to a "
                "bulk density of 1.35 g cm⁻³ in 1 L cylinders.",
            ),
            _sec("Calibration procedure", level=2),
            _p(
                "Each cylinder was wetted to eight water contents between "
                "air-dry and saturation and equilibrated for 24 h. The "
                "probe voltage ", _m("V"), " was recorded for 5 min, after "
                "which a 20 mL core was weighed wet and oven-dried at "
                "105 °C to obtain the volumetric water content ",
                _m(r"\theta"), ". We fitted the quadratic model",
            ),
            MathBlock(
                latex=r"\theta = a_0 + a_1 V + a_2 V^{2}",
                numbered=True, label="eq:calib"),
            _p(
                "by least squares, either separately for each soil or for "
                "all 144 samples together. Goodness of fit is reported as "
                "the coefficient of determination ", _m("R^2"),
                " and the RMSE of ",
                CrossRef(label="eq:rmse", kind="eqref"), ":",
            ),
            MathBlock(
                latex=(r"\mathrm{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n}"
                       r"\left(\theta_i^{\mathrm{model}} - "
                       r"\theta_i^{\mathrm{ref}}\right)^{2}}"),
                numbered=True, label="eq:rmse"),
            _p(
                "Temperature drift was measured by cycling the loam "
                "cylinders between 278 and 293 K in a climate chamber at "
                "constant water content.",
            ),

            Section(level=1, label="sec:results",
                    children=[Text(text="Results")]),
            _p(
                "Table ", CrossRef(label="tab:fit", kind="ref"),
                " lists the fit quality. All soils are described well by "
                "Eq. (", CrossRef(label="eq:calib", kind="ref"),
                "): ", _m("R^2"), " exceeds 0.95 everywhere and the bias "
                "is within ±0.003 m³ m⁻³. The error grows with clay "
                "content, from 0.012 m³ m⁻³ in the sand to 0.021 m³ m⁻³ "
                "in the clay. The pooled model has an RMSE of 0.019 "
                "m³ m⁻³.",
            ),
            Table(
                rows=[
                    ["Soil", "n", "R²", "RMSE (m³ m⁻³)", "Bias (m³ m⁻³)"],
                    ["Sand", "48", "0.981", "0.012", "0.001"],
                    ["Loam", "48", "0.972", "0.015", "−0.002"],
                    ["Clay", "48", "0.951", "0.021", "0.003"],
                    ["Pooled", "144", "0.962", "0.019", "0.000"],
                ],
                caption="Fit of Eq. (1) to the calibration data, per soil "
                        "and for all soils pooled.",
                label="tab:fit", alignment="lrrrr", header=True),
            _p(
                "Between 278 and 293 K the output of the loam cylinders "
                "drifted by less than 0.004 m³ m⁻³, smaller than the "
                "calibration error and therefore negligible for irrigation "
                "decisions.",
            ),

            Section(level=1, label="sec:discussion",
                    children=[Text(text="Discussion")]),
            _p(
                "A sand-specific model lowers the RMSE of the pooled "
                "model (0.019 m³ m⁻³) to 0.012 m³ m⁻³, a 37% reduction, "
                "whereas the clay-specific model (0.021 m³ m⁻³) is no "
                "better than the pooled one. This agrees with the "
                "explanation that the dielectric response of bound water "
                "in clay is the dominant error source ",
                Citation(keys=["Berg2019"], style="cite"),
                ". Salinity was not varied here and is the main "
                "limitation: in saline soils the probes read high",
                Footnote(children=[Text(text=
                    "Electrical conductivity above about 2 dS m⁻¹ was "
                    "not tested.")]),
                ".",
            ),

            _sec("Conclusions"),
            _p(
                "A 3 USD capacitive probe reaches an RMSE of 0.012 to "
                "0.021 m³ m⁻³ after a quadratic, soil-specific "
                "calibration. A pooled calibration is sufficient for "
                "coarse scheduling (0.019 m³ m⁻³), but texture-specific "
                "models should be used when the error budget is "
                "tighter. Future work will add salinity as a second "
                "predictor.",
            ),

            _sec("CRediT authorship contribution statement", numbered=False),
            _p(("Priya Raman:", ["bold"]),
               " Conceptualization, Methodology, Writing – original draft."),
            _p(("Tomas Lindqvist:", ["bold"]),
               " Investigation, Formal analysis."),
            _p(("Amara Okafor:", ["bold"]),
               " Resources, Writing – review & editing."),
            _sec("Declaration of competing interest", numbered=False),
            _p(
                "The authors declare that they have no known competing "
                "financial interests or personal relationships that could "
                "have appeared to influence the work reported in this paper.",
            ),
            _sec("Data availability", numbered=False),
            _p("Data will be made available on request."),
            _sec("Acknowledgements", numbered=False),
            _p(
                "This work was supported by the Example Research Council "
                "(grant ERC-0000). The authors thank the field staff of the "
                "Aldermere experimental farm.",
            ),

            _bib(
                ("Nakamura2021",
                 "K. Nakamura, L. Osei, Low-cost sensor networks for "
                 "irrigation management, J. Example Agric. Eng. 14 (2021) "
                 "101--112."),
                ("Berg2019",
                 "H. Berg, M. Duarte, Texture and salinity effects on "
                 "capacitive soil-moisture sensors, Example Soil Sci. 7 "
                 "(2019) 45--58."),
            ),
        ],
    )


def elsevier_twocol() -> Document:
    """Elsevier two-column final layout (5p), native author block with
    affiliation, e-mail and corresponding-author note."""
    return Document(
        meta=_meta(
            documentclass="elsarticle",
            class_options="final",
            body_font_family="libertine",
            title="Sound insulation of lightweight double-leaf partitions",
            author="Jonas Weber, Mei Lin",
            column_count=2,
            body_font_pt=10,
            line_spacing=1.0,
            packages=DEFAULT_PACKAGES + ["hyperref", "booktabs"],
            preamble_extras=(
                "\\journal{Applied Acoustics}\n"
                "\\bibliographystyle{elsarticle-num}"),
        ),
        children=[
            Title(children=[Text(text=
                "Sound insulation of lightweight double-leaf partitions")]),
            Author(children=[Text(text="Jonas Weber, Mei Lin")]),
            Affiliation(children=[Text(text=
                "Laboratory of Building Acoustics, Aldermere Polytechnic, "
                "Aldermere, Country")]),
            Correspondence(children=[Text(text=
                "Corresponding author. E-mail: j.weber@example.edu")]),
            Abstract(children=[Text(text=
                "Plasterboard partitions with a cavity are the standard "
                "lightweight wall. We measured the weighted sound "
                "reduction index Rw of three configurations in a "
                "laboratory test facility and compared the results with "
                "the mass law and with the mass–air–mass resonance "
                "frequency. Doubling the board mass raised Rw by 5 dB, "
                "while a 100 mm cavity with mineral wool added a further "
                "9 dB, reaching 45 dB. The resonance frequency of 85 Hz "
                "predicted from the cavity depth lies below the "
                "building-acoustics range, so the wall performs close to "
                "the double-leaf ideal.")]),
            Keywords(children=[Text(text=
                "sound insulation · double-leaf wall · mass law · "
                "plasterboard")]),

            _sec("Introduction"),
            _p(
                "Lightweight partitions cover most interior walls in "
                "modern buildings. Their sound insulation is governed by "
                "the mass of the leaves, by the cavity between them and "
                "by the studs that couple them ",
                Citation(keys=["Aalto2018", "Vogel2020"], style="cite"),
                ". We give a short measurement study of three partitions "
                "and check how closely simple prediction formulas "
                "describe them.",
            ),

            _sec("Theory"),
            _p(
                "For a single leaf of surface mass ", _m("m"),
                " (kg m⁻²) the random-incidence mass law gives the "
                "transmission loss at frequency ", _m("f"), " (Hz):",
            ),
            MathBlock(
                latex=r"R = 20 \log_{10}(f\,m) - 47\ \mathrm{dB}",
                numbered=True, label="eq:masslaw"),
            _p(
                "Two leaves of masses ", _m("m_1"), " and ", _m("m_2"),
                " separated by a cavity of depth ", _m("d"),
                " resonate on the air spring at",
            ),
            MathBlock(
                latex=(r"f_0 = \frac{1}{2\pi}\sqrt{\frac{\rho_0 c_0^{2}}{d}"
                       r"\left(\frac{1}{m_1}+\frac{1}{m_2}\right)}"),
                numbered=True, label="eq:f0"),
            _p(
                "with air density ", _m(r"\rho_0 = 1.2\ \mathrm{kg\,m^{-3}}"),
                " and speed of sound ", _m(r"c_0 = 343\ \mathrm{m\,s^{-1}}"),
                ". Below ", _m("f_0"), " the two leaves move together; "
                "above it the insulation rises by 12 dB per octave until "
                "the cavity modes set in.",
            ),

            _sec("Measurements"),
            _p(
                "Panels of 4.2 m² were mounted in the opening between two "
                "reverberation rooms and measured in one-third-octave "
                "bands from 100 Hz to 3.15 kHz. ",
                "Table ", CrossRef(label="tab:walls", kind="ref"),
                " lists the three configurations. Wall A is a single "
                "12.5 mm board; wall B doubles it; wall C has two "
                "12.5 mm boards on each side of a 100 mm cavity.",
            ),
            Table(
                rows=[
                    ["Wall", "Mass (kg/m²)", "Cavity", "Rw (dB)"],
                    ["A", "10", "none", "31"],
                    ["B", "20", "none", "36"],
                    ["C", "40", "100 mm wool", "45"],
                ],
                caption="Surface mass and measured weighted sound "
                        "reduction index of the three walls.",
                label="tab:walls", alignment="lrlr", header=True),

            _sec("Discussion"),
            _p(
                "Doubling the mass from A to B raises Rw by 5 dB, below "
                "the 6 dB per doubling of Eq. (",
                CrossRef(label="eq:masslaw", kind="ref"),
                ") because coincidence reduces the benefit at high "
                "frequency. For wall C, ", _m("m_1 = m_2 = 20"),
                " kg m⁻² and ", _m("d = 0.1"), " m give ",
                _m(r"f_0 \approx 85"), " Hz via Eq. (",
                CrossRef(label="eq:f0", kind="ref"),
                "), well under the lowest band, so the cavity improves "
                "the whole measured range.",
            ),

            _sec("Conclusions"),
            _p(
                "A 100 mm mineral-wool cavity adds 9 dB to a double-board "
                "partition, which is more than doubling its mass again "
                "would give. The mass law and the resonance formula are "
                "adequate for first design estimates.",
            ),

            _sec("Acknowledgements", numbered=False),
            _p("This study was funded by the Example Building Research "
               "Fund."),

            _bib(
                ("Aalto2018",
                 "S. Aalto, R. Kim, Airborne sound insulation of "
                 "lightweight walls, Example Acoust. Lett. 3 (2018) "
                 "12--24."),
                ("Vogel2020",
                 "T. Vogel, Stud coupling in double-leaf partitions, "
                 "Example Build. Phys. 9 (2020) 201--215."),
            ),
        ],
    )


# --------------------------------------------------------- IEEE

def ieee_conference() -> Document:
    """IEEE conference paper (IEEEtran) with author blocks, index terms,
    numbered equations, a table and the IEEE reference list."""
    authors = (
        "\\IEEEauthorblockN{Sofia Marin}\n"
        "\\IEEEauthorblockA{\\textit{Dept. of Electrical Engineering}\\\\\n"
        "\\textit{Aldermere Polytechnic}\\\\\n"
        "Aldermere, Country\\\\\n"
        "sofia.marin@example.edu}\n"
        "\\and\n"
        "\\IEEEauthorblockN{Kwame Boateng}\n"
        "\\IEEEauthorblockA{\\textit{Wireless Systems Group}\\\\\n"
        "\\textit{Example Networks Lab}\\\\\n"
        "Riverton, Country\\\\\n"
        "k.boateng@example.org}")
    return Document(
        meta=_meta(
            documentclass="IEEEtran",
            class_options="conference",
            body_font_family="times",
            title="Energy-Aware Duty-Cycle Scheduling for Class A LoRaWAN "
                  "Sensor Nodes",
            author="",
            column_count=2,
            body_font_pt=10,
            line_spacing=1.0,
            packages=_no_amsmath() + ["cite", "url", "booktabs"],
            preamble_extras=(
                "\\usepackage[cmex10]{amsmath}\n"
                "\\usepackage{amssymb}\n"
                "\\interdisplaylinepenalty=2500\n"
                "\\newenvironment{keyword}{\\begin{IEEEkeywords}"
                "\\def\\sep{\\unskip, }}{\\end{IEEEkeywords}}"),
        ),
        children=[
            RawLatex(text="\\author{" + authors + "}"),
            Title(children=[Text(text=
                "Energy-Aware Duty-Cycle Scheduling for Class A LoRaWAN "
                "Sensor Nodes")]),
            Abstract(children=[Text(text=
                "Battery life limits long-range wireless sensor networks, "
                "and most of the energy of a LoRaWAN node goes into "
                "transmitting. We propose a scheduler that picks the "
                "spreading factor and the reporting interval of each node "
                "from its measured collision probability. In a simulation "
                "of 500 nodes around one gateway the scheduler raised the "
                "packet delivery ratio from 78.4% to 94.2% and cut the "
                "energy per uplink by 34%, which extends the expected "
                "battery life from 2.1 to 3.2 years.")]),
            Keywords(children=[Text(text=
                "LoRaWAN · duty cycle · energy efficiency · wireless "
                "sensor networks · scheduling")]),

            _sec("Introduction"),
            _p(
                "Low-power wide-area networks connect sensors that must "
                "run for years on a battery. In LoRaWAN, a Class A node "
                "sends an uplink whenever it has data and opens two short "
                "receive windows afterwards ",
                Citation(keys=["Adel2019"], style="cite"),
                ". Because nodes share the channel by pure ALOHA, "
                "collisions grow with the number of nodes, and every lost "
                "uplink wastes the energy spent on it.",
            ),
            _p(
                "The contributions of this paper are: (i) an energy and "
                "collision model for Class A nodes; (ii) a distributed "
                "scheduler that needs no extra downlink traffic; and "
                "(iii) a simulation study with 500 nodes."),

            _sec("Related Work"),
            _p(
                "The adaptive data rate (ADR) mechanism of LoRaWAN "
                "selects the spreading factor from the link margin ",
                Citation(keys=["Adel2019"], style="cite"),
                ". It ignores the load of the cell. Scheduling approaches "
                "that assign time slots need tight synchronisation ",
                Citation(keys=["Chen2020"], style="cite"),
                ", which Class A nodes do not have. Our scheduler keeps "
                "the ALOHA access and only tunes the offered load.",
            ),

            _sec("System Model"),
            _sec("Collision probability", level=2),
            _p(
                "With ", _m("N"), " nodes sending at rate ",
                _m(r"\lambda"), " with time on air ", _m("T"),
                ", the normalised offered load is ",
                _m(r"G = N\lambda T"),
                ", and the probability that an uplink survives is",
            ),
            MathBlock(
                latex=r"P_s = e^{-2G}",
                numbered=True, label="eq:aloha"),
            _sec("Energy per uplink", level=2),
            _p(
                "A node spends ", _m("P_{tx}T"),
                " on transmission, ", _m("E_{rx}"),
                " on the receive windows and sleeps for the rest of the "
                "period ", _m("T_c"), ":",
            ),
            MathBlock(
                latex=(r"E_u = P_{tx}\,T + E_{rx} + P_{sleep}\,"
                       r"(T_c - T)"),
                numbered=True, label="eq:energy"),
            _p(
                "The energy per delivered message is ",
                _m("E_u / P_s"),
                ", so lowering ", _m("G"), " by stretching ", _m("T_c"),
                " lowers both terms in Eq. (",
                CrossRef(label="eq:aloha", kind="ref"), ") and Eq. (",
                CrossRef(label="eq:energy", kind="ref"), ").",
            ),

            _sec("Proposed Scheduler"),
            _p(
                "Each node estimates the survival probability ",
                _m(r"\hat P_s"), " of its uplinks from the "
                "acknowledgements of the last 20 messages and adapts its "
                "period once per hour. The rule has three steps:",
            ),
            ListNode(ordered=True, items=[
                ListItem(children=[
                    Text(text="if the estimated survival probability is "
                               "below the target of 0.9, stretch the "
                               "period by a factor "),
                    _m(r"1+\beta(0.9-\hat P_s)"), Text(text=";")]),
                ListItem(children=[Text(text=
                    "if it is above 0.97, shorten the period by 10% down "
                    "to the nominal value;")]),
                ListItem(children=[Text(text=
                    "move to the next lower spreading factor whenever the "
                    "link margin exceeds 10 dB, because a shorter time on "
                    "air lowers G directly.")]),
            ]),
            _p(
                "In compact form the period update is",
            ),
            MathBlock(
                latex=(r"T_c \leftarrow \min\left\{T_{\max},\; "
                       r"T_c\left[1+\beta\,(0.9-\hat P_s)\right]"
                       r"\right\}"),
                numbered=True, label="eq:update"),
            _p(
                "with gain ", _m(r"\beta = 2"), " and ",
                _m(r"T_{\max} = 60"), " min. Eq. (",
                CrossRef(label="eq:update", kind="ref"),
                ") needs only local information, so no downlink capacity "
                "is consumed.",
            ),

            _sec("Evaluation"),
            _p(
                "We simulated 500 nodes in a 3 km radius around one "
                "gateway for 30 days, with a 24-byte payload and a "
                "10-minute nominal period. ",
                "Table ", CrossRef(label="tab:results", kind="ref"),
                " compares a fixed spreading factor (SF9), ADR and the "
                "proposed scheduler; the simulation parameters are in "
                "Table ", CrossRef(label="tab:params", kind="ref"), ".",
            ),
            Table(
                rows=[
                    ["Parameter", "Value"],
                    ["Nodes", "500"],
                    ["Cell radius", "3 km"],
                    ["Bandwidth", "125 kHz"],
                    ["Payload", "24 bytes"],
                    ["Nominal period", "10 min"],
                    ["Simulated time", "30 days"],
                ],
                caption="Simulation parameters.",
                label="tab:params", alignment="lr", header=True),
            Table(
                rows=[
                    ["Scheme", "PDR (\\%)", "Energy (mJ)", "Life (years)"],
                    ["Fixed SF9", "78.4", "148", "2.1"],
                    ["ADR", "86.9", "121", "2.6"],
                    ["Proposed", "94.2", "97", "3.2"],
                ],
                caption="Packet delivery ratio (PDR), mean energy per "
                        "uplink and estimated battery life.",
                label="tab:results", alignment="lrrr", header=True),
            _p(
                "The proposed scheme delivers 94.2% of the packets, "
                "15.8 points more than the fixed configuration, and uses "
                "34% less energy per uplink (97 mJ against 148 mJ).",
            ),

            _sec("Conclusion"),
            _p(
                "Tuning the offered load per node from local collision "
                "estimates improves both reliability and battery life of "
                "Class A LoRaWAN networks without extra signalling. "
                "Future work will validate the scheduler on a field "
                "testbed.",
            ),

            _sec("Acknowledgment", numbered=False),
            _p("This work was supported by the Example Research Council "
               "under grant ERC-0000."),

            _bib(
                ("Adel2019",
                 "A. Adel and B. Quinn, \"A survey of LoRaWAN medium "
                 "access,\" \\textit{Example IoT Commun. Mag.}, vol. 5, "
                 "no. 2, pp. 40--48, 2019."),
                ("Chen2020",
                 "L. Chen, M. Ortiz, and P. Singh, \"Slotted scheduling "
                 "for low-power networks,\" in \\textit{Proc. Example "
                 "Conf. Sensor Netw.}, 2020, pp. 112--119."),
            ),
        ],
    )


# ------------------------------------------------ APS / Physical Review

def revtex_article() -> Document:
    """APS Physical Review article (revtex4-2) with several authors,
    affiliations and e-mail, an appendix and acknowledgments."""
    authors = (
        "\\author{Lena Hartmann}\n"
        "\\email{lena.hartmann@example.edu}\n"
        "\\affiliation{Department of Physics, Northern Lakes University, "
        "Aldermere, Country}\n"
        "\\author{Priya Venkat}\n"
        "\\affiliation{Department of Physics, Northern Lakes University, "
        "Aldermere, Country}\n"
        "\\author{Tomas Reyes}\n"
        "\\affiliation{Quantum Optics Group, Institute for Applied "
        "Photonics, Aldermere, Country}\n")
    return Document(
        meta=_meta(
            documentclass="revtex4-2",
            class_options="aps,pra,reprint,floatfix,nofootinbib",
            body_font_family="libertine",
            title="Rabi oscillations of a driven two-level system with "
                  "detuned probe",
            author="",
            body_font_pt=10,
            line_spacing=1.0,
            column_count=2,
            packages=_no_amsmath() + ["amsmath", "hyperref", "booktabs"],
            preamble_extras=(
                "\\usepackage{libertine}\n"
                "% Class options: aps/aip, a journal (prl, pra, prb, ...) "
                "and preprint | twocolumn | reprint.\n"
                "\\newenvironment{keyword}{\\par\\small\\noindent"
                "\\textbf{Keywords:}\\ \\def\\sep{\\unskip; }}{\\par\\medskip}"),
        ),
        children=[
            RawLatex(text=authors.strip()),
            Title(children=[Text(text=
                "Rabi oscillations of a driven two-level system with "
                "detuned probe")]),
            Abstract(children=[Text(text=
                "We measure the population of a laser-driven two-level "
                "system as a function of pulse duration and detuning and "
                "compare it with the generalized Rabi formula. The Rabi "
                "frequency grows as the square root of the drive power, "
                "from 12.4 kHz at 0.5 mW to 99.3 kHz at 32 mW, and the "
                "measured π-pulse durations follow from the fit within "
                "1%. A decay constant of 180 μs limits the contrast of "
                "the oscillations.")]),
            Keywords(children=[Text(text=
                "Rabi oscillations; two-level system; coherent control; "
                "detuning")]),

            _sec("Introduction"),
            _p(
                "Coherent driving of a two-level system is the basic "
                "operation behind atomic clocks, quantum gates and "
                "magnetic resonance ",
                Citation(keys=["Rabi1937", "Allen1987"], style="cite"),
                ". The population of the excited state oscillates between "
                "zero and one at the Rabi frequency, and the oscillation "
                "is faster but shallower when the drive is detuned. We "
                "test this quantitatively for a single-photon transition "
                "driven by a 532 nm laser.",
            ),

            _sec("Theory"),
            _p(
                "A two-level system with transition frequency ",
                _m(r"\omega_0"), " driven at ", _m(r"\omega"),
                " with Rabi frequency ", _m(r"\Omega"),
                " and detuning ", _m(r"\Delta = \omega - \omega_0"),
                " has the excited-state population",
            ),
            MathBlock(
                latex=(r"P_e(t) = \frac{\Omega^{2}}{\Omega_R^{2}}\,"
                       r"\sin^{2}\!\left(\frac{\Omega_R t}{2}\right),"
                       r"\qquad \Omega_R=\sqrt{\Omega^{2}+\Delta^{2}}"),
                numbered=True, label="eq:rabi"),
            _p(
                "At resonance the population reaches one after the "
                r"π-pulse duration ", _m(r"t_\pi = \pi/\Omega"),
                ". Since ", _m(r"\Omega"), " is proportional to the "
                "electric field, it scales with the square root of the "
                "power ", _m("P"), ":",
            ),
            MathBlock(
                latex=r"\Omega = \Omega_1 \sqrt{P / P_1}",
                numbered=True, label="eq:scaling"),
            _p("Finite coherence is included by damping the oscillation:"),
            MathBlock(
                latex=(r"P_e(t) \to \tfrac{1}{2}\left[1 - e^{-t/T_2}"
                       r"\cos(\Omega_R t)\right]"),
                numbered=True, label="eq:damped"),

            _sec("Experiment"),
            _p(
                "The drive pulse was gated by an acousto-optic modulator "
                "with a rise time below 100 ns. For each of four powers "
                "we scanned the pulse length from 0 to 120 μs and fitted ",
                "Eq. (", CrossRef(label="eq:damped", kind="ref"), ") to "
                "the data. Table ", CrossRef(label="tab:rabi", kind="ref"),
                " gives the fitted Rabi frequencies ",
                _m(r"\Omega/2\pi"), " and the resulting ",
                _m(r"\pi"), "-pulse times.",
            ),
            Table(
                rows=[
                    ["Power (mW)", "Ω/2π (kHz)", "tπ (μs)"],
                    ["0.5", "12.4 ± 0.2", "40.3 ± 0.7"],
                    ["2.0", "24.9 ± 0.3", "20.1 ± 0.2"],
                    ["8.0", "49.6 ± 0.5", "10.1 ± 0.1"],
                    ["32", "99.3 ± 0.9", "5.04 ± 0.05"],
                ],
                caption="Fitted Rabi frequency and π-pulse duration "
                        "versus drive power.",
                label="tab:rabi", alignment="lcc", header=True),

            _sec("Results and discussion"),
            _p(
                "Each factor of four in power doubles ", _m(r"\Omega"),
                ", as Eq. (", CrossRef(label="eq:scaling", kind="ref"),
                ") predicts: 12.4, 24.9, 49.6 and 99.3 kHz differ by "
                "factors of 2.01, 1.99 and 2.00. The dephasing time is ",
                _m("T_2 = 180"), " μs, so for the slowest drive (",
                _m(r"t_\pi = 40.3"), " μs) the contrast already falls "
                "by about 20%",
                Footnote(children=[
                    _m(r"e^{-t_\pi/T_2} \approx 0.80"),
                    Text(text=" for "), _m(r"t_\pi = 40.3"),
                    Text(text=" μs and "), _m("T_2 = 180"),
                    Text(text=" μs.")]),
                ".",
            ),

            _sec("Conclusion"),
            _p(
                "The generalized Rabi formula describes the measured "
                "populations over a factor of 64 in power. Faster driving "
                "is the simplest way to retain contrast when ",
                _m("T_2"), " is limited.",
            ),

            _sec("Acknowledgments", numbered=False),
            _p("We thank the Example Photonics Facility for laser time. "
               "This work was supported by the Example Science Fund "
               "(Grant No. ESF-0000)."),

            RawLatex(text="\\appendix"),
            _sec("Derivation of the generalized Rabi formula"),
            _p(
                "In the rotating-wave approximation the amplitudes ",
                _m("c_g"), " and ", _m("c_e"), " obey",
            ),
            MathBlock(
                latex=(r"i\,\dot c_e = \tfrac{\Omega}{2}\,c_g - "
                       r"\Delta\,c_e,\qquad "
                       r"i\,\dot c_g = \tfrac{\Omega}{2}\,c_e"),
                numbered=True, label="eq:amps"),
            _p(
                "With the initial condition ", _m("c_g(0)=1"),
                " the solution of Eq. (",
                CrossRef(label="eq:amps", kind="ref"),
                ") gives ", _m("|c_e|^2"), " equal to the right-hand side "
                "of Eq. (", CrossRef(label="eq:rabi", kind="ref"), ").",
            ),

            _bib(
                ("Rabi1937",
                 "A. Example, Space quantization in a gyrating magnetic "
                 "field, Example Phys. Rev. 51, 652 (1937)."),
                ("Allen1987",
                 "B. Sample and C. Demo, \\textit{Optical Resonance and "
                 "Two-Level Atoms} (Example Press, Riverton, 1987)."),
            ),
        ],
    )


# -------------------------------------------------------- ACS chemistry

def acs_article() -> Document:
    """ACS journal article (achemso) with TOC graphic note, scheme,
    experimental section and Supporting Information."""
    authors = (
        "\\author{Mira Okonkwo}\n"
        "\\email{mira.okonkwo@example.edu}\n"
        "\\affiliation[Aldermere]{Department of Chemistry, Aldermere "
        "University, Aldermere, Country}\n"
        "\\author{Daniel Fraser}\n"
        "\\affiliation[Aldermere]{Department of Chemistry, Aldermere "
        "University, Aldermere, Country}\n"
        "\\author{Yuki Tanaka}\n"
        "\\affiliation[Riverton]{Catalysis Research Institute, Riverton "
        "Institute of Technology, Riverton, Country}\n"
        "\\alsoaffiliation[Aldermere]{Department of Chemistry, Aldermere "
        "University, Aldermere, Country}")
    return Document(
        meta=_meta(
            documentclass="achemso",
            class_options="journal=jacsat,manuscript=article",
            body_font_family="libertine",
            title="Palladium nanoparticles on nitrogen-doped carbon for "
                  "Suzuki–Miyaura coupling in aqueous ethanol",
            author="",
            body_font_pt=12,
            line_spacing=1.0,
            packages=_no_amsmath() + ["amsmath", "chemformula", "booktabs"],
            preamble_extras=(
                "\\usepackage{libertine}\n"
                "\\newenvironment{keyword}{\\par\\noindent"
                "\\textbf{Keywords:}\\ \\def\\sep{\\unskip, }}"
                "{\\par\\medskip}\n" + authors + "\n"
                "% journal codes: jacsat (JACS), jpcafh (J. Phys. Chem. A), "
                "nalefd (Nano Lett.), ancham (Anal. Chem.), langd5 "
                "(Langmuir)"),
        ),
        children=[
            Title(children=[Text(text=
                "Palladium nanoparticles on nitrogen-doped carbon for "
                "Suzuki–Miyaura coupling in aqueous ethanol")]),
            RawLatex(text=(
                "\\begin{tocentry}\n"
                "\\centering Table-of-contents graphic placeholder: ACS "
                "asks for one image, 8.25\\,cm wide and at most "
                "4.75\\,cm high, plus an optional one-sentence "
                "caption.\\par\n"
                "\\end{tocentry}")),
            # The PDF takes authors, e-mail and affiliations from the
            # document settings (preamble); this line mirrors the names.
            Author(children=[Text(text=
                "Mira Okonkwo, Daniel Fraser, Yuki Tanaka")]),
            Abstract(children=[Text(text=
                "Palladium nanoparticles (3.1 ± 0.6 nm) supported on "
                "nitrogen-doped carbon catalyze the Suzuki–Miyaura "
                "coupling of aryl bromides with phenylboronic acid in "
                "aqueous ethanol at 60 °C. With 0.5 mol % Pd, yields of "
                "84–98% are reached within 1 h, corresponding to turnover "
                "frequencies of 168–196 h⁻¹. The catalyst is recovered "
                "by filtration and keeps 92% of its activity over five "
                "runs.")]),
            Keywords(children=[Text(text=
                "palladium nanoparticles · heterogeneous catalysis · "
                "cross-coupling · nitrogen-doped carbon")]),

            _sec("Introduction"),
            _p(
                "The palladium-catalyzed coupling of aryl halides with "
                "boronic acids is a workhorse of C–C bond formation ",
                Citation(keys=["Voss2017"], style="cite"),
                ". Homogeneous catalysts are active but hard to remove "
                "from the product, which matters for pharmaceutical "
                "intermediates. Supported nanoparticles are an "
                "alternative if they stay on the support and do not "
                "leach ",
                Citation(keys=["Ito2020", "Voss2017"], style="cite"),
                ". Nitrogen sites in doped carbon anchor Pd and keep "
                "the particles small.",
            ),

            _sec("Experimental Section"),
            _sec("General", level=2),
            _p(
                "Solvents and reagents were used as received. Particle "
                "sizes were measured on 300 particles from transmission "
                "electron microscopy images; the Pd content was "
                "determined by ICP-OES.",
            ),
            _sec("Catalytic procedure", level=2),
            _p(
                "A mixture of aryl bromide (1.0 mmol), phenylboronic "
                "acid (1.2 mmol), K₂CO₃ (2.0 mmol) and catalyst "
                "(0.5 mol % Pd) in 6 mL of ethanol/water (1:1) was "
                "stirred at 60 °C for 1 h (Scheme ",
                CrossRef(label="eq:scheme", kind="ref"), ").",
            ),
            MathBlock(
                latex=(r"\ch{ArBr + PhB(OH)2 ->[Pd/NC, K2CO3]"
                       r"[EtOH/H2O, 60 °C] Ar-Ph}"),
                numbered=True, label="eq:scheme"),
            _p(
                "The turnover frequency is calculated from the product "
                "amount ", _m(r"n_P"), ", the Pd amount ",
                _m(r"n_{Pd}"), " and the time ", _m("t"), ":",
            ),
            MathBlock(
                latex=r"\mathrm{TOF} = \frac{n_P}{n_{Pd}\,t}",
                numbered=True, label="eq:tof"),

            _sec("Results and Discussion"),
            _p(
                "Electron microscopy shows well-dispersed particles of "
                "3.1 ± 0.6 nm diameter. ",
                "Table ", CrossRef(label="tab:scope", kind="ref"),
                " lists the substrate scope. Because the yield after 1 h "
                "is given at a 0.5 mol % loading, the TOF of Eq. (",
                CrossRef(label="eq:tof", kind="ref"),
                ") is simply twice the yield in percent: electron-poor "
                "4-bromoacetophenone reacts fastest (196 h⁻¹) and "
                "sterically hindered 2-bromotoluene slowest (168 h⁻¹).",
            ),
            Table(
                rows=[
                    ["Aryl bromide", "Yield (\\%)", "TOF (h⁻¹)"],
                    ["4-Bromoanisole", "91", "182"],
                    ["Bromobenzene", "96", "192"],
                    ["4-Bromoacetophenone", "98", "196"],
                    ["2-Bromotoluene", "84", "168"],
                ],
                caption="Substrate scope under standard conditions "
                        "(0.5 mol \\% Pd, 60 °C, 1 h).",
                label="tab:scope", alignment="lrr", header=True),
            _p(
                "After five consecutive runs with bromobenzene the yield "
                "fell from 96% to 88%, i.e. the catalyst keeps 92% of "
                "its activity. The Pd content of the filtered solution "
                "was below the detection limit of the ICP-OES.",
            ),

            _sec("Conclusion"),
            _p(
                "Pd nanoparticles on nitrogen-doped carbon couple aryl "
                "bromides efficiently in green solvents and can be "
                "recycled. Studies on aryl chlorides are under way.",
            ),

            RawLatex(text=(
                "\\begin{acknowledgement}\n"
                "This work was supported by the Example Chemistry Fund "
                "(Grant No. ECF-0000). We thank the Aldermere Electron "
                "Microscopy Facility.\n"
                "\\end{acknowledgement}")),
            _sec("Supporting Information Available", numbered=False),
            _p(
                "Catalyst preparation, TEM images and size histogram, "
                "ICP-OES data, NMR spectra of the products (PDF). This "
                "material is available free of charge via the Internet "
                "at the journal website."),

            _bib(
                ("Voss2017",
                 "Voss, H.; Lindgren, E. Cross-coupling with supported "
                 "metals. \\textit{Example J. Catal.} \\textbf{2017}, "
                 "\\textit{12}, 301--315."),
                ("Ito2020",
                 "Ito, R.; Paul, S. Leaching from palladium on carbon. "
                 "\\textit{Example Chem. Rev.} \\textbf{2020}, "
                 "\\textit{3}, 88--97."),
            ),
        ],
    )
