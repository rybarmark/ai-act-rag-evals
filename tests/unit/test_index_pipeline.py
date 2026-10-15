from aiact_rag.index import VectorIndex
from aiact_rag.llm import FakeLLM
from aiact_rag.pipeline import RagPipeline
from aiact_rag.prompts import REFUSAL_MARKER


def test_search_ranks_relevant_chunk_first(index, embedder):
    hits = index.search(embedder.embed_query("administrative fines penalties"), k=2, lang="en")
    assert hits[0].chunk.article == "99"
    assert all(h.chunk.lang == "en" for h in hits)


def test_index_save_load(tmp_path, index, chunks):
    index.save(tmp_path / "i.npz")
    loaded = VectorIndex.load(tmp_path / "i.npz", chunks)
    assert [c.id for c in loaded.chunks] == [c.id for c in chunks]


def test_pipeline_parses_citations(index, embedder):
    llm = FakeLLM("Fines reach EUR 35 million [Art. 99].")
    a = RagPipeline(index, embedder, llm, top_k=2).answer("maximum fines", "en")
    assert a.citations == ["99"] and not a.refused
    _system, user = llm.calls[0]
    assert "<question>" in user and 'ref="Art. 99"' in user


def test_pipeline_detects_refusal(index, embedder):
    a = RagPipeline(index, embedder, FakeLLM(REFUSAL_MARKER)).answer("VAT rate?", "en")
    assert a.refused and a.citations == []
