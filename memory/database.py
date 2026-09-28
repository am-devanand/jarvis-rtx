"""SQLite memory: facts (+FTS5 or LIKE fallback), turns, projects."""
from __future__ import annotations

import sqlite3
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS facts(id INTEGER PRIMARY KEY, text TEXT, tag TEXT, created REAL);
CREATE TABLE IF NOT EXISTS turns(id INTEGER PRIMARY KEY, role TEXT, text TEXT, created REAL);
CREATE TABLE IF NOT EXISTS projects(name TEXT PRIMARY KEY, root TEXT, notes TEXT);
"""


class Memory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db = sqlite3.connect(db_path)
        self._db.executescript(_SCHEMA)
        self._fts = False
        try:
            self._db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(text, tag)"
            )
            self._fts = True
        except sqlite3.OperationalError:
            self._fts = False

    def add_fact(self, text: str, tag: str = "") -> None:
        now = time.time()
        cur = self._db.execute(
            "INSERT INTO facts(text, tag, created) VALUES (?, ?, ?)",
            (text, tag, now),
        )
        if self._fts:
            self._db.execute(
                "INSERT INTO facts_fts(rowid, text, tag) VALUES (?, ?, ?)",
                (cur.lastrowid, text, tag),
            )
        self._db.commit()

    def get_facts(self, tag: str | None = None, limit: int = 20) -> list[str]:
        if tag:
            rows = self._db.execute(
                "SELECT text FROM facts WHERE tag = ? ORDER BY id DESC LIMIT ?",
                (tag, limit),
            ).fetchall()
            return [r[0] for r in rows]
        rows = self._db.execute(
            "SELECT text FROM facts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        texts = [r[0] for r in rows]
        if not texts:
            return []
        # Prefer FTS match ordering when available is unnecessary; LIKE demo:
        return texts

    def search_facts(self, query: str, limit: int = 20) -> list[str]:
        if self._fts:
            rows = self._db.execute(
                "SELECT text FROM facts_fts WHERE facts_fts MATCH ? LIMIT ?",
                (query, limit),
            ).fetchall()
            if rows:
                return [r[0] for r in rows]
        like = f"%{query}%"
        rows = self._db.execute(
            "SELECT text FROM facts WHERE text LIKE ? OR tag LIKE ? LIMIT ?",
            (like, like, limit),
        ).fetchall()
        return [r[0] for r in rows]

    def log_turn(self, role: str, text: str) -> None:
        self._db.execute(
            "INSERT INTO turns(role, text, created) VALUES (?, ?, ?)",
            (role, text, time.time()),
        )
        self._db.commit()

    def recent_turns(self, n: int = 12) -> list[dict]:
        rows = self._db.execute(
            "SELECT role, text FROM turns ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [{"role": r[0], "text": r[1]} for r in reversed(rows)]

    def save_project(self, name: str, root: str, notes: str) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO projects(name, root, notes) VALUES (?, ?, ?)",
            (name, root, notes),
        )
        self._db.commit()

    def get_project(self, name: str) -> dict | None:
        row = self._db.execute(
            "SELECT name, root, notes FROM projects WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return {"name": row[0], "root": row[1], "notes": row[2]}
