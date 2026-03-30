# Local RAG Backend for Meeting Intelligence

A local, privacy-preserving Retrieval-Augmented Generation backend designed to ingest notes and documents, store semantic memory, and answer questions with structured output.

Current stack: Python, Flask, SQLAlchemy, ChromaDB, Ollama, Docker Compose.

## Current State

Implemented now:
- Ingestion endpoints for meeting and document text
- Word-overlap chunking pipeline
- Embeddings to Chroma vector store
- Relational metadata persistence via SQLAlchemy models
- Query endpoint with retrieval + prompt build + LLM call
- Thread and message persistence in query flow
- Tasks/events endpoints scaffolded
- Health endpoint for DB + Chroma + Ollama readiness

Main API file: api/app.py

## API Surface

Ingestion:
- POST /ingest/meeting
- POST /ingest/document

Query and threads:
- POST /query
- GET /threads
- GET /threads/<id>
- POST /threads/<id>/message

Tasks/events:
- GET /tasks
- POST /tasks
- PATCH /tasks/<id>
- GET /events

Admin:
- GET /health

## Local Run

### Docker (full stack)
1. docker compose up --build
2. API: http://localhost:5000

### API only (dev)
1. pip install -r api/requirements.txt
2. set DATABASE_URL=sqlite:///./rag.db
3. set OLLAMA_HOST=http://localhost:11434
4. set CHROMA_HOST=localhost
5. set CHROMA_PORT=8000
6. python -m api.app

## Testing

### Unit and integration-style tests with fakes
- pytest tests -v

### Optional live Chroma integration check
This test validates heartbeat + add/query roundtrip against a running Chroma instance.

1. Start Chroma (docker compose or local)
2. Set environment:
   - RUN_CHROMA_INTEGRATION=1
   - CHROMA_HOST=localhost (or your host)
   - CHROMA_PORT=8000
3. Run:
   - pytest -m integration -v

Files:
- tests/test_api_integration.py
- tests/test_chroma_integration.py

## Streamlit Test UI

Yes, this project can support a testing UI right now.

Added test bench:
- ui/streamlit_app.py

What it does:
- Takes raw text input
- Sends it to POST /ingest/document (which chunks + embeds + stores in Chroma)
- Sends questions to POST /query
- Displays structured RAG response
- Allows optional thread reuse and health checks

Run it:
1. pip install -r ui/requirements.txt
2. streamlit run ui/streamlit_app.py

## Architecture Next Steps

Priority 1: Reliability and schema control
- Add Alembic migrations for repeatable schema evolution
- Add explicit request/response models (Pydantic) for all endpoints
- Remove import-time boot side effects by introducing an app factory pattern

Priority 2: RAG quality and behavior
- Add intent router (structured SQL vs semantic RAG)
- Add retrieval filters (date range, category, participants, purpose)
- Persist tasks/events extracted from model responses

Priority 3: Production hardening
- Add structured logging and request IDs
- Add authentication (API key/JWT)
- Add compose healthchecks and startup sequencing

Priority 4: Evaluation
- Add regression fixtures for known Q/A scenarios
- Add retrieval quality metrics and confidence tuning loop

## Known Gap List

- Alembic migration workflow not wired yet
- Intent router is not yet implemented
- Tasks/events are not yet auto-extracted and persisted from model output
- Authentication is not implemented
