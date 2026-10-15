import hashlib
import re
from pathlib import Path

import numpy as np
import pytest

from aiact_rag.index import VectorIndex
from aiact_rag.models import Answer, Chunk, RetrievedChunk

FIXTURES = Path(__file__).parent / "fixtures"


class HashEmbedder:
    """Deterministic bag-of-words embedder: no model download, good enough to test search."""

    dim = 256

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for word in re.findall(r"\w+", text.lower()):
            v[int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dim] += 1
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed_passages(self, texts):
        return np.stack([self._vec(t) for t in texts])

    def embed_query(self, text):
        return self._vec(text)


@pytest.fixture
def embedder():
    return HashEmbedder()


@pytest.fixture
def chunks():
    return [
        Chunk(id="en-5-p0", lang="en", article="5", title="Prohibited AI practices",
              text="Article 5 Prohibited AI practices social scoring manipulation"),
        Chunk(id="en-99-p0", lang="en", article="99", title="Penalties",
              text="Article 99 Penalties administrative fines EUR 35 000 000 turnover"),
        Chunk(id="en-50-p0", lang="en", article="50", title="Transparency obligations",
              text="Article 50 Transparency informed interacting with an AI system chatbot"),
        Chunk(id="cs-99-p0", lang="cs", article="99", title="Sankce",
              text="Článek 99 Sankce správní pokuty 35 000 000 EUR obrat"),
    ]


@pytest.fixture
def index(chunks, embedder):
    return VectorIndex.build(chunks, embedder)


def make_answer(text="", citations=(), retrieved=("99",), refused=False, lang="en"):
    return Answer(
        question="q", lang=lang, text=text, citations=list(citations), refused=refused,
        retrieved=[RetrievedChunk(chunk=Chunk(id=f"{lang}-{a}", lang=lang, article=a, text=a), score=1.0)
                   for a in retrieved],
        model="fake", corpus_version="test",
    )
