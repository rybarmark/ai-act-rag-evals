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


def test_point_label_in_own_cell_is_joined_to_its_text():
    sections = parse_eurlex_html((FIXTURES / "eurlex_sample.html").read_text(encoding="utf-8"))
    lines = sections[0].text.split("\n")
    assert "(d) risk assessments of natural persons based solely on profiling;" in lines
    assert "(d)" not in lines


def test_table_cell_without_paragraph_is_kept():
    sections = parse_eurlex_html((FIXTURES / "eurlex_sample.html").read_text(encoding="utf-8"))
    lines = sections[2].text.split("\n")
    assert "2. Critical infrastructure, as a cell with no paragraph tag." in lines
    # cell with its own text and a nested table: text kept once, nested points in order
    assert lines[-2:] == ["3.1. An intro next to a nested list:", "(a) a nested point."]


def test_space_before_punctuation_is_removed():
    html = '<div id="art_1"><p class="oj-normal">the <span>Union</span> .</p></div>'
    assert parse_eurlex_html(html)[0].text == "the Union."


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
