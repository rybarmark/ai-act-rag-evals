from conftest import FIXTURES

from aiact_rag.ingest.chunk import chunk_sections, load_chunks, save_chunks
from aiact_rag.ingest.parse import Section, parse_eurlex_html


def test_parse_articles_and_annexes():
    sections = parse_eurlex_html((FIXTURES / "eurlex_sample.html").read_text(encoding="utf-8"))
    assert [s.article for s in sections] == ["5", "99", "Annex III"]
    assert sections[0].title == "Prohibited AI practices"
    assert sections[2].title == "High-risk AI systems referred to in Article 6(2)"
    assert "social scoring" in sections[0].text
    assert "Article 5" not in sections[0].text  # heading lines are not body text
    assert "recital" not in " ".join(s.text for s in sections).lower()


def test_chunk_header_and_ids():
    chunks = chunk_sections([Section("99", "Penalties", "body")], "cs")
    assert chunks[0].id == "cs-99-p0"
    assert chunks[0].text.startswith("Článek 99 – Penalties")


def test_long_article_is_split():
    text = "\n".join(f"line {i} " + "x" * 50 for i in range(40))
    chunks = chunk_sections([Section("6", "Classification", text)], "en", max_chars=500)
    assert len(chunks) > 1
    assert len({c.id for c in chunks}) == len(chunks)
    assert all(c.article == "6" for c in chunks)


def test_save_load_roundtrip(tmp_path, chunks):
    path = tmp_path / "chunks.jsonl"
    save_chunks(chunks, path)
    assert load_chunks(path) == chunks
