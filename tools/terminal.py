"""Terminal tool: allowlisted subprocess only."""
from __future__ import annotations

import shlex
import subprocess

TOOL = {
    "name": "terminal",
    "description": "Run an allowlisted shell command (first token must be allowed).",
    "parameters": {
        "type": "object",
        "properties": {"cmd": {"type": "string"}},
        "required": ["cmd"],
    },
}

DEFAULT_ALLOW = ["ls", "cat", "git", "python3", "npm", "systemctl", "ps"]


async def run(args: dict, ctx: dict) -> str:
    cmd = str(args.get("cmd", "")).strip()
    if not cmd:
        return "refused: empty cmd"
    cfg = (ctx or {}).get("config", {}) or {}
    allowed = ((cfg.get("tools") or {}).get("allow_terminal")) or DEFAULT_ALLOW
    try:
        first = shlex.split(cmd, posix=True)[0]
    except ValueError as exc:
        return f"refused: {exc}"
    base = first.rsplit("/", 1)[-1]
    if base not in allowed:
        return f"refused: '{base}' not in allowlist"
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return "timeout after 60s"
    except Exception as exc:
        return f"error: {exc}"
    out = (proc.stdout or "") + (proc.stderr or "")
    out = out.strip() or f"(exit {proc.returncode}, no output)"
    return out[:2000]
