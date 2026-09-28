"""Voice package: mic -> STT -> reply -> TTS -> speaker.

Heavy deps (sounddevice, faster-whisper, piper-tts) are imported lazily
INSIDE functions so `import voice.*` works without models/hardware.
"""
