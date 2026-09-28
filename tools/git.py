"""Git tool: read-only status/log/diff, repo jailed under fs_roots."""
from __future__ import annotations

import os
import subprocess

TOOL = {
    "name": "git",
    "description": "Read-only git status/log/diff for a jailed repo.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["status", "log", "diff"]},
            "repo": {"type": "string"},
        },
        "required": ["action", "repo"],
    },
}

CMDS = {
    "status": ["git", "status", "--short", "--branch"],
    "log": ["git", "log", "--oneline", "-20"],
    "diff": ["git", "diff", "--stat"],
}


async def run(args: dict, ctx: dict) -> str:
    action = args.get("action")
    raw = str(args.get("repo", ""))
    if action not in CMDS:
        return "refused: unknown action"
    cfg = (ctx or {}).get("config", {}) or {}
    roots = [os.path.realpath(os.path.expanduser(str(r))) for r in
             (((cfg.get("tools") or {}).get("fs_roots")) or ["~/Projects"])]
    real = os.path.realpath(os.path.expanduser(raw))
    if not any(real == r or real.startswith(r + os.sep) for r in roots):
        return "refused: repo outside fs_roots"
    try:
        proc = subprocess.run(
            CMDS[action], cwd=real, capture_output=True,
            text=True, timeout=60,
        )
    except Exception as exc:
        return f"error: {exc}"
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return (out or "(clean)")[:2000]
