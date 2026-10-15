"""aiact fetch | parse | build-index | ask "question" [--lang cs]"""

from __future__ import annotations

import argparse
from collections import Counter

from dotenv import load_dotenv

from aiact_rag.config import load_settings


def _fetch(s, _args) -> None:
    from aiact_rag.ingest.fetch import fetch

    for lang in s.corpus.languages:
        dest = s.path(s.corpus.raw_dir) / f"{lang}.html"
        print(f"{lang}: {fetch(s.corpus.sources[lang], dest)}")


def _parse(s, _args) -> None:
    from aiact_rag.ingest.chunk import chunk_sections, save_chunks
    from aiact_rag.ingest.parse import parse_eurlex_html

    chunks = []
    for lang in s.corpus.languages:
        html = (s.path(s.corpus.raw_dir) / f"{lang}.html").read_text(encoding="utf-8")
        sections = parse_eurlex_html(html)
        articles = sum(1 for x in sections if not x.article.startswith("Annex"))
        print(f"{lang}: {articles} Articles, {len(sections) - articles} Annexes")
        chunks += chunk_sections(sections, lang, s.retrieval.max_chunk_chars)
    counts = Counter(c.lang for c in chunks)
    if len(set(counts.values())) > 1:
        print(f"WARNING: languages have different chunk counts: {dict(counts)}")
    save_chunks(chunks, s.path(s.corpus.chunks_path))
    print(f"saved {len(chunks)} chunks -> {s.corpus.chunks_path}")


def _build_index(s, _args) -> None:
    from aiact_rag.index import E5Embedder, VectorIndex
    from aiact_rag.ingest.chunk import load_chunks

    chunks = load_chunks(s.path(s.corpus.chunks_path))
    index = VectorIndex.build(chunks, E5Embedder(s.retrieval.embedding_model))
    index.save(s.path(s.corpus.index_path))
    print(f"indexed {len(chunks)} chunks -> {s.corpus.index_path}")


def _ask(s, args) -> None:
    from aiact_rag.pipeline import RagPipeline

    a = RagPipeline.from_settings(s).answer(args.question, args.lang)
    print(a.text)
    print(f"\ncited: {a.citations or '-'}   retrieved: {a.retrieved_articles}   refused: {a.refused}")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="aiact")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="download EN and CS HTML from EUR-Lex")
    sub.add_parser("parse", help="raw HTML -> data/processed/chunks.jsonl")
    sub.add_parser("build-index", help="chunks -> embeddings index")
    ask = sub.add_parser("ask", help="ask one question")
    ask.add_argument("question")
    ask.add_argument("--lang", default="en", choices=["en", "cs"])
    args = parser.parse_args()
    handlers = {"fetch": _fetch, "parse": _parse, "build-index": _build_index, "ask": _ask}
    handlers[args.cmd](load_settings(), args)


if __name__ == "__main__":
    main()
