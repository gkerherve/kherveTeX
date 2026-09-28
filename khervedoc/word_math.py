"""Turn an equation pasted from Word as plain Unicode text back into LaTeX.

Word's clipboard text flattens OMML: subscripts become ordinary letters
("Lₙ" arrives as "Ln"), brackets and operators arrive as Unicode glyphs
and the equation number trails after tabs. The conversion is a best
guess that the user then refines in the equation builder, so it favours
readable, compilable LaTeX over cleverness.
"""
from __future__ import annotations

import re

_SYMBOLS = {
    "−": "-", "–": "-", "×": r"\times ", "·": r"\cdot ", "⋅": r"\cdot ",
    "÷": r"\div ", "±": r"\pm ", "∓": r"\mp ", "≤": r"\le ", "≥": r"\ge ",
    "≠": r"\ne ", "≈": r"\approx ", "≡": r"\equiv ", "∝": r"\propto ",
    "∼": r"\sim ", "∞": r"\infty ", "∂": r"\partial ", "∇": r"\nabla ",
    "∑": r"\sum ", "∏": r"\prod ", "∫": r"\int ", "∮": r"\oint ",
    "√": r"\sqrt ", "→": r"\to ", "←": r"\leftarrow ", "⇒": r"\Rightarrow ",
    "⇔": r"\Leftrightarrow ", "↔": r"\leftrightarrow ", "∈": r"\in ",
    "∉": r"\notin ", "⊂": r"\subset ", "∪": r"\cup ", "∩": r"\cap ",
    "∀": r"\forall ", "∃": r"\exists ", "°": r"^\circ ", "′": "'",
    "⟨": r"\langle ", "⟩": r"\rangle ", "〈": r"\langle ", "〉": r"\rangle ",
    "‖": r"\| ", "…": r"\dots ", "⋯": r"\cdots ", "ℏ": r"\hbar ", "ħ": r"\hbar ",
    "Å": r"\text{Å}",
}
_GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "varepsilon",
    "ϵ": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta", "ϑ": "vartheta",
    "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu", "µ": "mu",
    "ν": "nu", "ξ": "xi", "π": "pi", "ρ": "rho", "σ": "sigma", "ς": "varsigma",
    "τ": "tau", "υ": "upsilon", "φ": "phi", "ϕ": "phi", "χ": "chi",
    "ψ": "psi", "ω": "omega", "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta",
    "Λ": "Lambda", "Ξ": "Xi", "Π": "Pi", "Σ": "Sigma", "Φ": "Phi",
    "Ψ": "Psi", "Ω": "Omega",
}
_SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ", "0123456789+-=()ni"))
_SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ", "0123456789+-=()aeoxhklmnpst"))
# Letter runs that are words, not a symbol with a flattened subscript.
_FUNCTIONS = {"sin", "cos", "tan", "cot", "sec", "csc", "sinh", "cosh",
              "tanh", "exp", "ln", "log", "lim", "max", "min", "sup", "inf",
              "det", "arg", "mod", "gcd", "Pr", "arcsin", "arccos", "arctan"}

_NUMBER_RE = re.compile(r"[\t ]*\(\s*(\d+(?:\.\d+)?[a-z]?)\s*\)\s*$")


def _script_runs(text: str, table: dict, op: str) -> str:
    out, run = [], ""
    for ch in text + "\0":
        if ch in table:
            run += table[ch]
            continue
        if run:
            out.append(f"{op}{{{run}}}")
            run = ""
        if ch != "\0":
            out.append(ch)
    return "".join(out)


def _word(m: re.Match) -> str:
    word = m.group(0)
    if word in _FUNCTIONS:
        return f"\\{word} "
    # Capital + short lowercase tail: Word's "Lₙ", "Eₐ", "Tₘₐₓ" flattened.
    if len(word) >= 2 and word[0].isupper() and word[1:].islower() \
            and len(word) <= 4:
        tail = word[1:] if len(word) == 2 else r"\text{" + word[1:] + "}"
        return word[0] + "_{" + tail + "}"
    # Anything else ("mc", "nFE") is a product of single-letter symbols.
    return word


def convert(text: str) -> tuple[str, str | None]:
    """Return (latex, equation_number) for Word-flattened equation text.
    The number is the trailing "(2)" Word puts after a tab, or None."""
    s = text.replace(" ", " ").replace(" ", " ").strip()
    number = None
    m = _NUMBER_RE.search(s)
    if m and m.start() > 0:
        number = m.group(1)
        s = s[:m.start()]
    s = _script_runs(s, _SUP, "^")
    s = _script_runs(s, _SUB, "_")
    # Text after a closing delimiter is a flattened subscript: ⟨P⟩hi.
    s = re.sub(r"([⟩〉)\]|])([a-z]{1,4})\b",
               lambda mm: mm.group(1) + r"_{\text{" + mm.group(2) + "}}", s)
    s = re.sub(r"(?<![\\{A-Za-z])[A-Za-z]+(?![A-Za-z}])",
               lambda mm: mm.group(0) if mm.string[max(0, mm.start() - 6):
                                             mm.start()].endswith(r"\text{")
               else _word(mm), s)
    out = []
    for ch in s:
        if ch in _GREEK:
            out.append(f"\\{_GREEK[ch]} ")
        else:
            out.append(_SYMBOLS.get(ch, ch))
    s = "".join(out)
    # Several equations on one line, separated by a comma and a wide gap.
    s = re.sub(r",\s{2,}", r",\\qquad ", s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s, number
