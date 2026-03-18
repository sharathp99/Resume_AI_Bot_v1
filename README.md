# Resume Intelligence Platform

A production-style internal recruiting intelligence application for ingesting resumes, extracting structured candidate data, indexing evidence-backed search content, and supporting recruiter workflows through a FastAPI backend and Streamlit UI.

## Proposed Project Structure

```text
app/
  api/                  # FastAPI routes and request dependencies
  core/                 # settings, logging, exceptions, security helpers
  db/                   # SQLAlchemy models, repositories, session, migrations
  integrations/         # OpenAI provider and Qdrant vector index adapters
  schemas/              # Pydantic request/response/domain schemas
  services/             # ingestion, parsing, extraction, JD parsing, search, ranking, chat, export
  ui/                   # Streamlit recruiter-facing application
  tests/                # unit, integration, and end-to-end tests
alembic/                # Alembic migration environment
scripts/                # reindexing and sample-data generation utilities
data/                   # local resumes, recruiter notes, exports
```

## Architecture Summary

### Retrieval-first design
- Resume ingestion extracts raw text from PDF and DOCX files.
- A hybrid extraction pipeline combines deterministic parsing with optional OpenAI structured extraction.
- Structured candidate records are stored in SQLite through SQLAlchemy.
- Chunked resume content is embedded and written to Qdrant for evidence-backed retrieval.
- Search combines role-bucket filtering, vector similarity, and transparent weighted ranking.
- The recruiter copilot only answers by invoking explicit tools over indexed data.

### Enterprise-oriented layering
- **API layer**: FastAPI routes define clean service contracts and OpenAPI documentation.
- **Service layer**: business logic for ingestion, search, ranking, chat, and export lives outside the UI.
- **Repository layer**: database operations are isolated for maintainability and testing.
- **Integration layer**: OpenAI and Qdrant are wrapped behind replaceable adapters.
- **UI layer**: Streamlit is a thin client over backend APIs so the frontend can later be replaced.

### Phased implementation plan
1. **Foundation**: config, logging, DB schema, repositories, parser/extractor scaffolding.
2. **Ingestion/search core**: resume indexing, JD parsing, vector retrieval, ranking.
3. **Recruiter workflows**: candidate detail, notes/status, comparison, export.
4. **Copilot**: grounded tool-driven chat over indexed data.
5. **Operationalization**: tests, Docker, sample data tooling, README, migrations.

## Key Features

- Resume ingestion from role-based local folders.
- PDF and DOCX parsing with graceful failure handling.
- Deterministic extraction for email, phone, LinkedIn, and GitHub.
- Optional OpenAI-based structured extraction and JD parsing.
- Normalized candidate schema with notes, status history, and resume documents.
- Evidence-backed candidate search and weighted ranking.
- Candidate comparison, shortlist export, and recruiter copilot chat.
- Structured JSON logging and query audit capture.
- Qdrant integration with an in-memory fallback for local development and tests.

## Privacy and Security Notes

- Resume files remain local except when OpenAI extraction/embedding is enabled.
- API keys are environment-driven; never hardcode secrets.
- Logs are structured and designed to support masking of sensitive values.
- Streamlit users are shielded from raw backend stack traces through API error handling.
- The OpenAI integration is wrapped behind a provider abstraction so a local model can replace it later.

## Setup

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2. Configure environment

```bash
cp .env.example .env
```

Update `.env` as needed:
- `DATABASE_URL`
- `QDRANT_URL`
- `OPENAI_API_KEY`
- `ENABLE_OPENAI_EXTRACTION`
- `ENABLE_QDRANT`

### 3. Generate sample data (optional)

```bash
python scripts/seed_sample_data.py
```

### 4. Run the API

```bash
make run-api
```

### 5. Run the Streamlit UI

```bash
make run-ui
```

### 6. Run with Docker Compose

```bash
docker compose up --build
```

## Common Commands

```bash
make install
make run-api
make run-ui
make test
make lint
python scripts/reindex.py --role data_engineer --reindex
```

## Re-indexing resumes

1. Place resumes under `data/resumes/<role_bucket>/`.
2. Use the Streamlit ingestion tab or call the API endpoint:

```bash
curl -X POST http://localhost:8000/api/ingestion/resumes \
  -H 'Content-Type: application/json' \
  -d '{"role_bucket":"data_engineer","reindex":true}'
```

## API Overview

- `GET /health`
- `POST /api/ingestion/resumes`
- `GET /api/candidates/`
- `GET /api/candidates/{candidate_id}`
- `POST /api/search/jd`
- `POST /api/search/skills`
- `POST /api/search/compare`
- `POST /api/notes/`
- `GET /api/notes/{candidate_id}`
- `POST /api/notes/status`
- `POST /api/exports/shortlist`
- `POST /api/chat/`

## Testing

Run the full test suite:

```bash
make test
```

Coverage focus includes:
- PDF and DOCX parsing
- deterministic extraction
- JD parsing
- ranking behavior
- ingestion + search integration
- notes/status + export flow
- recruiter copilot detail lookup

## Known Limitations

- The MVP uses SQLite; PostgreSQL migration is straightforward but not included.
- The included Alembic migration bootstraps the core candidate/contact schema only.
- Chat orchestration intentionally supports a focused set of recruiter queries, not free-form general chat.
- OpenAI response formatting can vary, so the pipeline falls back to heuristic extraction when needed.
- Qdrant is expected for production; the in-memory vector index exists to keep development and tests reliable.

## Suggested Next Steps for Enterprise Hardening

- Add authentication and role-based access control.
- Expand Alembic migrations to cover all tables with managed revisions.
- Add sparse retrieval and hybrid BM25 + dense reranking.
- Introduce PostgreSQL, background job workers, and object storage.
- Add duplicate candidate detection and recruiter feedback loops for ranking corrections.
- Add a richer chat planner with explicit intent classification and session memory.
