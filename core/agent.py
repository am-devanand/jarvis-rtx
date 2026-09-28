"""Agent: route -> tool/multi run or direct chat. Callables injected."""
from __future__ import annotations

import inspect

from .context import ConversationContext
from .router import route
from .task_manager import run_steps


async def _maybe_await(fn, *args, **kwargs):
    res = fn(*args, **kwargs)
    if inspect.isawaitable(res):
        return await res
    return res


class Agent:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.ctx = ConversationContext()

    async def ask(self, text: str, call_model, dispatch_tool, mem) -> str:
        r = route(text)
        kind = r.get("kind", "chat")

        if kind in ("tool", "multi"):
            steps = r.get("steps") or [text]
            results = await run_steps(steps, dispatch_tool)
            reply = f"Ran {len(results)} step(s): " + " | ".join(results)
            self.ctx.add("user", text)
            self.ctx.add("assistant", reply)
            self._mem_log(mem, text, reply)
            return reply

        model = r.get("model")
        messages = [{"role": "system", "content": "You are Jarvis, a concise local assistant."}]
        messages += self.ctx.history()
        messages.append({"role": "user", "content": text})
        try:
            reply = await _maybe_await(call_model, messages, model=model)
        except TypeError:
            reply = await _maybe_await(call_model, messages)
        reply = str(reply)
        self.ctx.add("user", text)
        self.ctx.add("assistant", reply)
        self._mem_log(mem, text, reply)
        return reply

    @staticmethod
    def _mem_log(mem, user: str, assistant: str) -> None:
        if mem is None:
            return
        try:
            if hasattr(mem, "log"):
                mem.log(user, assistant)
            elif hasattr(mem, "add"):
                mem.add(user, assistant)
            elif callable(mem):
                mem(user, assistant)
        except Exception:
            pass
