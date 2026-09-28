"""Trading-chart tool: screenshot + vision ask with disclaimer."""
from __future__ import annotations

TOOL = {
    "name": "trading_chart",
    "description": "Describe the chart on screen (not financial advice).",
    "parameters": {
        "type": "object",
        "properties": {
            "region": {"type": "boolean"},
            "question": {"type": "string"},
        },
        "required": [],
    },
}

DISCLAIMER = ("This is an automated chart description for education only, "
              "not financial advice.")


async def run(args: dict, ctx: dict) -> str:
    region = bool(args.get("region", False))
    question = str(args.get("question", "Describe this trading chart."))
    try:
        from vision.shot import grab
    except ImportError as exc:
        return f"error: vision.shot unavailable ({exc})"
    try:
        from vision.ask import ask_about_screen
    except ImportError as exc:
        return f"error: vision.ask unavailable ({exc})"
    try:
        shot = await grab(region=region) if callable(grab) else grab(region)
        answer = await ask_about_screen(shot, question)
        return f"{answer}\n\n{DISCLAIMER}"[:2000]
    except Exception as exc:
        return f"error: {exc}"
