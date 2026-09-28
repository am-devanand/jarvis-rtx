"""STT: transcribe(wav_path, cfg) -> str. No imports of heavy deps at top."""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict


def _resolve_device(device_cfg: str) -> str:
    if device_cfg != "auto":
        return device_cfg
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def transcribe(wav_path: str, cfg: Dict[str, Any]) -> str:
    """Transcribe wav via faster-whisper, else whisper.cpp CLI fallback."""
    stt = (cfg.get("stt") if isinstance(cfg, dict) else {}) or {}
    model_name = stt.get("model", "base.en")
    device = _resolve_device(stt.get("device", "auto"))

    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(model_name, device=device, compute_type="int8")
        segments, _info = model.transcribe(wav_path)
        return "".join(seg.text for seg in segments).strip()
    except ImportError:
        pass

    binary = stt.get("binary", "")
    model_path = stt.get("model_path", "")
    if binary and shutil.which(binary) and os.access(binary, os.X_OK):
        cmd = [binary, "-m", str(model_path), "-f", wav_path]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"whisper.cpp binary timed out: {binary}") from e
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
        raise RuntimeError(f"whisper.cpp binary failed ({binary}): {out.stderr.strip()}")
    raise RuntimeError(
        "STT needs one of: pip install faster-whisper"
        " OR whisper.cpp CLI (set stt.binary to the executable"
        " and stt.model_path to the .bin model, e.g. binary=whisper-cpp)"
    )
