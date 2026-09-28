"""Rolling conversation window (last 12 turns)."""
from __future__ import annotations

MAX_TURNS = 12


class ConversationContext:
    def __init__(self, max_turns: int = MAX_TURNS):
        self.max_turns = max_turns
        self._turns: list[dict] = []

    def add(self, role: str, content: str) -> None:
        self._turns.append({"role": role, "content": content})
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns:]

    def history(self) -> list[dict]:
        return list(self._turns)

    def as_messages(self, system: str | None = None) -> list[dict]:
        msgs: list[dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(self._turns)
        return msgs

    def clear(self) -> None:
        self._turns = []
