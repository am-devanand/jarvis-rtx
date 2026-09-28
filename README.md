# Jarvis RTX — local agent for RTX 3050 4GB laptop

Local-first voice + vision + tool agent. Ollama serves one model at a
time (VRAM safety). Defaults are 4B models; 8B chat (`qwen3:8b`) is
optional if VRAM allows.

## Setup (target machine: RTX 3050 4GB + 14GB RAM, Linux/Hyprland)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 1. Ollama + models

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:4b
ollama pull qwen3-vl:2b
ollama pull nomic-embed-text
# Optional (needs more VRAM, router still loads ONE model at a time):
# ollama pull qwen3:8b
# ollama pull qwen3-vl:4b  # sharper eyes for detailed chart reads
```

### 2. Voice (STT/TTS) — owned by voice sibling agent

```bash
pip install faster-whisper
# Piper TTS binary + voice, e.g.:
# https://github.com/rhasspy/piper/releases
```

### 3. Browser tool — owned by tools sibling agent

```bash
pip install playwright
playwright install chromium
```

### 4. Run

```bash
python main.py                  # chat loop (stdin/stdout)
python main.py --ask "status"   # one-shot
python main.py --shot "what is on screen?"      # vision (lazy import)
python main.py --voice          # voice loop (lazy import)
python3 tests/smoke.py          # fakes only, no network/models
```

## Layout

- `config.yaml` — shared contract (models/chat/vision/embed, ollama_url, memory.db)
- `core/` — router, agent, context, task_manager (this scaffold owns)
- `models/` — qwen chat + embeddings via Ollama (this scaffold owns)
- `main.py`, `tests/smoke.py` — (this scaffold owns)
- `tools/` — sibling: terminal/filesystem/browser/screenshot/applications/git/system/trading_chart
- `voice/` — sibling: STT (faster-whisper) / TTS (piper)
- `vision/` — sibling: screenshots + qwen3-vl:4b questions
- `memory/` — sibling: sqlite at `memory/jarvis.db` + vectors (nomic-embed-text)

`tools.*`, `stt.*`, `tts.*` settings are documented here in README only;
sibling agents own those fragments.
