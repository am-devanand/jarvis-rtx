"""Ask about the screen via Qwen3-VL. Lazy models import, stdlib-only."""
from __future__ import annotations

import base64
from typing import Any, Dict, Optional

CHART_SUFFIX = (
    " Interpret structure (trend, S/R, liquidity, patterns, indicators)."
    " Educational chart reading, never a guaranteed prediction."
)


def ask_about_screen(
    question: str, cfg: Dict[str, Any], region: bool = False, model: Optional[str] = None,
    timeout: int = 600,
) -> str:
    """Grab screen, send to Qwen3-VL, return answer string."""
    try:
        from vision.shot import grab
    except ImportError:
        from .shot import grab  # type: ignore[no-redef]

    png = grab(region=region)
    b64 = base64.b64encode(png).decode("ascii")

    vision_cfg = (cfg.get("vision") if isinstance(cfg, dict) else {}) or {}
    resolved = model or vision_cfg.get("model", "qwen3-vl:4b")

    try:
        from models.qwen import chat
    except ImportError as e:
        raise RuntimeError(
            "vision needs models.qwen.chat (sibling module) + Ollama at"
            " http://localhost:11434 with qwen3-vl:4b"
        ) from e

    messages = [{"role": "user", "content": question + CHART_SUFFIX}]
    return str(chat(messages, model=resolved, images=[b64], timeout=timeout))
