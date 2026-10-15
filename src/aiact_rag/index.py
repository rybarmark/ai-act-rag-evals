"""Embeddings and a small in-memory vector index.

A few hundred chunks need no vector database: a NumPy matrix and a dot product are
fast, and nothing is hidden from the reader.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from aiact_rag.models import Chunk, RetrievedChunk


class Embedder(Protocol):
    def embed_passages(self, texts: list[str]) -> np.ndarray: ...
    def embed_query(self, text: str) -> np.ndarray: ...


class E5Embedder:
    """intfloat/multilingual-e5-*: expects "query: " / "passage: " prefixes."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # optional dependency

        self.model = SentenceTransformer(model_name)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            [f"passage: {t}" for t in texts], normalize_embeddings=True, batch_size=32
        )

    def embed_query(self, text: str) -> np.ndarray:
        return self.model.encode([f"query: {text}"], normalize_embeddings=True)[0]


class VectorIndex:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray):
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors differ in length")
        self.chunks = chunks
        self.vectors = np.asarray(vectors, dtype=np.float32)

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> VectorIndex:
        return cls(chunks, embedder.embed_passages([c.text for c in chunks]))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, vectors=self.vectors, ids=np.array([c.id for c in self.chunks]))

    @classmethod
    def load(cls, path: Path, chunks: list[Chunk]) -> VectorIndex:
        data = np.load(path)
        by_id = {c.id: c for c in chunks}
        missing = [i for i in data["ids"] if str(i) not in by_id]
        if missing:
            raise ValueError(f"index has {len(missing)} chunk ids not in chunks.jsonl; rebuild it")
        return cls([by_id[str(i)] for i in data["ids"]], data["vectors"])

    def search(self, query_vec: np.ndarray, k: int, lang: str | None = None) -> list[RetrievedChunk]:
        scores = self.vectors @ np.asarray(query_vec, dtype=np.float32)
        results: list[RetrievedChunk] = []
        for i in np.argsort(-scores):
            chunk = self.chunks[int(i)]
            if lang and chunk.lang != lang:
                continue
            results.append(RetrievedChunk(chunk=chunk, score=float(scores[i])))
            if len(results) == k:
                break
        return results
