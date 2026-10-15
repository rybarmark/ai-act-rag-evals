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
# A point label alone on a line: "(a)", "a)", "(iv)", "1.", "3.1.", "—". EUR-Lex puts these
# in their own table cell, so they arrive as a separate <p> from the text they label.
_POINT_LABEL = re.compile(r"^(?:\(?[0-9a-z]{1,6}\)|[0-9]{1,3}(?:\.[0-9]{1,3})*\.|[—–-])$")


@dataclass
class Section:
    article: str  # normalised: "5" or "Annex III"
    title: str
    text: str


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r" ([.,;:])(?=\s|$)", r"\1", s)  # "Union ." from get_text(" ") -> "Union."


def _join_point_labels(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if out and _POINT_LABEL.match(out[-1]):
            out[-1] = f"{out[-1]} {line}"
        else:
            out.append(line)
    return out


def _is_heading(tag) -> bool:
    return any(_HEADING_CLASS.search(c) for c in tag.get("class", []))


def _body_text(tag) -> str:
    """Body text of a <p> (unless it is a heading) or of a table cell's own content.

    Some cells hold text directly, outside any <p>: Annex I lists its legislation as
    <td><span>…</span></td>, and Annex VII has <td><span>intro</span><table>…</table></td>.
    Nested <p> and <table> are skipped here; find_all visits them separately.
    """
    if tag.name == "td":
        return " ".join(
            c.get_text(" ") if c.name else str(c)
            for c in tag.children
            if c.name not in ("p", "table", "div")
        )
    return "" if _is_heading(tag) else tag.get_text(" ")


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
        lines = [_clean(_body_text(el)) for el in div.find_all(["p", "td"])]
        lines = _join_point_labels([t for t in lines if t])
        sections.append(Section(article=ref, title=title, text="\n".join(lines)))
    return sections
