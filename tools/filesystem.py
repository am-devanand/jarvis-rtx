"""Filesystem tool: jailed under tools.fs_roots."""
from __future__ import annotations

import os

TOOL = {
    "name": "filesystem",
    "description": "Read/write/list files confined under fs_roots.",
    "parameters": {
        "type": "object",
        "properties": {
            "op": {"type": "string", "enum": ["read", "write", "list"]},
            "path": {"type": "string"},
            "text": {"type": "string"},
        },
        "required": ["op", "path"],
    },
}


def _roots(ctx: dict) -> list[str]:
    cfg = (ctx or {}).get("config", {}) or {}
    roots = ((cfg.get("tools") or {}).get("fs_roots")) or ["~/Projects"]
    return [os.path.realpath(os.path.expanduser(str(r))) for r in roots]


def _jailed(path: str, roots: list[str]) -> str | None:
    real = os.path.realpath(os.path.expanduser(path))
    for root in roots:
        if real == root or real.startswith(root + os.sep):
            return real
    return None


async def run(args: dict, ctx: dict) -> str:
    op = args.get("op")
    raw = str(args.get("path", ""))
    roots = _roots(ctx or {})
    real = _jailed(raw, roots)
    if real is None:
        return "refused: path outside fs_roots"
    if op == "read":
        try:
            with open(real, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read(2000 * 4)[:2000]
        except Exception as exc:
            return f"error: {exc}"
    if op == "write":
        text = str(args.get("text", ""))
        try:
            os.makedirs(os.path.dirname(real) or ".", exist_ok=True)
            with open(real, "w", encoding="utf-8") as fh:
                fh.write(text)
            return f"wrote {len(text)} chars to {real}"
        except Exception as exc:
            return f"error: {exc}"
    if op == "list":
        try:
            names = sorted(os.listdir(real))
            return "\n".join(names)[:2000] or "(empty)"
        except Exception as exc:
            return f"error: {exc}"
    return "refused: unknown op"
