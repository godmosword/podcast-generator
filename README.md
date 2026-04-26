# Wavescript

Wavescript is a Chinese-friendly AI podcast generator. It turns a marked-up script into a multi-host podcast episode with voice assignment, voice preview, SSE progress updates, audio post-processing, and downloadable MP3/WAV output.

The project currently includes a FastAPI backend, a React/Vite frontend prototype, and a shared Python audio pipeline that also supports the original CLI flow.

## Features

- 1-4 host podcast generation from text scripts
- Speaker tags such as `[主持人A]: dialogue`
- Automatic speaker detection and role-to-voice mapping
- Edge TTS by default, with optional OpenAI and ElevenLabs provider modules
- Voice preview endpoint for short audition clips
- Server-Sent Events generation progress
- MP3/WAV export
- ID3 metadata for MP3 output
- LUFS normalization with dBFS fallback
- Peak limiting, fades, and optional BGM mixing
- Built-in BGM catalog with preview, volume, and fade controls
- Docker Compose setup for frontend + backend

## Project Structure

```text
.
├── backend/              # FastAPI API server
├── assets/bgm/           # Built-in background music library
├── core/                 # Parser, role mapping, audio processing, exporter
├── frontend/             # React + Vite Studio UI
├── pipeline/             # Shared podcast generation orchestration
├── providers/            # TTS provider implementations
├── utils/                # File, text chunking, SSML helpers
├── docker-compose.yml
├── main.py               # Typer CLI entry point
├── requirements.txt
└── TODOS.md
```

## Requirements

- Python 3.12+ recommended
- Node.js 22+ recommended
- Docker, optional
- `ffmpeg` for local audio export

The backend Docker image installs `ffmpeg` automatically. If you run the backend directly on your machine, install `ffmpeg` separately.

## Environment

Create `.env` from `.env.example` or edit the provided local `.env`:

```env
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
BGM_PATH=
TTS_PROVIDER=edge
OUTPUT_DIR=output
VITE_API_BASE_URL=http://localhost:8000
```

Edge TTS is the default provider and does not require an API key.

## Run With Docker

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API health: `http://localhost:8000/api/health`

## Local Development

Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run the backend:

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Run the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## CLI Usage

Generate an MP3 from a script:

```bash
python3 main.py generate --script sample_multi.txt --output output/sample.mp3
```

List available Chinese Edge TTS voices:

```bash
python3 main.py voices
```

## Script Format

Use speaker tags for multi-host scripts:

```text
[主持人A]: 大家好，歡迎收聽 Wavescript。
[主持人B]: 今天我們來聊聊 AI 如何改變日常創作。
---PAUSE:0.5s---
[主持人A]: 我們會從文稿、聲線到輸出流程一路拆解。
```

Supported syntax:

- `[Speaker]: text`
- `[Speaker]：text`
- `---PAUSE:1.5s---`
- Plain text, treated as a single speaker when no speaker tags are present

## Built-In Background Music

Place MP3 or WAV files in `assets/bgm/`. Wavescript scans the folder and exposes tracks through `GET /api/bgm`.

You can optionally describe tracks in `assets/bgm/manifest.json`:

```json
[
  {
    "id": "warm-intro",
    "title": "Warm Intro",
    "mood": "warm",
    "filename": "warm-intro.mp3",
    "duration": 30
  }
]
```

If no audio files are present, the frontend shows an empty BGM state and generation runs without background music.

## API Overview

- `GET /api/health` checks backend status.
- `GET /api/voices` returns the configured voice catalog.
- `GET /api/bgm` returns the built-in background music catalog.
- `GET /api/bgm/{id}/preview` streams a short background music preview.
- `POST /api/preview` generates a short voice preview.
- `POST /api/generate` creates a generation job.
- `GET /api/generate/{id}` returns a job snapshot.
- `GET /api/generate/{id}/events` streams progress with SSE.
- `GET /api/files/{id}` downloads the generated audio file.

## Tests And Checks

Run Python syntax checks and unit tests:

```bash
python3 -m compileall backend core pipeline providers utils main.py config.py
python3 -m unittest
```

Run frontend build:

```bash
cd frontend
npm run build
```

Validate Docker Compose configuration:

```bash
docker compose config --quiet
```

## Current Limitations

- Jobs are stored in memory; restarting the backend clears job state.
- Mixed TTS providers in a single generation job are rejected for now.
- Project drafts, autosave, persistent history, and timeline editing are planned but not implemented yet.
- Local generation requires `ffmpeg` installed outside Docker.
- Background music is currently limited to the built-in `assets/bgm/` catalog; user uploads are not implemented yet.

## License

MIT. See [LICENSE](LICENSE).
