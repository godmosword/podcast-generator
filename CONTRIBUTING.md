# Contributing

## Checks

Run Python syntax and unit tests:

```bash
python3 -m compileall backend core pipeline providers utils main.py config.py
python3 -m unittest
```

Run frontend build:

```bash
cd frontend
npm run build
```

## Development Notes

- Keep CLI and API generation behavior shared through `pipeline/podcast_pipeline.py`.
- Add provider-specific logic behind `providers/base.py`.
- Keep frontend API calls in `frontend/src/api.ts`.
- Do not commit real API keys. Use `.env.example` as the template.
