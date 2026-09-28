"""Screenshot tool: delegates to vision.shot.grab (lazy import)."""
from __future__ import annotations

import os

TOOL = {
    "name": "screenshot",
    "description": "Capture screen/region via vision.shot.grab.",
    "parameters": {
        "type": "object",
        "properties": {"region": {"type": "boolean"}},
        "required": [],
    },
}


async def run(args: dict, ctx: dict) -> str:
    region = bool(args.get("region", False))
    try:
        from vision.shot import grab
    except ImportError as exc:
        return f"error: vision.shot unavailable ({exc})"
    try:
        path = await grab(region=region) if callable(grab) else grab(region)
        path = str(path)
        size = os.path.getsize(path) if os.path.exists(path) else -1
        return f"{path} ({size} bytes)"[:2000]
    except Exception as exc:
        return f"error: {exc}"
