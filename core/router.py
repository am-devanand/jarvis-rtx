"""Router: text -> {kind, model, tools, steps}. Stdlib only."""
from __future__ import annotations

import re
from pathlib import Path

TOOL_NAMES = [
    "terminal", "filesystem", "browser", "screenshot",
    "applications", "git", "system", "trading_chart",
]

_CHAT_DEFAULT = "qwen3:4b"
_VISION_DEFAULT = "qwen3-vl:4b"


def _resolve_models() -> tuple[str, str]:
    chat, vision = _CHAT_DEFAULT, _VISION_DEFAULT
    try:
        cfg = Path(__file__).resolve().parent.parent / "config.yaml"
        if cfg.exists():
            try:
                import yaml  # type: ignore
            except Exception:
                yaml = None  # type: ignore
            if yaml is not None:
                data = yaml.safe_load(cfg.read_text()) or {}
                m = data.get("models", {}) or {}
                chat = str(m.get("chat", chat))
                vision = str(m.get("vision", vision))
    except Exception:
        pass
    return chat, vision


VISION_WORDS = [
    "image", "picture", "photo", "screenshot", "screen",
    "chart", "graph", "plot", "terminal error", "traceback",
    "what is on screen", "on my screen",
]
CODE_WORDS = [
    "python", "react", "git ", " git", "debug", "dsa",
    "algorithm", "linked list", "binary tree", "javascript",
    "typescript", "function", "code",
]
TOOL_HINTS: list[tuple[str, list[str]]] = [
    ("terminal", ["terminal", "command", "run ", "execute", "shell", "kill", "process"]),
    ("filesystem", ["find ", "find file", "file", "folder", "directory", "list files", "read file"]),
    ("browser", ["web", "search", "browse", "url", "site", "google"]),
    ("screenshot", ["screenshot", "capture screen"]),
    ("applications", ["open ", "launch", "close ", "window", "app", "firefox", "chrome"]),
    ("git", ["commit", "push", "pull", "branch", "checkout", "merge"]),
    ("system", ["status", "cpu", "memory", "ram", "disk", "battery", "volume"]),
    ("trading_chart", ["trading", "stock", "price", "candle", "chart"]),
]

MULTI_RE = re.compile(r"\band then\b", re.IGNORECASE)


def _split_steps(text: str) -> list[str]:
    parts = MULTI_RE.split(text)
    if len(parts) == 1 and "," in text:
        parts = [p for p in text.split(",")]
    else:
        flat: list[str] = []
        for p in parts:
            flat.extend([s for s in p.split(",")])
        parts = flat
    steps = [p.strip(" .,;") for p in parts]
    steps = [s for s in steps if s]
    if len(steps) >= 2:
        if MULTI_RE.search(text) or "," in text:
            return steps[:5]
    return [text.strip()] if text.strip() else []


def route(text: str) -> dict:
    chat_model, vision_model = _resolve_models()
    low = text.lower().strip()

    steps = _split_steps(text)
    if len(steps) >= 2:
        tools = _match_tools(low)
        return {"kind": "multi", "model": chat_model, "tools": tools, "steps": steps}

    if any(w in low for w in VISION_WORDS):
        return {"kind": "vision", "model": vision_model, "tools": [], "steps": []}

    if any(w in low for w in CODE_WORDS):
        return {"kind": "code", "model": chat_model, "tools": [], "steps": []}

    tools = _match_tools(low)
    if tools:
        return {"kind": "tool", "model": chat_model, "tools": tools, "steps": []}

    return {"kind": "chat", "model": chat_model, "tools": [], "steps": []}


def _match_tools(low: str) -> list[str]:
    found: list[str] = []
    for name, words in TOOL_HINTS:
        if any(w in low for w in words):
            found.append(name)
    # dedupe, preserve TOOL_NAMES order
    return [t for t in TOOL_NAMES if t in found]
