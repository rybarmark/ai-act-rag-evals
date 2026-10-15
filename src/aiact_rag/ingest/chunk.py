"""Turn parsed sections into retrieval chunks.

One chunk per Article; long Articles are split at line breaks into parts. Every chunk
starts with a header naming its Article, so the embedding and the generator both know
where the text comes from, and retrieval can be graded by Article number.
"""

from __future__ import annotations

import json
from pathlib import Path

from aiact_rag.ingest.parse import Section
from aiact_rag.models import Chunk

_LABELS = {
    "en": {"article": "Article", "annex": "Annex"},
    "cs": {"article": "Článek", "annex": "Příloha"},
}


def _header(section: Section, lang: str) -> str:
    labels = _LABELS.get(lang, _LABELS["en"])
    if section.article.startswith("Annex"):
        name = f"{labels['annex']} {section.article.split()[1]}"
    else:
        name = f"{labels['article']} {section.article}"
    return f"{name} – {section.title}" if section.title else name


def _split(text: str, max_chars: int) -> list[str]:
    parts, current = [], ""
    for line in text.split("\n"):
        if current and len(current) + len(line) + 1 > max_chars:
            parts.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        parts.append(current)
    return parts or [""]


def chunk_sections(sections: list[Section], lang: str, max_chars: int = 4000) -> list[Chunk]:
    chunks: list[Chunk] = []
    for s in sections:
        header = _header(s, lang)
        slug = s.article.replace(" ", "").lower()
        for i, body in enumerate(_split(s.text, max_chars)):
            chunks.append(
                Chunk(
                    id=f"{lang}-{slug}-p{i}",
                    lang=lang,
                    article=s.article,
                    title=s.title,
                    part=i,
                    text=f"{header}\n{body}",
                )
            )
    return chunks


def save_chunks(chunks: list[Chunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(c.model_dump_json() + "\n")


def load_chunks(path: Path) -> list[Chunk]:
    with path.open(encoding="utf-8") as f:
        return [Chunk.model_validate(json.loads(line)) for line in f if line.strip()]
