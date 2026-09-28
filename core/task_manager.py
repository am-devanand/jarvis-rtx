"""Sequential task runner. Dependency-free."""
from __future__ import annotations

import inspect


async def _maybe_await(fn, *args):
    res = fn(*args)
    if inspect.isawaitable(res):
        return await res
    return res


async def run_steps(steps, dispatch_tool, max_steps: int = 5) -> list[str]:
    """Run steps sequentially; stop with clear message on first tool error."""
    out: list[str] = []
    for i, step in enumerate(list(steps)[:max_steps]):
        try:
            res = await _maybe_await(dispatch_tool, step)
            out.append(str(res))
        except Exception as e:
            out.append(f"ERROR on step {i + 1} ({step!r}): {e}")
            break
    return out
