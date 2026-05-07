# Cognitive Streaming

A local AI runtime where intelligence is modular — specialists are activated
on demand, memory is progressive, and models are loaded dynamically.

Inspired by TerraVision's tile-based streaming architecture from the 1990s.

## The Idea

Instead of loading all intelligence at once, Cognitive Streaming loads specialists
on demand, increases depth only when necessary, and activates modules dynamically.
The right intelligence, at the right time, with the minimum resources necessary.

## Tile Manifest Schema

A tile is the atomic unit of specialization. Each tile defines:
- Base model + quantization + system prompt
- Routing utterances + similarity threshold
- Cache TTL + similarity threshold (per-tile)
- Scheduler: keep-warm duration + prewarm triggers

See `tiles/` for examples.

## Quick Start

1) Create and activate a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

2) Install Python deps:

    pip install fastapi uvicorn httpx semantic-router sentence-transformers structlog pyyaml numpy pydantic-settings pytest

3) Ensure Ollama is reachable locally:

    curl -sS http://127.0.0.1:11434/api/tags

If this returns JSON, Ollama is reachable.

4) Pull required models:

    ollama pull smollm2:135m
    ollama pull qwen3:4b
    ollama pull qwen2.5-coder:3b

5) Set runtime URL (recommended explicit setting):

    cp .env.example .env
    source .env

Or set only what you need manually:

    export OLLAMA_BASE_URL="http://127.0.0.1:11434"

6) Run API:

    python3 main.py

7) Validate endpoints:

    curl -sS http://127.0.0.1:8000/health
    curl -sS -X POST http://127.0.0.1:8000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"user","content":"what is 2+2?"}],"stream":false}'

Endpoints:
- GET  /health  — status + loaded tiles
- GET  /tiles   — tile list with warm state
- POST /v1/chat/completions — OpenAI-compatible

## Configuration

Runtime config is centralized in `config.py` and can be overridden with env vars:

- `OLLAMA_BASE_URL` (preferred), e.g. `http://127.0.0.1:11434`
- `OLLAMA_HOST`, `OLLAMA_PORT` (used if `OLLAMA_BASE_URL` is not set)
- `HTTP_TIMEOUT_SECONDS`
- `PREWARM_HTTP_TIMEOUT_SECONDS`
- `DEFAULT_TILE_NAME`
- `DEFAULT_TILE_TTL_SECONDS`
- `DEFAULT_CACHE_SIMILARITY_THRESHOLD`
- `EMBEDDING_MODEL_NAME`
- `HISTORY_SIZE`
- `APP_HOST`
- `APP_PORT`

Note: If `OLLAMA_HOST` includes `http://...`, the app normalizes it correctly.

## Troubleshooting

- `httpx.ConnectError: All connection attempts failed`
  - Ollama is not reachable at configured URL.
  - Verify with `curl -sS http://127.0.0.1:11434/api/tags`.

- `{"models":[]}` from `/api/tags`
  - Ollama is running but no models are installed yet.
  - Run `ollama pull qwen3:4b` and `ollama pull qwen2.5-coder:3b`.

- `ollama serve` fails with `bind: can't assign requested address`
  - Your shell has a bad `OLLAMA_HOST`.
  - Run `unset OLLAMA_HOST` and use `OLLAMA_BASE_URL` explicitly.

- `zsh: command not found: python`
  - Use `python3` or activate `.venv` first.

## Architecture

    REQUEST → Router (<15ms) → Cache lookup → Tile Scheduler
                                                   ↓
                                         Composite Streaming
                                         (preamble if cold)
                                                   ↓
                                         Specialist Model
                                                   ↓
                                         RESPONSE (streaming)

## License
MIT — see LICENSE
