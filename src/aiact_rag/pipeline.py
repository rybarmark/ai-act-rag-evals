"""The system under test: question in, Answer (text + citations + retrieved chunks) out."""

from __future__ import annotations

from aiact_rag.config import Settings
from aiact_rag.index import E5Embedder, Embedder, VectorIndex
from aiact_rag.ingest.chunk import load_chunks
from aiact_rag.llm import LLMClient, make_client
from aiact_rag.models import Answer
from aiact_rag.prompts import ANSWER_SYSTEM, REFUSAL_MARKER, build_answer_prompt
from aiact_rag.refs import extract_citations


class RagPipeline:
    def __init__(
        self,
        index: VectorIndex,
        embedder: Embedder,
        llm: LLMClient,
        *,
        top_k: int = 5,
        max_tokens: int = 2000,
        corpus_version: str = "unknown",
    ):
        self.index = index
        self.embedder = embedder
        self.llm = llm
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.corpus_version = corpus_version

    @classmethod
    def from_settings(cls, s: Settings) -> RagPipeline:
        chunks = load_chunks(s.path(s.corpus.chunks_path))
        index = VectorIndex.load(s.path(s.corpus.index_path), chunks)
        return cls(
            index,
            E5Embedder(s.retrieval.embedding_model),
            make_client(s.generation),
            top_k=s.retrieval.top_k,
            max_tokens=s.generation.max_tokens,
            corpus_version=s.corpus.version,
        )

    def answer(self, question: str, lang: str) -> Answer:
        retrieved = self.index.search(self.embedder.embed_query(question), self.top_k, lang=lang)
        raw = self.llm.complete(
            ANSWER_SYSTEM,
            build_answer_prompt(question, retrieved),
            max_tokens=self.max_tokens,
        ).strip()
        refused = raw.startswith(REFUSAL_MARKER)
        return Answer(
            question=question,
            lang=lang,
            text=raw,
            citations=[] if refused else extract_citations(raw),
            retrieved=retrieved,
            refused=refused,
            model=self.llm.model,
            corpus_version=self.corpus_version,
        )
