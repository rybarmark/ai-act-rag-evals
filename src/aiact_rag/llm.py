"""LLM clients behind one small interface, plus a fake for tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from aiact_rag.config import ModelSettings


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, user: str, *, max_tokens: int, temperature: float) -> str: ...


class AnthropicClient:
    def __init__(self, model: str):
        import anthropic

        self.model = model
        self._client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

    def complete(self, system: str, user: str, *, max_tokens: int, temperature: float) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")


class FakeLLM:
    """Returns a fixed string, or whatever `responder(system, user)` returns."""

    def __init__(self, responder: str | Callable[[str, str], str], model: str = "fake"):
        self.responder = responder
        self.model = model
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, *, max_tokens: int, temperature: float) -> str:
        self.calls.append((system, user))
        return self.responder if isinstance(self.responder, str) else self.responder(system, user)


def make_client(settings: ModelSettings) -> LLMClient:
    if settings.provider == "anthropic":
        return AnthropicClient(settings.model)
    raise ValueError(f"Unknown provider: {settings.provider}")
