"""Browser tool: headless chromium via playwright (lazy import)."""
from __future__ import annotations

import urllib.parse
import urllib.request

TOOL = {
    "name": "browser",
    "description": "Open a page, DuckDuckGo search, or snapshot text.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["open", "search", "snapshot"]},
            "target": {"type": "string"},
        },
        "required": ["action", "target"],
    },
}


def _ddg_search(query: str) -> str:
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", "replace")
    import re

    links = re.findall(r'<a[^>]+class="result__a"[^>]*>(.*?)</a>', html, re.S)
    clean = [re.sub(r"<.*?>", "", a).strip() for a in links]
    return "\n".join(c for c in clean if c)[:2000] or "(no results)"


async def run(args: dict, ctx: dict) -> str:
    action = args.get("action")
    target = str(args.get("target", "")).strip()
    if not target:
        return "refused: empty target"
    if action == "search":
        try:
            return _ddg_search(target)[:2000]
        except Exception as exc:
            return f"error: {exc}"
    if action in ("open", "snapshot"):
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return "error: playwright not installed"
        url = target if "://" in target else "https://" + target
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=30000)
                text = await page.evaluate("() => document.body.innerText || ''")
                await browser.close()
            return (text.strip() or "(empty page)")[:2000]
        except Exception as exc:
            return f"error: {exc}"
    return "refused: unknown action"
