"""Golden cases and results. A malformed golden case fails at load time, not mid-run."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from aiact_rag.models import Answer
from aiact_rag.refs import normalise_ref


class Category(str, Enum):
    factual = "factual"
    classification = "classification"
    dates = "dates"
    multi_article = "multi_article"
    out_of_scope = "out_of_scope"
    false_premise = "false_premise"
    adversarial = "adversarial"


class GoldenCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: Category
    lang: Literal["en", "cs"]
    question: str
    expected_articles: list[str] = []
    reference_answer: str | None = None
    should_refuse: bool = False
    pair_id: str | None = None  # links an EN case to its CS twin
    version_sensitive: bool = False  # answer depends on which corpus version is indexed
    notes: str = ""

    @model_validator(mode="after")
    def _consistent(self) -> GoldenCase:
        if self.should_refuse and self.expected_articles:
            raise ValueError(f"{self.id}: refusal cases must not list expected_articles")
        if not self.should_refuse and not self.expected_articles:
            raise ValueError(f"{self.id}: answerable cases need expected_articles")
        if not self.should_refuse and not self.reference_answer:
            raise ValueError(f"{self.id}: answerable cases need a reference_answer")
        self.expected_articles = [normalise_ref(a) for a in self.expected_articles]
        return self


class GradeResult(BaseModel):
    grader: str
    passed: bool | None  # None = not applicable to this case
    reason: str = ""


class CaseRun(BaseModel):
    case_id: str
    run: int
    answer: Answer
    grades: list[GradeResult]
