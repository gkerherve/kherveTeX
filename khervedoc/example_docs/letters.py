"""Letters, CVs, memos, minutes and a how-to guide, each in its own class."""
from __future__ import annotations

from ..model import (
    Author, CrossRef, DEFAULT_PACKAGES, Document, Footnote, Link,
    List as ListNode, ListItem, MathBlock, MathInline, Paragraph, RawLatex,
    Section, Table, Text, Title,
)
from ..example_helpers import _items, _meta, _ord_items, _p


# ------------------------------------------------------------------ letter

def letter() -> Document:
    """A manuscript-submission letter in the classic LaTeX `letter` class."""
    return Document(
        meta=_meta(
            title="", author="",
            documentclass="letter", body_font_pt=11,
            margin_left_cm=3.0, margin_right_cm=3.0,
            margin_top_cm=2.0, margin_bottom_cm=2.0,
            preamble_extras=(
                "\\address{Dr Jane Author\\\\Department of Examples\\\\"
                "University of KherveTeX\\\\123 Example Road\\\\"
                "London EC1A 1AA\\\\jane.author@example.org}\n"
                "\\signature{Dr Jane Author\\\\\\textit{on behalf of all authors}}\n"
                "\\date{17 May 2026}\n"
            ),
        ),
        children=[
            RawLatex(text=(
                "\\begin{letter}{Prof.\\ Recipient Name\\\\Editor-in-Chief\\\\"
                "Journal of Worked Examples\\\\456 Editorial Avenue\\\\"
                "Cambridge CB2 1TN}\n"
                "\\opening{Dear Prof.\\ Recipient,}")),
            _p(("Submission of manuscript JWE-2026-0142 for consideration",
                ["bold"])),
            _p(
                "I am writing to submit our manuscript, entitled "
                "\u201cA worked example of the KherveTeX editor for "
                "scientific writing,\u201d for consideration as a research "
                "article in the Journal of Worked Examples. The work has "
                "not been published elsewhere and is not under "
                "consideration at any other journal.",
            ),
            _p("The manuscript presents KherveTeX, an editor that stores documents as a structured model and serialises them to LaTeX on demand. Our contributions are threefold:"),
            _ord_items(
                "a document model that round-trips to LaTeX, including "
                "environments and macros the editor does not itself "
                "understand;",
                "a user study (N\u00a0=\u00a037) in which participants drafted "
                "a short article faster than in a conventional LaTeX "
                "setup, with no measurable loss of formatting quality;",
                "an open-source release of the editor under the BSD-3 "
                "licence.",
            ),
            _p(
                "We suggest Prof.\u00a0X (University of Y), Dr\u00a0Z "
                "(Institute of W) and Dr\u00a0V (Laboratory of U) as "
                "reviewers; we have not collaborated with any of them in "
                "the past three years.",
            ),
            _p(
                "Thank you for considering our submission. I am happy to "
                "provide any further information you need and look forward "
                "to hearing from you.",
            ),
            RawLatex(text=(
                "\\closing{Yours sincerely,}\n"
                "\\encl{Manuscript (PDF), cover figure, author checklist}\n"
                "\\end{letter}")),
        ],
    )


def koma_letter() -> Document:
    """A formal job-application cover letter in the KOMA-Script scrlttr2
    class: sender block, address window, subject line, enclosures."""
    return Document(
        meta=_meta(
            title="", author="",
            documentclass="scrlttr2", body_font_pt=11,
            class_options="11pt,parskip=half,fromalign=right,"
                          "fromrule=afteraddress,subject=underlined",
            margin_left_cm=2.5, margin_right_cm=2.5,
            margin_top_cm=1.5, margin_bottom_cm=1.5,
            preamble_extras=(
                "\\setkomavar{fromname}{Maria Eriksen}\n"
                "\\setkomavar{fromaddress}{14 Harbour Lane\\\\"
                "Eastport EP3 4QR}\n"
                "\\setkomavar{fromemail}{maria.eriksen@example.org}\n"
                "\\setkomavar{fromphone}{+44 7700 900456}\n"
                "\\setkomavar{subject}{Application for the post of Senior "
                "Data Engineer (ref.\\ DE-2026-17)}\n"
                "\\setkomavar{date}{3 November 2026}\n"
                "\\setkomavar{signature}{Maria Eriksen}\n"
            ),
        ),
        children=[
            RawLatex(text=(
                "\\begin{letter}{Ms Anika Rao\\\\Head of Data Platform\\\\"
                "Northway Analytics Ltd\\\\8 Canal Street\\\\"
                "Midford MD1 5TT}\n"
                "\\opening{Dear Ms Rao,}")),
            _p(
                "I am applying for the position of Senior Data Engineer "
                "advertised on your careers page. For six years I have built "
                "data platforms for a logistics company, and the mix of "
                "batch and streaming work in your team is exactly the "
                "direction I want to take."),
            _p(
                "At Tidewater Freight I led the migration of 140 nightly "
                "batch jobs to an event-driven pipeline. Median end-to-end "
                "latency fell from 9\u00a0hours to under 4\u00a0minutes and "
                "the cloud bill by 22\u00a0%. Schema contracts between "
                "producers and consumers cut data-quality incidents from "
                "eleven per quarter to two."),
            _p(
                "I also bring well-tested Python and SQL pipelines and "
                "experience mentoring five junior engineers."),
            _p(
                "I would welcome the chance to discuss Northway\u2019s platform "
                "roadmap. I am free for interview at short notice and "
                "could start after a two-month notice period."),
            RawLatex(text=(
                "\\closing{Yours sincerely,}\n"
                "\\encl{Curriculum vitae, two references, degree "
                "certificate}\n"
                "\\cc{Recruitment office, Northway Analytics Ltd}\n"
                "\\end{letter}")),
        ],
    )


# ---------------------------------------------------------------------- CV

def cv() -> Document:
    """Academic CV in the moderncv class (classic style, blue)."""
    def entry(years, title, where, desc="", city="", grade=""):
        return (f"\\cventry{{{years}}}{{{title}}}{{{where}}}{{{city}}}"
                f"{{{grade}}}{{{desc}}}")

    return Document(
        meta=_meta(
            title="", author="Jane A. Researcher",
            documentclass="moderncv", class_options="11pt,a4paper,sans",
            margin_left_cm=2.0, margin_right_cm=2.0,
            margin_top_cm=2.0, margin_bottom_cm=2.0,
            preamble_extras=(
                "\\moderncvstyle{classic}\n\\moderncvcolor{blue}\n"
                "\\title{Postdoctoral researcher}\n"
                "\\address{Department of Physics, University of Somewhere}"
                "{Somewhere SW1 2AB}{United Kingdom}\n"
                "\\email{jane.researcher@example.org}\n"
                "\\homepage{www.example.org/jresearcher}\n"
                "\\extrainfo{ORCID 0000-0000-0000-0001}\n"
            ),
        ),
        children=[
            Author(children=[Text(text="Jane Researcher")]),
            Section(level=1, numbered=False,
                    children=[Text(text="Education")]),
            RawLatex(text="\n".join([
                entry("2019--2023", "PhD in Condensed Matter Physics",
                      "University of Somewhere",
                      "Thesis: \\emph{Topological phases in two-dimensional "
                      "electron gases under periodic driving}. Supervisor: "
                      "Prof.~M.~Topologist."),
                entry("2015--2019", "MSci Physics (First Class)",
                      "Example College London",
                      "Final-year project: \\emph{Raman spectroscopy of "
                      "graphene heterostructures}."),
            ])),
            Section(level=1, numbered=False,
                    children=[Text(text="Research experience")]),
            RawLatex(text="\n".join([
                entry("2023--present", "Postdoctoral Research Associate",
                      "University of Somewhere",
                      "\\begin{itemize}\\item Theory of Floquet topological "
                      "insulators under dissipation.\\item Co-supervision of "
                      "two PhD students.\\item Maintenance of the group "
                      "computing cluster (48 nodes, SLURM).\\end{itemize}"),
                entry("2019--2023", "Graduate Research Assistant",
                      "University of Somewhere",
                      "\\begin{itemize}\\item Analytic edge-state transport "
                      "in periodically driven honeycomb lattices.\\item "
                      "Tight-binding code in Julia, ten times faster than "
                      "the legacy Fortran code.\\item Five conference talks, "
                      "two of them invited.\\end{itemize}"),
            ])),
            Section(level=1, numbered=False,
                    children=[Text(text="Selected publications")]),
            RawLatex(text="\n".join([
                "\\cvitem{2024}{J.~A.~Researcher, M.~Topologist, "
                "``Floquet edge modes in dissipative honeycomb lattices,'' "
                "\\emph{Phys.\\ Rev.\\ Lett.} \\textbf{132}, 076401.}",
                "\\cvitem{2022}{J.~A.~Researcher, ``Topological invariants "
                "of periodically driven systems: a pedagogical review,'' "
                "\\emph{J.\\ Phys.\\ A} \\textbf{55}, 123001.}",
                "\\cvitem{2021}{J.~A.~Researcher, K.~Collaborator, ``Raman "
                "signatures of twist-angle disorder in moir\\'e "
                "superlattices,'' \\emph{Nano Lett.} \\textbf{21}, "
                "4532--4539.}",
            ])),
            Section(level=1, numbered=False,
                    children=[Text(text="Teaching")]),
            RawLatex(text="\n".join([
                "\\cvitem{2024}{Lecturer, summer school on topological "
                "matter, University of Elsewhere}",
                "\\cvitem{2021--22}{Tutorial leader, Mathematical Methods "
                "(second year)}",
                "\\cvitem{2020--23}{Demonstrator, Quantum Mechanics II "
                "(third year)}",
            ])),
            Section(level=1, numbered=False,
                    children=[Text(text="Skills")]),
            RawLatex(text="\n".join([
                "\\cvitem{Programming}{Python, Julia, Fortran, C, Bash}",
                "\\cvitem{Scientific}{NumPy, SciPy, QuTiP, Kwant, "
                "Matplotlib, \\LaTeX}",
                "\\cvitem{HPC}{SLURM, MPI, OpenMP, CUDA}",
                "\\cvitem{Languages}{English (native), French (fluent), "
                "German (intermediate)}",
            ])),
            Section(level=1, numbered=False,
                    children=[Text(text="Awards and service")]),
            RawLatex(text="\n".join([
                "\\cvitem{2024}{National Research Fellowship, "
                "2024--2027 (\\pounds350\\,k)}",
                "\\cvitem{2022}{Best Poster Prize, Condensed Matter "
                "Physics conference}",
                "\\cvitem{2019}{University President's PhD Scholarship}",
                "\\cvitem{Referee}{Phys.\\ Rev.\\ Lett., Phys.\\ Rev.\\ B, "
                "New J.\\ Phys.}",
                "\\cvitem{Outreach}{Annual public lecture on quantum "
                "materials, Science Festival 2023 and 2024}",
            ])),
        ],
    )


def europass_cv() -> Document:
    """A Europass-style CV (europasscv class): personal information,
    work experience, education, languages on the CEFR scale, digital skills."""
    sec = lambda t, body: RawLatex(text=f"\\ecvsection{{{t}}}\n{body}")
    return Document(
        meta=_meta(
            title="", author="", documentclass="europasscv",
            class_options="english",
            preamble_extras=(
                # The class draws small PNG/PDF icons that tectonic's bundle
                # does not ship; skip only those so the CV still compiles.
                "\\let\\ktig\\includegraphics\n"
                "\\renewcommand{\\includegraphics}[2][]"
                "{\\IfSubStringInString{icons/}{#2}{}{\\ktig[#1]{#2}}}\n"
                "\\ecvname{Maria Eriksen}\n"
                "\\ecvaddress{14 Harbour Lane, Eastport EP3 4QR, "
                "United Kingdom}\n"
                "\\ecvmobile{+44 7700 900456}\n"
                "\\ecvemail{maria.eriksen@example.org}\n"
                "\\ecvhomepage{www.example.org/meriksen}\n"
                "\\ecvnationality{Norwegian}\n"
                "\\ecvdateofbirth{12/03/1992}\n"
            ),
        ),
        children=[
            RawLatex(text="\\begin{europasscv}\n\\ecvpersonalinfo"),
            sec("Work experience",
                "\\ecvtitle{2021--present}{Senior Data Engineer\\newline"
                "\\normalsize\\textcolor{ecvtextcolor}{Tidewater Freight, "
                "Eastport (UK)}}\n"
                "\\ecvitem{}{\\begin{ecvitemize}\n"
                "\\item Led the migration of 140 nightly batch jobs to an "
                "event-driven pipeline (latency from 9 h to 4 min).\n"
                "\\item Introduced schema contracts; data-quality incidents "
                "fell from 11 to 2 per quarter.\n"
                "\\item Mentored five junior engineers.\n"
                "\\end{ecvitemize}}\n"
                "\\ecvtitle{2017--2021}{Data Engineer\\newline"
                "\\normalsize\\textcolor{ecvtextcolor}{Fjordline Systems, "
                "Bergen (Norway)}}\n"
                "\\ecvitem{}{\\begin{ecvitemize}\n"
                "\\item Built the reporting warehouse used by 60 analysts.\n"
                "\\item Automated regulatory reports, saving about 30 hours "
                "per month.\n"
                "\\end{ecvitemize}}"),
            sec("Education and training",
                "\\ecvtitle{2015--2017}{MSc Computer Science\\newline"
                "\\normalsize\\textcolor{ecvtextcolor}{University of Example, "
                "Bergen (Norway)}}\n"
                "\\ecvitem{}{Specialisation in distributed systems; thesis "
                "on consistency in streaming joins (grade A).}\n"
                "\\ecvtitle{2012--2015}{BSc Mathematics\\newline"
                "\\normalsize\\textcolor{ecvtextcolor}{University of Example, "
                "Bergen (Norway)}}"),
            sec("Personal skills",
                "\\ecvmothertongue{Norwegian}\n"
                "\\ecvlanguageheader\n"
                "\\ecvlanguage{English}{\\ecvCTwo}{\\ecvCTwo}{\\ecvCOne}"
                "{\\ecvCOne}{\\ecvCOne}\n"
                "\\ecvlanguage{German}{\\ecvBTwo}{\\ecvBOne}{\\ecvBOne}"
                "{\\ecvBOne}{\\ecvATwo}\n"
                "\\ecvlastlanguage{French}{\\ecvATwo}{\\ecvATwo}{\\ecvAOne}"
                "{\\ecvAOne}{\\ecvAOne}\n"
                "\\ecvitem{}{\\footnotesize Levels: A1/A2 basic user, B1/B2 "
                "independent user, C1/C2 proficient user (Common European "
                "Framework of Reference).}"),
            RawLatex(text=(
                "\\ecvblueitem{Digital skills}{Python, SQL, Apache Airflow, "
                "Kafka, dbt, Terraform, Git}\n"
                "\\ecvblueitem{Certifications}{Cloud Data Engineer "
                "(professional level), 2022}")),
            sec("Additional information",
                "\\ecvblueitem{Talks}{Event-driven data platforms in "
                "practice, Data Engineering Meetup, Bergen, 2023.}\n"
                "\\ecvblueitem{Volunteering}{Code club mentor: weekly "
                "coding sessions for teenagers, 2018--present.}\n"
                "\\end{europasscv}"),
        ],
    )


# -------------------------------------------------------------------- memo

def memo() -> Document:
    """Short technical memo in KOMA-Script's scrartcl."""
    return Document(
        meta=_meta(
            title="", author="",
            documentclass="scrartcl", body_font_pt=11,
            margin_left_cm=3.0, margin_right_cm=3.0,
            margin_top_cm=2.5, margin_bottom_cm=2.5,
        ),
        children=[
            Paragraph(children=[Text(text="TECHNICAL MEMO",
                                     marks=["bold"])], alignment="center"),
            Paragraph(children=[
                Text(text="To:\u00a0\u00a0", marks=["bold"]),
                Text(text="Engineering team")], alignment="left"),
            Paragraph(children=[
                Text(text="From:\u00a0\u00a0", marks=["bold"]),
                Text(text="J. Author, Systems lead")], alignment="left"),
            Paragraph(children=[
                Text(text="Date:\u00a0\u00a0", marks=["bold"]),
                Text(text="20 May 2026")], alignment="left"),
            Paragraph(children=[
                Text(text="Subject:\u00a0\u00a0", marks=["bold"]),
                Text(text="Migration from PostgreSQL 14 to 16")],
                alignment="left"),
            RawLatex(text="\\noindent\\rule{\\textwidth}{0.4pt}"),
            Section(level=1, numbered=False,
                    children=[Text(text="Summary")]),
            _p(
                "We propose migrating the production database from "
                "PostgreSQL 14 to PostgreSQL 16 during the maintenance "
                "window of 7\u20138 June 2026. The upgrade brings the "
                "logical-replication improvements that unblock the "
                "event-sourcing work planned for Q3 and removes our "
                "dependency on a version that is about to lose community "
                "support."),
            Section(level=1, numbered=False,
                    children=[Text(text="Background")]),
            _p(
                "PostgreSQL 14 reaches community end-of-life in November "
                "2026", Footnote(children=[Text(
                    text="Per the project's published versioning policy, "
                         "each major release is supported for five years.")]),
                ". Several extensions we depend on (pg_partman, pgvector) "
                "have already dropped CI testing against it, so staying "
                "put raises the risk of compatibility regressions with "
                "every extension update."),
            Section(level=1, numbered=False,
                    children=[Text(text="Proposal")]),
            _ord_items(
                "Upgrade the staging cluster with pg_upgrade this week.",
                "Run the full regression suite against staging for two "
                "weeks (24 May to 6 June).",
                "Cut over production during the 7 June window: promote a "
                "PG 16 replica fed by logical replication, with a write "
                "freeze of under five minutes.",
                "Keep the PG 14 primary, fenced read-only, for 48 hours as "
                "a rollback target.",
                "Decommission the old cluster once the on-call rotation "
                "signs off.",
            ),
            Section(level=1, numbered=False,
                    children=[Text(text="Risks")]),
            _p("The main risks and their mitigations are summarised in Table\u00a0",
               CrossRef(label="tab:risks"), "."),
            Table(
                rows=[
                    ["Risk", "Likelihood", "Mitigation"],
                    ["Extension incompatibility", "Low",
                     "Pre-tested in staging"],
                    ["Replication lag during cutover", "Medium",
                     "Schedule in the low-traffic window; abort if lag "
                     "exceeds 30 s"],
                    ["Rollback needed after 48 h", "Very low",
                     "WAL archiving to object storage"],
                ],
                caption="Risk assessment for the migration.",
                label="tab:risks",
                alignment="llp{6cm}",
                header=True,
            ),
            Section(level=1, numbered=False,
                    children=[Text(text="Decision requested")]),
            _p(
                "Please confirm by 28 May whether the 7 June window is "
                "acceptable, or suggest an alternative date. Without "
                "objections by then we will proceed as described above."),
        ],
    )


# ------------------------------------------------------------ meeting minutes

def meeting_minutes() -> Document:
    """Meeting minutes in KOMA-Script's scrartcl: attendees, agenda,
    decisions, action items."""
    return Document(
        meta=_meta(
            title="", author="",
            documentclass="scrartcl", body_font_pt=11,
            margin_left_cm=2.5, margin_right_cm=2.5,
            margin_top_cm=2.0, margin_bottom_cm=2.0,
            preamble_extras="\\date{}\n",
        ),
        children=[
            Title(children=[Text(text="Project Phoenix: Sprint review "
                                      "meeting")]),
            Author(children=[Text(
                text="20 May 2026, 14:00\u201315:00 (video call)")]),
            Section(level=1, children=[Text(text="Attendees")]),
            _p(("Present:", ["bold"]),
               " J. Manager (chair), A. Developer, B. Developer, "
               "C. Designer, D. QA Engineer, E. Product Owner (remote)."),
            _p(("Apologies:", ["bold"]), " F. DevOps (on leave)."),
            Section(level=1, children=[Text(text="Agenda")]),
            _ord_items(
                "Sprint 14 demo and retrospective",
                "Sprint 15 planning",
                "Infrastructure update",
                "Any other business"),
            Section(level=1, children=[Text(text="Sprint 14 demo")]),
            _p(
                "A. Developer demonstrated the new bulk-import endpoint. "
                "It processes CSV uploads asynchronously and returns a job "
                "ID for polling. E. Product Owner confirmed that the "
                "feature meets the acceptance criteria in ticket PX-312."),
            _p(
                "C. Designer walked through the updated settings page. Two "
                "minor spacing issues were logged as PX-345 and PX-346."),
            Section(level=1, children=[Text(text="Retrospective")]),
            _p(("What went well", ["bold"])),
            _items(
                "Pair programming on the import endpoint caught two edge "
                "cases before they reached QA.",
                "Daily stand-ups stayed under ten minutes all sprint.",
                "The new staging environment was stable throughout."),
            _p(("What could improve", ["bold"])),
            _items(
                "Flaky integration tests blocked the pipeline three times.",
                "A late requirement change on PX-330 caused scope creep."),
            Section(level=1, children=[Text(text="Sprint 15 planning")]),
            _p("The stories in Table\u00a0", CrossRef(label="tab:sprint15"),
               " were committed for Sprint 15: 19 story points against a "
               "forecast capacity of 21."),
            Table(
                rows=[
                    ["Ticket", "Title", "Owner", "Points"],
                    ["PX-350", "Role-based access control", "A. Dev", "8"],
                    ["PX-351", "Password reset flow", "B. Dev", "5"],
                    ["PX-345", "Settings page spacing fix", "C. Des", "2"],
                    ["PX-346", "Settings page icon alignment", "C. Des",
                     "1"],
                    ["PX-352", "Flaky test investigation", "D. QA", "3"],
                    ["", "Total", "", "19"],
                ],
                caption="Sprint 15 backlog.",
                label="tab:sprint15",
                alignment="lllr",
                header=True,
            ),
            Section(level=1, children=[Text(text="Infrastructure update")]),
            _p(
                "In F. DevOps' absence, J. Manager relayed the update: the "
                "Kubernetes cluster will be upgraded on 1 June. No "
                "application changes are expected, but every team should "
                "check its Helm charts against the API deprecations."),
            Section(level=1, children=[Text(text="Action items")]),
            Table(
                rows=[
                    ["No.", "Action", "Owner", "Due"],
                    ["1", "Investigate flaky tests", "D. QA", "23 May"],
                    ["2", "Review Helm charts for the cluster upgrade",
                     "F. DevOps", "28 May"],
                    ["3", "Send password-reset wireframes", "C. Des",
                     "22 May"],
                    ["4", "Schedule PX-330 scope review", "E. PO",
                     "21 May"],
                ],
                caption="Action items from this meeting.",
                label="tab:actions",
                alignment="rlll",
                header=True,
            ),
            Section(level=1, children=[Text(text="Next meeting")]),
            _p("Sprint 15 review: 3 June 2026, 14:00, same video link."),
        ],
    )


# ------------------------------------------------------------- how-to guide

def _verb(*lines: str) -> RawLatex:
    return RawLatex(text="\\begin{verbatim}\n" + "\n".join(lines)
                    + "\n\\end{verbatim}")


def recipe() -> Document:
    """Step-by-step how-to guide in scrartcl: prerequisites, numbered steps
    with commands and tips, a summary table."""
    return Document(
        meta=_meta(
            title="How-to guide", author="",
            documentclass="scrartcl", body_font_pt=11,
            margin_left_cm=2.5, margin_right_cm=2.5,
            preamble_extras="\\date{}\n",
        ),
        children=[
            Title(children=[Text(text="Setting up a reproducible Python "
                                      "project from scratch")]),
            Author(children=[Text(text="A practical step-by-step guide")]),
            Section(level=1, children=[Text(text="Prerequisites")]),
            _items(
                "Python 3.12 or newer, available on your PATH",
                "Git, with your name and e-mail configured "
                "(git config user.name, git config user.email)",
                "A terminal (bash, zsh or PowerShell)",
                "A text editor or IDE of your choice"),
            _p("The whole procedure takes about fifteen minutes and "
               "produces the layout shown below."),
            _verb("my-project/", "  .gitignore", "  pyproject.toml",
                  "  src/my_project/__init__.py", "  tests/test_smoke.py"),
            Section(level=1, children=[Text(text="Steps")]),

            Section(level=2, numbered=False,
                    children=[Text(text="1. Create the project directory")]),
            _p("Open a terminal and run:"),
            _verb("mkdir my-project && cd my-project", "git init",
                  "mkdir -p src/my_project tests",
                  "touch src/my_project/__init__.py"),
            _p(("Tip:", ["italic"]),
               " choose a short, lowercase, hyphen-separated name. Use an "
               "underscore instead of a hyphen for the importable package "
               "(my_project)."),

            Section(level=2, numbered=False,
                    children=[Text(text="2. Create a virtual environment")]),
            _verb("python -m venv .venv",
                  "source .venv/bin/activate    # Linux / macOS",
                  ".venv\\Scripts\\activate       # Windows"),
            _p(("Tip:", ["italic"]), " put ", ("/.venv/", ["code"]),
               " and ", ("__pycache__/", ["code"]), " in your ",
               (".gitignore", ["code"]),
               " so they are never committed."),

            Section(level=2, numbered=False,
                    children=[Text(text="3. Declare and pin dependencies")]),
            _p("Describe the project in ", ("pyproject.toml", ["code"]),
               ", then compile a lock file so everyone installs the same "
               "versions:"),
            _verb("[project]",
                  "name = \"my-project\"",
                  "version = \"0.1.0\"",
                  "requires-python = \">=3.12\"",
                  "dependencies = [\"numpy\"]"),
            _verb("pip install pip-tools",
                  "pip-compile -o requirements.lock pyproject.toml",
                  "pip install -r requirements.lock"),

            Section(level=2, numbered=False,
                    children=[Text(text="4. Add a test framework")]),
            _verb("pip install pytest",
                  "echo 'def test_smoke(): assert True' > tests/test_smoke.py",
                  "pytest -q"),
            _p("A passing run prints ", ("1 passed", ["code"]),
               ". From now on every change should keep it green."),

            Section(level=2, numbered=False,
                    children=[Text(text="5. Configure linting and "
                                        "formatting")]),
            _p("Ruff does both jobs in one tool:"),
            _verb("pip install ruff", "ruff check .", "ruff format ."),

            Section(level=2, numbered=False,
                    children=[Text(text="6. Make your first commit")]),
            _verb("git add pyproject.toml requirements.lock .gitignore",
                  "git add src/ tests/",
                  "git commit -m \"Initial project skeleton\""),

            Section(level=1, children=[Text(text="Summary")]),
            _p("Each step and the tool behind it is listed in Table\u00a0",
               CrossRef(label="tab:steps"), "."),
            Table(
                rows=[
                    ["Step", "Tool", "Purpose"],
                    ["1", "git init", "Version control"],
                    ["2", "python -m venv", "Isolation"],
                    ["3", "pip-tools", "Reproducible dependencies"],
                    ["4", "pytest", "Testing"],
                    ["5", "ruff", "Linting and formatting"],
                    ["6", "git commit", "Checkpoint"],
                ],
                caption="Quick reference for each step.",
                label="tab:steps",
                alignment="cll",
                header=True,
            ),
            Section(level=1, children=[Text(text="Next steps")]),
            _items(
                "Add a CI pipeline (GitHub Actions, GitLab CI) that runs "
                "pytest and ruff on every push.",
                "Set up pre-commit hooks to catch issues before CI does.",
                "Write a README.md with setup instructions for "
                "collaborators.",
                "Consider static type checking with mypy or pyright."),
        ],
    )
