"""Ollama embeddings via /api/embeddings. Stdlib + requests only."""
from __future__ import annotations

from pathlib import Path

import requests


def _config() -> tuple[str | None, str]:
    model, url = None, "http://localhost:11434"
    try:
        cfg = Path(__file__).resolve().parent.parent / "config.yaml"
        if cfg.exists():
            try:
                import yaml  # type: ignore

                data = yaml.safe_load(cfg.read_text()) or {}
            except Exception:
                data = {}
            m = (data or {}).get("models", {}) or {}
            model = m.get("embed")
            url = str((data or {}).get("ollama_url", url))
    except Exception:
        pass
    return model, url


def embed(texts: list[str]) -> list[list[float]]:
    model, base_url = _config()
    if not model:
        raise RuntimeError("embed model missing in config (vectors disabled)")
    out: list[list[float]] = []
    for t in texts:
        try:
            resp = requests.post(
                f"{base_url.rstrip('/')}/api/embeddings",
                json={"model": model, "prompt": t},
                timeout=60,
            )
        except Exception as e:
            raise RuntimeError(f"ollama embeddings unreachable: {e}") from e
        if resp.status_code != 200:
            raise RuntimeError(f"ollama embeddings failed {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"ollama embeddings bad json: {e}") from e
        vec = data.get("embedding")
        if not isinstance(vec, list):
            raise RuntimeError("ollama embeddings empty vector")
        out.append([float(x) for x in vec])
    return out
