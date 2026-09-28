"""TTS: speak(text, cfg) -> str. Piper primary, aplay/paplay playback."""
from __future__ import annotations

import shutil
import subprocess
import wave
from typing import Any, Dict

OUT_PATH = "/tmp/jarvis-say.wav"


def _play(wav_path: str) -> None:
    player = shutil.which("aplay") or shutil.which("paplay")
    if not player:
        return
    subprocess.run([player, wav_path], timeout=120, check=False)


def speak(text: str, cfg: Dict[str, Any]) -> str:
    """Synthesize text with Piper and play it. Returns wav path or 'spoken'."""
    tts = (cfg.get("tts") if isinstance(cfg, dict) else {}) or {}
    voice_name = tts.get("voice", "en_US-lessac-medium")
    model_path = tts.get("model_path", "")
    _ = voice_name  # voice selects model file; path in tts.model_path

    try:
        from piper import PiperVoice
    except ImportError as e:
        raise RuntimeError(
            "TTS needs: pip install piper-tts"
            " ; download voice e.g.:"
            " python3 -m piper.download_voices en_US-lessac-medium"
        ) from e

    if not model_path:
        raise RuntimeError(
            "TTS needs tts.model_path set to the Piper .onnx voice file"
            " (e.g. ~/.local/share/piper/en_US-lessac-medium.onnx)"
        )

    voice = PiperVoice.load(str(model_path))
    sample_rate = int(getattr(getattr(voice, "config", None), "sample_rate", 22050))
    with wave.open(OUT_PATH, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        voice.synthesize(text, wf)
    _play(OUT_PATH)
    return OUT_PATH
