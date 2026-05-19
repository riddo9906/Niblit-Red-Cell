# META-UTILITY HUB

Lightweight production-ready FastAPI micro-SaaS that transforms raw user input into structured professional outputs.

## Features

- Modular AI pipeline (`input_normalizer`, `prompt_engine`, `ai_orchestrator`, `output_formatter`, `export_engine`, `template_library`)
- Endpoints for resume, cover letter, meeting notes, business idea, and ad copy generation
- Structured JSON output with Markdown/PDF export and downloadable result endpoint
- API key authentication, rate limiting, tiered usage limits (`free`, `pro`, `enterprise`)
- Usage tracking endpoint and billing-ready tier stubs
- Input sanitization and basic prompt injection filtering
- Request observability logs (request type, token estimate, latency)

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

App runs at `http://127.0.0.1:8000`.

## API

### Register API key

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"tier":"free"}'
```

### Health

```bash
curl http://127.0.0.1:8000/health
```

### Generate resume

```bash
curl -X POST http://127.0.0.1:8000/generate/resume \
  -H "X-API-Key: <YOUR_KEY>" \
  -H 'Content-Type: application/json' \
  -d '{"raw_experience_text":"Built APIs, reduced latency by 40%", "export_pdf": true}'
```

The response includes downloadable export links:

- `/results/{result_id}/download?format=json`
- `/results/{result_id}/download?format=markdown`
- `/results/{result_id}/download?format=pdf` (if requested)

### Other generation endpoints

- `POST /generate/cover-letter`
- `POST /generate/meeting-summary`
- `POST /generate/business-idea`
- `POST /generate/ad-copy`
- `GET /usage`

## Local AI behavior

- Uses OpenAI adapter if SDK/API key is available.
- Falls back automatically to deterministic local adapter for offline operation.
