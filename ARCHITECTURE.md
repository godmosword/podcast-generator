# Wavescript Architecture

## Product Shape

Wavescript is currently optimized for script-to-podcast generation, not full recording and timeline editing. The MVP supports 1-4 speakers, role-to-voice mapping, preview, SSE progress, and file download.

## Data Flow

1. Frontend Studio collects script, host count, voice assignments, and audio settings.
2. `POST /api/generate` creates an in-memory job.
3. Frontend opens `GET /api/generate/{id}/events` with EventSource.
4. Backend parses speaker turns, maps roles to voices, synthesizes TTS chunks, merges audio, applies normalization/limiting/BGM, and exports the final file.
5. Frontend receives a `done` event and downloads from `GET /api/files/{id}`.

## Backend Modules

- `backend/routers/generate.py`: job creation, job snapshots, SSE event stream.
- `backend/routers/preview.py`: single voice preview.
- `backend/routers/files.py`: output download.
- `core/script_parser.py`: script turns and speaker metadata.
- `core/role_mapper.py`: speaker-to-voice mapping.
- `pipeline/podcast_pipeline.py`: shared CLI/API generation pipeline.

## Limits

- 1-4 speakers per episode.
- Mixed TTS providers in the same generation job are rejected for now.
- Jobs are stored in memory, so restarting the backend clears job status.
- Local non-Docker export requires ffmpeg installed on the host.
