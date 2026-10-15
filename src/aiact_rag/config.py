"""Typed access to config/settings.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS = ROOT / "config" / "settings.yaml"


class CorpusSettings(BaseModel):
    version: str
    languages: list[str]
    sources: dict[str, str]
    raw_dir: Path
    chunks_path: Path
    index_path: Path


class RetrievalSettings(BaseModel):
    embedding_model: str
    top_k: int = 5
    max_chunk_chars: int = 4000


class ModelSettings(BaseModel):
    provider: str = "anthropic"
    model: str
    max_tokens: int = 800
    temperature: float = 0.0


class EvalSettings(BaseModel):
    repeats: int = 3
    smoke_size: int = 20
    golden_files: list[Path]
    results_dir: Path
    baseline_path: Path
    max_drop_pp: float = 3.0
    thresholds: dict[str, float]


class Settings(BaseModel):
    corpus: CorpusSettings
    retrieval: RetrievalSettings
    generation: ModelSettings
    judge: ModelSettings
    eval: EvalSettings

    @staticmethod
    def path(p: Path) -> Path:
        """Resolve a repo-relative path from the settings file."""
        return p if p.is_absolute() else ROOT / p


def load_settings(path: Path | None = None) -> Settings:
    data = yaml.safe_load((path or DEFAULT_SETTINGS).read_text(encoding="utf-8"))
    return Settings.model_validate(data)
