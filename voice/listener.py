"""Mic capture: record() -> wav path in /tmp. Stdlib-only at import."""
from __future__ import annotations

import tempfile
import wave


def record(seconds: float = 5, rate: int = 16000) -> str:
    """Record from mic and return wav path in /tmp.

    Raises RuntimeError with install hint when audio deps are missing.
    """
    try:
        import sounddevice as sd
    except ImportError as e:
        raise RuntimeError(
            "mic needs: pip install sounddevice (+ portaudio)"
        ) from e

    try:
        import numpy  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "mic needs: pip install sounddevice (requires numpy)"
        ) from e

    frames = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="int16")
    sd.wait()

    fd, path = tempfile.mkstemp(prefix="jarvis-mic-", suffix=".wav", dir="/tmp")
    import os

    os.close(fd)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(frames.tobytes())
    return path
