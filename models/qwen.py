"""Ollama chat via /api/chat. Stdlib + requests only."""
from __future__ import annotations

from pathlib import Path

import requests

_DEFAULT_MODEL = "qwen3:4b"
_DEFAULT_URL = "http://localhost:11434"


def _config_defaults() -> tuple[str, str]:
    model, url = _DEFAULT_MODEL, _DEFAULT_URL
    try:
        cfg = Path(__file__).resolve().parent.parent / "config.yaml"
        if cfg.exists():
            try:
                import yaml  # type: ignore

                data = yaml.safe_load(cfg.read_text()) or {}
            except Exception:
                data = {}
            m = (data or {}).get("models", {}) or {}
            model = str(m.get("chat", model))
            url = str((data or {}).get("ollama_url", url))
    except Exception:
        pass
    return model, url


def chat(
    messages: list[dict],
    model: str | None = None,
    images: list[str] | None = None,
    timeout: int = 120,
    keep_alive: str = "30m",
) -> str:
    default_model, base_url = _config_defaults()
    model = model or default_model
    payload_messages = [dict(m) for m in messages]
    if images:
        for m in reversed(payload_messages):
            if m.get("role") == "user":
                m["images"] = list(images)
                break
    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={"model": model, "messages": payload_messages, "stream": False, "keep_alive": keep_alive},
            timeout=timeout,
        )
    except Exception as e:
        raise RuntimeError(f"ollama chat unreachable: {e}") from e
    if resp.status_code != 200:
        raise RuntimeError(f"ollama chat failed {resp.status_code}: {resp.text[:200]}")
    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"ollama chat bad json: {e}") from e
    content = ((data.get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("ollama chat empty reply")
    return content
