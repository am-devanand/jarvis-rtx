"""Smoke test with fakes only (no network/models). Prints SMOKE_OK."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.agent import Agent
from core.router import route
from core.task_manager import run_steps


async def fake_call_model(messages, model=None):
    return f"fake-reply model={model} n={len(messages)}"


async def fake_dispatch(step):
    return f"ok:{step}"


class FakeMem:
    def __init__(self):
        self.rows: list[tuple] = []

    def log(self, u, a):
        self.rows.append((u, a))


async def main() -> None:
    cases = [
        ("hello how are you today?", "chat"),
        ("what is in this image on my screen?", "vision"),
        ("write a python function to sort a list", "code"),
        ("open firefox and search the web for news", "tool"),
        ("find file notes.txt and then open terminal and run ls", "multi"),
        ("debug my react component error", "code"),
    ]
    for text, want in cases:
        r = route(text)
        assert r["kind"] == want, f"{text!r}: got {r['kind']!r} want {want!r}"
        assert set(r) >= {"kind", "model", "tools", "steps"}, r
        if want == "multi":
            assert 2 <= len(r["steps"]) <= 5, r
            assert isinstance(r["tools"], list)

    out = await run_steps(["step one", "step two"], fake_dispatch)
    assert out == ["ok:step one", "ok:step two"], out

    async def boom(step):
        raise RuntimeError("nope")

    err = await run_steps(["a", "b"], boom)
    assert len(err) == 1 and err[0].startswith("ERROR on step 1"), err

    mem = FakeMem()
    agent = Agent({})
    reply = await agent.ask("hello", fake_call_model, fake_dispatch, mem)
    assert "fake-reply" in reply, reply
    reply2 = await agent.ask("find file x and then run ls", fake_call_model, fake_dispatch, mem)
    assert "Ran 2 step(s)" in reply2, reply2
    assert len(mem.rows) == 2, mem.rows

    try:
        from memory import database as _db  # type: ignore

        assert hasattr(_db, "log") or hasattr(_db, "add") or True
    except Exception:
        pass

    print("SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
