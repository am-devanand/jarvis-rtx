"""System tool: stats/ps via /proc+df; killport needs confirm."""
from __future__ import annotations

import os
import signal
import subprocess

TOOL = {
    "name": "system",
    "description": "Host stats, process list, or kill by port (confirm).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["stats", "ps", "killport"]},
            "port": {"type": "integer"},
        },
        "required": ["action"],
    },
}


def _stats() -> str:
    parts: list[str] = []
    try:
        with open("/proc/loadavg") as fh:
            parts.append("load: " + fh.read().strip())
    except OSError as exc:
        parts.append(f"load: n/a ({exc})")
    try:
        mem: dict[str, str] = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                k, _, v = line.partition(":")
                if k.strip() in ("MemTotal", "MemAvailable"):
                    mem[k.strip()] = v.strip()
        parts.append("mem: " + ", ".join(f"{k}={v}" for k, v in mem.items()))
    except OSError as exc:
        parts.append(f"mem: n/a ({exc})")
    try:
        df = subprocess.run(["df", "-h", "/"], capture_output=True,
                            text=True, timeout=10)
        parts.append("disk:\n" + (df.stdout or "").strip())
    except Exception as exc:
        parts.append(f"disk: n/a ({exc})")
    return "\n".join(parts)


def _ps() -> str:
    rows: list[str] = []
    for pid in sorted(p for p in os.listdir("/proc") if p.isdigit()):
        try:
            with open(f"/proc/{pid}/comm") as fh:
                rows.append(f"{pid} {fh.read().strip()}")
        except OSError:
            continue
        if len(rows) >= 50:
            break
    return "\n".join(rows) or "(none)"


async def run(args: dict, ctx: dict) -> str:
    action = args.get("action")
    if action == "stats":
        return _stats()[:2000]
    if action == "ps":
        return _ps()[:2000]
    if action == "killport":
        confirm = (ctx or {}).get("confirm")
        if confirm is None:
            return "needs confirmation"
        try:
            ok = await confirm(f"Kill process on port {args.get('port')}?")
        except Exception:
            ok = False
        if not ok:
            return "needs confirmation"
        try:
            port = int(args.get("port", 0))
        except (TypeError, ValueError):
            return "refused: bad port"
        try:
            ss = subprocess.run(["ss", "-lptn", f"sport = :{port}"],
                                capture_output=True, text=True, timeout=10)
            import re

            pids = re.findall(r"pid=(\d+)", ss.stdout or "")
            if not pids:
                return f"no listener on port {port}"
            for pid in pids:
                os.kill(int(pid), signal.SIGTERM)
            return f"killed pid(s) {','.join(pids)} on port {port}"
        except Exception as exc:
            return f"error: {exc}"
    return "refused: unknown action"
