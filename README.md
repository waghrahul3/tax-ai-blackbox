# Tax AI Agent

AI-assisted FastAPI service for processing tax documents with prompt-driven workflows, rich output management, and a chatbot-style frontend UI.

## Features

- **FastAPI backend with Swagger UI** – `/docs` documents all endpoints with clear descriptions, required prompt input, optional template selection, CTID passthrough, expected file types, and download link behavior (markdown/CSV/zip/ZIP).
- **AI document pipeline** – configurable prompt templates (e.g., T-slip verification, Ontario medical expense reconciliation) or ad-hoc prompt-only executions.
- **Flexible file uploads** – accepts PDFs, images, and CSVs via multipart form data; supports multi-file ingestion.
- **Rich output handling** – auto-detects format, sanitizes CSV blocks, splits markdown + CSV combinations into dedicated files, and packages each run folder into a ZIP archive.
- **Secure download endpoint** – `/ai/download` serves results from the `output/` directory with path validation.
- **Chatbot-inspired frontend** – `/ui` provides template selection, multi-file uploads, status messaging, rendered markdown previews, and download links.

## Requirements

- Python 3.11+
- Virtual environment recommended (repo ships with `venv/` example)
- Dependencies listed in `requirements.txt` (FastAPI, Uvicorn, Anthropics SDK, LangChain, etc.)
- Anthropic API key available in environment for LLM access (`ANTHROPIC_API_KEY`)

## Local Setup

```bash
# 1. Create and activate virtualenv (or reuse repo's venv)
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env example and edit values
cp .env.example .env
# set ANTHROPIC_API_KEY, LOG_LEVEL, DEBUG_LOG_DIR, etc.

# 4. Run the FastAPI server
venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

- Swagger UI: `http://127.0.0.1:8000/docs`
- Chat UI: `http://127.0.0.1:8000/ui`
- Health check: `GET /`

## API Overview

### `POST /ai/process`
- **Purpose:** Process uploaded documents with a required `prompt`; optionally pass `template_name` and `ctid` (correlation tracking ID).
- **Request:**
  - `files`: one or more PDF/JPG/PNG/CSV uploads (required)
  - `prompt`: string instructions for the LLM (required)
  - `template_name`: optional template key (`t_slip_data_extraction`, `medical_tax_credit`, etc.)
  - `ctid`: optional correlation ID echoed in logs and response
- **Response:** JSON describing output format and download URLs for primary file, markdown split, CSV split, and ZIP archive plus the echoed `ctid`. Links are relative (`/ai/download?...`) so they respect the originating host/proxy scheme.

### `GET /ai/templates`
Lists available prompt templates (name, label, description, per-step metadata).

### `GET /ai/download`
Serves generated files from the `output/` directory. Validates paths to prevent traversal outside the output root.

### `GET /ui`
Returns the static chatbot frontend page.

## Frontend Chatbot (`/ui`)

- Fetches `/ai/templates` on load and provides a "No template (Prompt only)" option by default.
- Multi-file input with preview of selected filenames.
- Status banner + chat transcript showing user inputs and system responses.
- Download links appear after processing for markdown, CSV, or the general ZIP bundle.
- Markdown viewer modal fetches and renders markdown reports directly in-app.

## Output Structure

Generated artifacts live under `output/run_<timestamp>_<id>/` with:
- `summary_report.md` (when markdown format)
- `summary_report.csv` (split from markdown or native CSV output)
- Optional template-specific filenames if configured
- `output/run_<timestamp>_<id>.zip` containing the entire run folder for convenience

Logs and `output/` are git-ignored by default via `.gitignore`.

## Deployment Notes

- The sample `systemd` unit in `/Untitled-1` demonstrates running via Gunicorn with Uvicorn workers bound to `127.0.0.1:9000` behind Nginx (or another reverse proxy).
- Ensure proxy forwards `Host` and `X-Forwarded-Proto` headers if you later switch back to absolute URLs. Currently the API returns relative download URLs to avoid scheme mismatches.

## Troubleshooting

- **No markdown file produced** – occurs if the LLM response is pure CSV. Ensure your prompt instructs the model to include narrative/markdown sections; detection logic now preserves markdown when additional text surrounds fenced CSV blocks.
- **Swagger file field missing** – verify you’re running the patched FastAPI app (`main.py` overrides OpenAPI to mark file arrays as binary).
- **Anthropic authentication errors** – confirm `ANTHROPIC_API_KEY` is exported in the environment where Uvicorn/Gunicorn is launched.
- **Download link 404** – the `/ai/download` endpoint only allows files inside the `output/` folder; verify the run hasn’t been manually deleted.
- **Structured logs not appearing** – set `LOG_LEVEL=DEBUG` and `DEBUG_LOG_DIR=logs` (or similar) to emit JSON logs via structlog. Files rotate automatically with date-stamped filenames (`app-debug-YYYYMMDD.log`) controlled by `LOG_FILE_MAX_BYTES` and `LOG_FILE_BACKUP_COUNT`.

## License

Internal project. Add licensing details here if distributing more broadly.
