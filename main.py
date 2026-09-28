"""Jarvis CLI: chat loop, --ask, --shot, --voice. Lazy/guarded imports."""
from __future__ import annotations

import argparse
import asyncio
import inspect
from pathlib import Path

from core.agent import Agent


def load_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.yaml"
    try:
        import yaml  # type: ignore

        if cfg_path.exists():
            return dict(yaml.safe_load(cfg_path.read_text()) or {})
    except Exception:
        pass
    return {}


def build_wiring():
    from models.qwen import chat as real_chat

    async def call_model(messages, model=None):
        res = real_chat(messages, model=model) if model else real_chat(messages)
        if inspect.isawaitable(res):
            return await res
        return res

    try:
        from tools import REGISTRY as _REG  # type: ignore
    except Exception:
        _REG = None

    async def dispatch_tool(step):
        tool, _, arg = (step.partition(":") if isinstance(step, str) else ("", "", ""))
        tool, arg = tool.strip(), arg.strip()
        if _REG:
            try:
                if tool in _REG:
                    fn = _REG[tool]
                    r = fn(arg) if not inspect.iscoroutinefunction(fn) else await fn(arg)
                    return str(r)
            except Exception as e:
                raise RuntimeError(str(e)) from e
        if isinstance(step, str) and step.strip():
            if _REG is None:
                return f"[no-tools] {step}"
            raise RuntimeError(f"unknown tool '{tool}'")
        raise RuntimeError("empty step")

    try:
        from memory import database as _db  # type: ignore

        mem = _db
    except Exception:
        mem = None
    return call_model, dispatch_tool, mem


async def run_once(text: str) -> str:
    cfg = load_config()
    agent = Agent(cfg)
    call_model, dispatch_tool, mem = build_wiring()
    return await agent.ask(text, call_model, dispatch_tool, mem)


def main() -> None:
    ap = argparse.ArgumentParser(description="Jarvis local agent")
    ap.add_argument("--ask", default=None, help="one-shot question")
    ap.add_argument("--shot", default=None, help="vision question about screen")
    ap.add_argument("--voice", action="store_true", help="voice loop")
    args = ap.parse_args()

    if args.shot is not None:
        try:
            from vision import screen as _vscreen  # type: ignore
        except Exception as e:
            print(f"vision unavailable: {e}")
            raise SystemExit(2)
        print(asyncio.run(_vscreen.ask(args.shot)))
        return

    if args.voice:
        try:
            from voice import loop as _vloop  # type: ignore
        except Exception as e:
            print(f"voice unavailable: {e}")
            raise SystemExit(2)
        _vloop.run()
        return

    if args.ask is not None:
        print(asyncio.run(run_once(args.ask)))
        return

    print("jarvis> chat loop (Ctrl-D to exit)")
    while True:
        try:
            text = input("you> ").strip()
        except EOFError:
            break
        if not text:
            continue
        print("jarvis> " + asyncio.run(run_once(text)))


if __name__ == "__main__":
    main()
