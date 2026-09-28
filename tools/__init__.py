"""Jarvis tools registry.

Safety rule (read once): every dangerous op needs an allowlist or an
explicit user confirm. Terminal commands are allowlisted by first token,
filesystem/git paths are jailed under tools.fs_roots, app launches are
allowlisted, and destructive ops (system killport) require
`await ctx["confirm"](prompt)` or they return "needs confirmation".
"""
from __future__ import annotations

REGISTRY: dict[str, str] = {
    "terminal": "tools.terminal",
    "filesystem": "tools.filesystem",
    "browser": "tools.browser",
    "screenshot": "tools.screenshot",
    "applications": "tools.applications",
    "git": "tools.git",
    "system": "tools.system",
    "trading_chart": "tools.trading_chart",
}

MAX_OUT = 2000


def _short(text: str) -> str:
    if len(text) > MAX_OUT:
        return text[:MAX_OUT] + "...[truncated]"
    return text


async def dispatch(name: str, args: dict, ctx: dict) -> str:
    """Dispatch to a registered tool. Raises RuntimeError("unknown tool")."""
    if name not in REGISTRY:
        raise RuntimeError("unknown tool")
    import importlib

    mod = importlib.import_module(REGISTRY[name])
    result = await mod.run(args or {}, ctx or {})
    return _short(str(result))
