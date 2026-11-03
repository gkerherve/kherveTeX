"""The examples and templates: what File > New from Template and the Examples
tab offer, and the empty page the app opens on.

Each factory returns a fully-formed Document, so an example always matches
the current model schema; the documents themselves live in
khervedoc.example_docs, one module per family. Every document type the app
offers has at least one example here, and each compiles cleanly
(tests/test_examples.py, packaging/smoke_test.py).
"""
from __future__ import annotations

from .example_docs.book_classes import (
    ams_book, koma_book, koma_report, memoir_book, tufte_book, tufte_handout,
)
from .example_docs.journal_classes import (
    acmart_paper, amsart_paper, apa_paper, koma_article, llncs_paper,
    mnras_paper, springer_nature_paper,
)
from .example_docs.journals import (
    acs_article, elsevier_preprint, elsevier_twocol, ieee_conference,
    revtex_article,
)
from .example_docs.letters import (
    cv, europass_cv, koma_letter, letter, meeting_minutes, memo, recipe,
)
from .example_docs.long_form import (
    a0_poster, beamer_slides, book_chapter, poster, standalone_figure, thesis,
    white_paper,
)
from .example_docs.planning import (
    calendar, daily_journal, grant_proposal, lab_sop, monthly_journal,
    response_to_reviewers, weekly_journal,
)
from .example_docs.science import (
    battery_paper, clinical_trial, dft_study, ecology_field_study,
    quantum_notes, xps_surface_study, xrd_nanoparticles,
)
from .example_docs.start import (
    article, blank, math_heavy, three_column_document, two_column_article,
    welcome,
)
from .example_docs.teaching import (
    exam_paper, homework, lab_report, lecture_notes, literature_review,
    research_proposal,
)
from .example_docs.thesis_classes import (
    disser_thesis, elegant_book, hep_thesis, mimosis_thesis, suftesi_thesis,
    toptesi_thesis,
)

GALLERY_CATEGORIES: tuple[str, ...] = (
    "Start", "Articles", "Journals", "Theses & books", "Teaching",
    "Science", "Letters & CV", "Slides & posters", "Planning")

# (category, label, factory, one line for the user), in gallery order.
GALLERY: list[tuple[str, str, callable, str]] = [
    ("Start", "Welcome tour", welcome,
     "A ten-minute guided tour of the editor: formatting, maths, tables, "
     "history, review, import and export."),
    ("Start", "Blank document", blank, "An empty page, as in Word."),

    ("Articles", "Single-column article", article,
     "A short experimental paper with abstract, equations, a table and "
     "citations."),
    ("Articles", "Two-column article", two_column_article,
     "The same paper in two columns at 10 pt."),
    ("Articles", "Three-column document", three_column_document,
     "The same paper in three columns."),
    ("Articles", "Maths-heavy document", math_heavy,
     "Quadratics: derivations, a theorem and proof, a table and worked "
     "examples."),
    ("Articles", "KOMA-Script article", koma_article,
     "A technical field report with KOMA's sans headings, lists, a table and "
     "an equation."),
    ("Articles", "White paper", white_paper,
     "Executive summary, problem, options with a cost model, plan and risks."),
    ("Articles", "Literature review", literature_review,
     "A thematic review with author-year citations, a summary table and a "
     "bibliography."),
    ("Articles", "Research proposal", research_proposal,
     "Summary, background, objectives, methods, timeline, risks and budget."),

    ("Journals", "Elsevier journal preprint", elsevier_preprint,
     "An elsarticle submission with highlights, graphical abstract, CRediT "
     "and data statements."),
    ("Journals", "Elsevier two-column", elsevier_twocol,
     "A two-column Elsevier paper with editable authors and affiliations."),
    ("Journals", "IEEE conference paper", ieee_conference,
     "IEEEtran with author blocks, index terms, equations and IEEE-style "
     "references."),
    ("Journals", "APS Physical Review (RevTeX)", revtex_article,
     "A RevTeX letter with affiliations, appendix and acknowledgments."),
    ("Journals", "ACS journal article", acs_article,
     "achemso with a TOC graphic, a reaction scheme and Supporting "
     "Information."),
    ("Journals", "Springer LNCS conference paper", llncs_paper,
     "An llncs paper with institutes, keywords, a theorem and references."),
    ("Journals", "Springer Nature journal article", springer_nature_paper,
     "An sn-jnl article with affiliations, keywords, equations and a table."),
    ("Journals", "ACM conference paper", acmart_paper,
     "An acmart short paper with CCS concepts, keywords and a results table."),
    ("Journals", "AMS mathematics paper", amsart_paper,
     "An amsart note with theorem, proof, corollary and MSC classes."),
    ("Journals", "MNRAS astronomy paper", mnras_paper,
     "A two-column MNRAS paper with a parameter table and author-year "
     "citations."),
    ("Journals", "APA 7 psychology paper", apa_paper,
     "An APA manuscript: title page, author note, abstract and APA tables."),

    ("Theses & books", "Thesis", thesis,
     "A report-class thesis: abstract, contents, six chapters, appendices."),
    ("Theses & books", "Book chapter", book_chapter,
     "A textbook chapter with definitions, a worked example and exercises."),
    ("Theses & books", "Book (memoir)", memoir_book,
     "Two chapters in memoir, with equations, tables and footnotes."),
    ("Theses & books", "Report (KOMA-Script)", koma_report,
     "An annual report in scrreprt: summary, chapters, an equation and a "
     "table."),
    ("Theses & books", "Book (KOMA-Script)", koma_book,
     "A teaching book in scrbook with equations and tables."),
    ("Theses & books", "Book (Tufte)", tufte_book,
     "A Tufte book with side notes and margin notes."),
    ("Theses & books", "Monograph (AMS book)", ams_book,
     "An amsbook chapter: definitions, propositions, theorems and proofs."),
    ("Theses & books", "Book (elegantbook)", elegant_book,
     "A short course with definition, theorem and proof boxes."),
    ("Theses & books", "Thesis (mimosis)", mimosis_thesis,
     "A physics thesis in mimosis: abstract, contents, three chapters."),
    ("Theses & books", "Thesis (hepthesis, particle physics)", hep_thesis,
     "A particle-physics thesis: a dijet resonance search."),
    ("Theses & books", "Thesis (suftesi, humanities)", suftesi_thesis,
     "A humanities thesis in the Italian typographic tradition."),
    ("Theses & books", "Thesis (toptesi, engineering)", toptesi_thesis,
     "An engineering thesis with model equations and results tables."),
    ("Theses & books", "Dissertation (disser)", disser_thesis,
     "A dissertation in the Russian disser class."),

    ("Teaching", "Lab report", lab_report,
     "An undergraduate lab report with data tables and uncertainties."),
    ("Teaching", "Exam (exam class)", exam_paper,
     "A timed test with points per question, parts, a points table and "
     "solutions that print with the answers option."),
    ("Teaching", "Homework / problem set", homework,
     "Problems with points, lemmas and worked solutions."),
    ("Teaching", "Lecture notes", lecture_notes,
     "Course notes with definitions, theorems, proofs and exercises."),
    ("Teaching", "Handout (Tufte)", tufte_handout,
     "A one-topic handout with margin notes and side notes."),
    ("Teaching", "Quantum mechanics lecture", quantum_notes,
     "Perturbation theory with an exact-versus-series table and problems."),

    ("Science", "XPS surface-science paper", xps_surface_study,
     "Ti 2p and O 1s fitting with a Shirley background and quantification."),
    ("Science", "XRD / nanomaterials paper", xrd_nanoparticles,
     "Bragg, Scherrer and Williamson-Hall analysis of ZnO grain growth."),
    ("Science", "DFT computational study", dft_study,
     "CO on Pt(111): convergence, functionals and vibrations."),
    ("Science", "Battery / electrochemistry paper", battery_paper,
     "A doped NMC811 cathode: cycling, impedance and GITT."),
    ("Science", "Clinical trial (CONSORT)", clinical_trial,
     "A randomised trial with sample size, CONSORT flow and outcomes."),
    ("Science", "Ecology field study", ecology_field_study,
     "A pollinator survey with diversity indices and a mixed model."),
    ("Science", "Grant proposal (work packages)", grant_proposal,
     "Objectives, work packages, Gantt chart, milestones, risks and budget."),
    ("Science", "Response to reviewers", response_to_reviewers,
     "A point-by-point rebuttal for a revised manuscript."),
    ("Science", "Lab SOP / risk assessment", lab_sop,
     "A standard operating procedure with risks, PPE and a training record."),

    ("Letters & CV", "Letter", letter,
     "A submission letter to an editor, in the letter class."),
    ("Letters & CV", "KOMA-Script letter", koma_letter,
     "A job-application cover letter in scrlttr2."),
    ("Letters & CV", "Academic CV", cv,
     "An academic CV in moderncv: education, posts, publications, skills."),
    ("Letters & CV", "Europass CV", europass_cv,
     "A Europass CV with the CEFR language grid."),
    ("Letters & CV", "Technical memo", memo,
     "An internal memo with a risk table."),
    ("Letters & CV", "How-to guide", recipe,
     "A step-by-step guide with commands, tips and a summary table."),

    ("Slides & posters", "Presentation (beamer)", beamer_slides,
     "A 16:9 ten-minute talk in eight slides."),
    ("Slides & posters", "Poster (tikzposter)", poster,
     "A portrait conference poster in titled blocks and two columns."),
    ("Slides & posters", "Poster (a0poster)", a0_poster,
     "A classic A0 poster."),
    ("Slides & posters", "Standalone figure (TikZ)", standalone_figure,
     "One self-contained TikZ figure on a page cropped to fit."),

    ("Planning", "Daily planner", daily_journal,
     "Today: priorities, an hourly schedule, follow-ups and a review."),
    ("Planning", "Weekly planner", weekly_journal,
     "This week: goals, day-by-day plan, habit tracker and review."),
    ("Planning", "Monthly planner", monthly_journal,
     "This month: goals, a week-by-week outline and key dates."),
    ("Planning", "Calendar", calendar,
     "A landscape wall calendar for this month."),
    ("Planning", "Meeting minutes", meeting_minutes,
     "Attendees, agenda, decisions and action items."),
]

# Every example as (label, factory), the welcome tour first: what the welcome
# page lists and what the compile checks and the offline bundle cover.
EXAMPLES: list[tuple[str, callable]] = [(label, f) for _c, label, f, _d
                                        in GALLERY]
JOURNAL_EXAMPLES: list[tuple[str, callable]] = [
    (label, f) for c, label, f, _d in GALLERY if c == "Journals"]
