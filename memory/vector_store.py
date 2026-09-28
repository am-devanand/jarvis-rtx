"""Vector memory: sqlite chunks+embeddings, cosine search, embed_fn injected."""
from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Callable


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class VectorMemory:
    def __init__(self, db_path: str, embed_fn: Callable[[str], list[float]] | None = None):
        self.db_path = db_path
        self.embed_fn = embed_fn
        self._db = sqlite3.connect(db_path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, text TEXT, vec TEXT)"
        )
        self._db.commit()

    def add(self, text: str) -> None:
        vec: list[float] = self.embed_fn(text) if self.embed_fn else []
        self._db.execute(
            "INSERT INTO chunks(text, vec) VALUES (?, ?)",
            (text, json.dumps(vec)),
        )
        self._db.commit()

    def search(self, query_vec: list[float], k: int = 5) -> list[str]:
        rows = self._db.execute("SELECT text, vec FROM chunks").fetchall()
        scored: list[tuple[float, str]] = []
        for text, vec_json in rows:
            try:
                vec = json.loads(vec_json or "[]")
            except json.JSONDecodeError:
                continue
            if not vec or not query_vec or len(vec) != len(query_vec):
                continue
            scored.append((_cosine(query_vec, vec), text))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [t[1] for t in scored[:k]]
