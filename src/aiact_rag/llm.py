"""LLM clients behind one small interface, plus a fake for tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from aiact_rag.config import ModelSettings


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, user: str, *, max_tokens: int) -> str: ...


class AnthropicClient:
    def __init__(self, model: str, effort: str | None = None):
        import anthropic

        self.model = model
        self.effort = effort
        # Credentials from the environment: ANTHROPIC_API_KEY locally, Workload Identity
        # Federation env vars in CI.
        self._client = anthropic.Anthropic()

    def complete(self, system: str, user: str, *, max_tokens: int) -> str:
        # No temperature: current models only accept the default. Thinking is adaptive by
        # default, its tokens count toward max_tokens, and `effort` sets how much it thinks.
        extra = {"output_config": {"effort": self.effort}} if self.effort else {}
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            **extra,
        )
        # Content may start with thinking blocks; keep only the text.
        return "".join(block.text for block in resp.content if block.type == "text")


class FakeLLM:
    """Returns a fixed string, or whatever `responder(system, user)` returns."""

    def __init__(self, responder: str | Callable[[str, str], str], model: str = "fake"):
        self.responder = responder
        self.model = model
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, *, max_tokens: int) -> str:
        self.calls.append((system, user))
        return self.responder if isinstance(self.responder, str) else self.responder(system, user)


def make_client(settings: ModelSettings) -> LLMClient:
    if settings.provider == "anthropic":
        return AnthropicClient(settings.model, settings.effort)
    raise ValueError(f"Unknown provider: {settings.provider}")
