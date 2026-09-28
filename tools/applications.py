"""Applications tool: allowlisted launch + .desktop listing."""
from __future__ import annotations

import glob
import os
import shutil
import subprocess

TOOL = {
    "name": "applications",
    "description": "Launch allowlisted apps or list installed names.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["launch", "list"]},
            "app": {"type": "string"},
        },
        "required": ["action"],
    },
}

BUILTIN_APPS = ["code", "firefox", "thunar"]


async def run(args: dict, ctx: dict) -> str:
    action = args.get("action")
    cfg = (ctx or {}).get("config", {}) or {}
    allowed = list(((cfg.get("tools") or {}).get("allowed_apps")) or [])
    allowed = allowed + [a for a in BUILTIN_APPS if a not in allowed]
    if action == "list":
        names: list[str] = []
        for f in glob.glob("/usr/share/applications/*.desktop"):
            names.append(os.path.splitext(os.path.basename(f))[0])
        return ("\n".join(sorted(names)) or "(none)")[:2000]
    if action == "launch":
        app = str(args.get("app", "")).strip()
        if not app:
            return "refused: empty app"
        if app not in allowed:
            return f"refused: '{app}' not in allowed_apps"
        try:
            if shutil.which("gtk-launch"):
                subprocess.Popen(
                    ["gtk-launch", app],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            else:
                subprocess.Popen(
                    ["nohup", "xdg-open", app],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            return f"launched {app}"[:2000]
        except Exception as exc:
            return f"error: {exc}"
    return "refused: unknown action"
