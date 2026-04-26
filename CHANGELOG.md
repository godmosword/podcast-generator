# Changelog

All notable changes to Wavescript will be documented in this file.

## [Unreleased]

### Added

- Added FastAPI backend scaffold under `backend/`.
- Added `POST /api/generate`, `GET /api/generate/{id}`, `GET /api/generate/{id}/events`, `POST /api/preview`, `GET /api/files/{id}`, `GET /api/voices`, and `GET /api/health`.
- Added in-memory generation jobs with SSE progress events.
- Added backend schemas for generation, preview, audio settings, voice assignments, and job snapshots.
- Added role mapping for 1-4 speakers with UI overrides.
- Added script parser metadata output with speaker count and ordered turns.
- Added MP3/WAV export selection.
- Added LUFS normalization support with dBFS fallback.
- Added peak limiting and BGM fade support.
- Added Dockerfiles for backend and frontend.
- Added root `docker-compose.yml`.
- Added safe default `.env` and expanded `.env.example`.
- Added README, architecture notes, and contributing instructions.
- Added parser and role mapper unit tests.
- Added built-in BGM catalog under `assets/bgm/`.
- Added `GET /api/bgm` and `GET /api/bgm/{id}/preview`.
- Added BGM selection, preview, volume, and fade controls to the frontend audio settings step.
- Added generation payload fields for `bgm_id`, `bgm_volume_db`, and `bgm_fade_ms`.
- Added tests for BGM catalog loading, unknown BGM validation, and mix volume behavior.
- Wired frontend generation to real backend API calls.
- Wired frontend voice preview to `POST /api/preview`.
- Wired frontend output progress to EventSource SSE.
- Created an upgraded Wavescript UI prototype under `frontend/`.
- Added a React + Vite + TypeScript frontend scaffold.
- Added a four-step Studio flow:
  - Script input and estimated duration
  - Host setup
  - Audio settings
  - Output progress and download state
- Added `HostCountPicker` with 1–4 host selection.
- Added per-host voice slot rows with:
  - Editable role name
  - Voice selection
  - Voice tone metadata
  - Simulated preview state
- Added script stats for Chinese character count, estimated minutes, and detected speaker count.
- Added audio controls for speed, pause length, BGM toggle, and MP3/WAV output format.
- Added simulated generation progress and a visual audio player strip.
- Added responsive layout for desktop and mobile.
- Added frontend `.gitignore` for `node_modules/`, `dist/`, and TypeScript build cache.

### Verified

- Frontend dependencies install successfully with `npm install`.
- Production build passes with `npm run build`.
- Vite dev server serves the prototype at `http://localhost:3000/`.
- Python modules compile successfully with `python3 -m compileall`.
- FastAPI app imports successfully.
- `GET /api/health` returns `{"status":"ok"}`.
- `GET /api/voices` returns the configured voice catalog.
- `python3 -m unittest` passes.

### Existing Backend Capabilities

- Typer CLI can generate a podcast MP3 from text or Markdown scripts.
- Existing parser supports:
  - `[Speaker]: text`
  - `---PAUSE:1.5s---`
  - Plain narrator text
- Existing providers include Edge TTS, OpenAI TTS, and ElevenLabs.
- Existing audio pipeline can merge generated chunks, normalize volume approximately, fade edges, mix BGM, export MP3, and write ID3 tags.

### Known Gaps

- Local audio export requires ffmpeg installed on the machine; Docker backend image installs ffmpeg.
- Frontend currently uses Edge voices for the MVP generation flow; mixed providers in one job are rejected.
- `utils/ssml_builder.py` exists but is not used by the current providers.
- Project drafts, autosave, job persistence, and version history are not implemented yet.
- No automated tests are present yet.

## Product Direction

Wavescript will prioritize becoming a Chinese-friendly AI podcast generator rather than a full recording and editing workstation. The near-term target is a reliable workflow from script to multi-host generated episode with preview, progress, post-processing, and downloadable output.
