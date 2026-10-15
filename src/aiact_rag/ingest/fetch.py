"""Download the AI Act XHTML from the EU Publications Office (CELLAR).

The eur-lex.europa.eu pages sit behind a JavaScript bot check that scripts cannot pass
(HTTP 202, empty body). CELLAR is the Publications Office's machine-readable endpoint for
the same documents: one URL per CELEX number, language chosen with Accept-Language, and the
same <div id="art_N"> / "anx_N" markup that the parser relies on.
"""

from __future__ import annotations

from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "ai-act-rag-evals/0.1 (portfolio project; contact via GitHub)",
    "Accept": "application/xhtml+xml, text/html;q=0.9",
}
# CELLAR selects the language version by ISO 639-2 code.
_CELLAR_LANG = {"en": "eng", "cs": "ces"}


def fetch(url: str, lang: str, dest: Path, timeout: int = 120) -> Path:
    headers = {**HEADERS, "Accept-Language": _CELLAR_LANG[lang]}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    if 'id="art_1"' not in resp.text:
        raise RuntimeError(
            f"{url} ({lang}) returned no Article markup (HTTP {resp.status_code}, "
            f"{len(resp.text)} chars). Save the page from a browser as {dest} instead."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(resp.text, encoding="utf-8")
    return dest
