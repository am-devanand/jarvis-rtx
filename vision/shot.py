"""Screenshot via grim/slurp on Hyprland. Pure subprocess, stdlib-only."""
from __future__ import annotations

import shutil
import subprocess


def grab(region: bool = False) -> bytes:
    """Capture screen and return raw PNG bytes.

    region False -> `grim -`; True -> `grim -g "$(slurp)" -`.
    """
    grim = shutil.which("grim")
    if not grim:
        raise RuntimeError("screenshot needs grim: sudo pacman -S grim (or apt install grim)")
    if not region:
        out = subprocess.run([grim, "-"], capture_output=True, timeout=30)
        if out.returncode != 0:
            raise RuntimeError(f"grim failed: {out.stderr.decode(errors='replace')}")
        return bytes(out.stdout)
    slurp = shutil.which("slurp")
    if not slurp:
        raise RuntimeError("region capture needs slurp: sudo pacman -S slurp")
    sel = subprocess.run([slurp], capture_output=True, text=True, timeout=60)
    if sel.returncode != 0 or not sel.stdout.strip():
        raise RuntimeError("slurp cancelled/failed: no region selected")
    geom = sel.stdout.strip()
    out = subprocess.run([grim, "-g", geom, "-"], capture_output=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"grim region failed: {out.stderr.decode(errors='replace')}")
    return bytes(out.stdout)


def save_shot(path: str, region: bool = False) -> str:
    """Capture screen and save PNG to path. Returns path."""
    data = grab(region=region)
    with open(path, "wb") as f:
        f.write(data)
    return path
