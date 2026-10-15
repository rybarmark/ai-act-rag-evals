"""Article / Annex references: one normalised form everywhere.

"Art. 5", "Article 5", "Čl. 5", "článek 5" -> "5"
"Annex iii", "Příloha III"                 -> "Annex III"
"""

from __future__ import annotations

import re

_ARTICLE = re.compile(r"^(?:art(?:icle|\.)?|čl(?:ánek|\.)?)?\s*(\d+[a-z]?)$", re.IGNORECASE)
_ANNEX = re.compile(r"^(?:annex|příloha)\s+([ivxlc]+)$", re.IGNORECASE)

# Citations the generator is told to write: [Art. 5] or [Annex III]. Czech variants are
# accepted because models sometimes translate the label in Czech answers.
_CITATION = re.compile(
    r"\[\s*((?:Art(?:icle|\.)?|Čl(?:ánek|\.)?)\s*\d+[a-z]?|(?:Annex|Příloha)\s+[IVXLC]+)\s*\]",
    re.IGNORECASE,
)


def normalise_ref(ref: str) -> str:
    ref = ref.strip()
    if m := _ANNEX.match(ref):
        return f"Annex {m.group(1).upper()}"
    if m := _ARTICLE.match(ref):
        return m.group(1).lower()
    raise ValueError(f"Not an Article or Annex reference: {ref!r}")


def display_ref(ref: str) -> str:
    """Normalised ref -> the label used in prompts: "Art. 5" or "Annex III"."""
    return ref if ref.startswith("Annex") else f"Art. {ref}"


def extract_citations(text: str) -> list[str]:
    """Unique normalised references in the order they first appear."""
    found: list[str] = []
    for m in _CITATION.finditer(text):
        ref = normalise_ref(m.group(1))
        if ref not in found:
            found.append(ref)
    return found
