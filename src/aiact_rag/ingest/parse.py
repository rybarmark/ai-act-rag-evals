"""Parse EUR-Lex HTML into one section per Article and Annex.

EUR-Lex marks each Article with <div id="art_N"> and each Annex with <div id="anx_N">.
These ids are the same in every language version, which is what makes the EN and CS
corpora comparable. Check this against the HTML you downloaded: EUR-Lex has changed its
markup before. tests/fixtures/eurlex_sample.html is a simplified copy of the structure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

_ARTICLE_ID = re.compile(r"^art_(\d+[a-z]?)$")
_ANNEX_ID = re.compile(r"^anx_([IVXLC]+)$")
_HEADING_CLASS = re.compile(r"(?:^|-)(?:ti-art|sti-art|doc-ti)$")


@dataclass
class Section:
    article: str  # normalised: "5" or "Annex III"
    title: str
    text: str


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _is_heading(tag) -> bool:
    return any(_HEADING_CLASS.search(c) for c in tag.get("class", []))


def parse_eurlex_html(html: str) -> list[Section]:
    soup = BeautifulSoup(html, "html.parser")
    sections: list[Section] = []
    for div in soup.find_all("div", id=True):
        art, anx = _ARTICLE_ID.match(div["id"]), _ANNEX_ID.match(div["id"])
        if not (art or anx):
            continue
        if art:
            ref = art.group(1)
            title_el = div.find(class_=re.compile(r"sti-art"))
            title = _clean(title_el.get_text(" ")) if title_el else ""
        else:
            ref = f"Annex {anx.group(1)}"
            headings = div.find_all(class_=re.compile(r"doc-ti"))
            title = _clean(headings[1].get_text(" ")) if len(headings) > 1 else ""
        lines = [_clean(p.get_text(" ")) for p in div.find_all("p") if not _is_heading(p)]
        sections.append(Section(article=ref, title=title, text="\n".join(t for t in lines if t)))
    return sections
