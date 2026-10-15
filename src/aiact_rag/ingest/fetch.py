"""Download the AI Act HTML from EUR-Lex.

EUR-Lex sometimes answers scripts with a bot-check page. If the saved file does not
contain any Articles, open the URL in a browser, save the page as
data/raw/<lang>.html, and run `aiact parse`.
"""

from __future__ import annotations

from pathlib import Path

import requests

HEADERS = {"User-Agent": "ai-act-rag-evals/0.1 (portfolio project; contact via GitHub)"}


def fetch(url: str, dest: Path, timeout: int = 60) -> Path:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(resp.text, encoding="utf-8")
    if 'id="art_1"' not in resp.text:
        print(f"WARNING: {dest} has no Article markup. Download it manually (see module docstring).")
    return dest
