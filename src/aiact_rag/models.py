"""Data passed between the pipeline and the eval harness."""

from __future__ import annotations

from pydantic import BaseModel


class Chunk(BaseModel):
    id: str
    lang: str
    article: str  # normalised reference: "5", "Annex III"
    title: str = ""
    part: int = 0
    text: str


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float


class Answer(BaseModel):
    question: str
    lang: str
    text: str
    citations: list[str]  # normalised references the answer cites
    retrieved: list[RetrievedChunk]
    refused: bool
    model: str
    corpus_version: str

    @property
    def retrieved_articles(self) -> list[str]:
        seen: list[str] = []
        for r in self.retrieved:
            if r.chunk.article not in seen:
                seen.append(r.chunk.article)
        return seen
