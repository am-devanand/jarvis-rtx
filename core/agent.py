"""Agent: route -> tool/multi run or direct chat. Callables injected."""
from __future__ import annotations

import inspect

from .context import ConversationContext
from .router import route


async def _maybe_await(fn, *args, **kwargs):
    res = fn(*args, **kwargs)
    if inspect.isawaitable(res):
        return await res
    return res


TOOL_DEFAULTS: dict[str, dict] = {
    "system": {"action": "stats"},
    "applications": {"action": "list"},
    "screenshot": {"region": False},
}

TOOL_NEEDS_DETAIL = {
    "terminal": 'say the command, e.g. "run ls in the terminal"',
    "filesystem": 'say e.g. "list files in Projects"',
    "browser": 'say e.g. "search the web for X"',
    "git": "name the repo, e.g. \"git status in ~/Projects/foo\"",
    "trading_chart": 'say e.g. "analyze this chart" with it on screen',
}


class Agent:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.ctx = ConversationContext()

    async def _run_tool(self, name: str, dispatch_tool) -> str:
        if name in TOOL_DEFAULTS:
            try:
                res = await _maybe_await(dispatch_tool, name, TOOL_DEFAULTS[name])
            except TypeError:
                res = await _maybe_await(dispatch_tool, name)
            except Exception as e:
                return f"ERROR ({name}): {e}"
            return f"{name}: {res}"
        hint = TOOL_NEEDS_DETAIL.get(name, "needs more detail")
        return f"{name}: {hint}"

    async def _run_step(self, step_text: str, call_model, dispatch_tool) -> str:
        r2 = route(step_text)
        if r2.get("kind") == "tool" and r2.get("tools"):
            outs = [await self._run_tool(t, dispatch_tool) for t in r2["tools"][:3]]
            return " | ".join(outs)
        model = r2.get("model")
        try:
            reply = await _maybe_await(
                call_model, [{"role": "user", "content": step_text}], model=model
            )
        except TypeError:
            reply = await _maybe_await(call_model, [{"role": "user", "content": step_text}])
        except Exception as e:
            return f"ERROR (chat): {e}"
        return str(reply)

    async def ask(self, text: str, call_model, dispatch_tool, mem) -> str:
        r = route(text)
        kind = r.get("kind", "chat")

        if kind == "multi":
            steps = r.get("steps") or [text]
            results = [await self._run_step(s, call_model, dispatch_tool) for s in steps[:5]]
            reply = f"Ran {len(results)} step(s): " + " | ".join(results)
            self.ctx.add("user", text)
            self.ctx.add("assistant", reply)
            self._mem_log(mem, text, reply)
            return reply

        if kind == "tool":
            tools = r.get("tools") or []
            if not tools:
                tools = []
            results = [await self._run_tool(t, dispatch_tool) for t in tools[:3]]
            if not results:
                results = [await self._run_step(text, call_model, dispatch_tool)]
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
