import importlib
import sys

import pytest


class FakeEmbedder:
    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[0.01 * (i + 1) for i in range(8)] for _ in texts]


class FakeChroma:
    def __init__(self):
        self._rows = []

    def add_chunk(self, chunk_id, text, embedding, metadata):
        self._rows.append(
            {
                "id": str(chunk_id),
                "text": text,
                "embedding": embedding,
                "metadata": metadata,
            }
        )

    def query(self, query_embedding, top_k=10):
        rows = self._rows[:top_k]
        return [
            {
                "id": row["id"],
                "text": row["text"],
                "metadata": row["metadata"],
                "distance": 0.1,
            }
            for row in rows
        ]


class FakeOllama:
    def generate(self, _prompt):
        return {
            "outline": ["Summary"],
            "report": "Generated from indexed context.",
            "todos": [],
            "events": [],
            "metadata": {},
        }


@pytest.fixture
def app_module(monkeypatch, tmp_path):
    db_path = tmp_path / "integration.db"

    monkeypatch.setenv("SKIP_APP_BOOTSTRAP", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    if "api.app" in sys.modules:
        del sys.modules["api.app"]

    module = importlib.import_module("api.app")
    module.init_db()

    module.embedder = FakeEmbedder()
    module.chroma = FakeChroma()
    module.ollama = FakeOllama()

    # Keep /health deterministic in this test suite.
    monkeypatch.setattr(module, "check_ollama", lambda timeout=2: True)
    monkeypatch.setattr(module, "check_chroma", lambda timeout=2: True)

    return module


@pytest.fixture
def client(app_module):
    return app_module.app.test_client()


def test_health_reports_ok_when_dependencies_available(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert body["chroma"] is True
    assert body["ollama"] is True


def test_ingest_document_then_query_returns_thread_result(client):
    ingest_resp = client.post(
        "/ingest/document",
        json={
            "title": "Onboarding Notes",
            "content": "We decided to stage onboarding over two weeks and pair new hires.",
            "purpose": "meeting_notes",
        },
    )

    assert ingest_resp.status_code == 200
    ingest_body = ingest_resp.get_json()
    assert ingest_body["document_id"] > 0
    assert ingest_body["chunks_ingested"] >= 1

    query_resp = client.post(
        "/query",
        json={
            "query": "What did we decide about onboarding?",
        },
    )

    assert query_resp.status_code == 200
    query_body = query_resp.get_json()

    assert query_body["thread_id"] > 0
    assert "result" in query_body
    assert query_body["result"]["report"] == "Generated from indexed context."
    assert "confidence" in query_body["result"]["metadata"]


def test_ingest_meeting_creates_meeting_and_supports_thread_reuse(client):
    meeting_resp = client.post(
        "/ingest/meeting",
        json={
            "title": "Weekly Standup",
            "meeting_time": "2026-03-28T14:30:00Z",
            "participants": ["a@example.com", "b@example.com"],
            "content": "Owners agreed to close migration tasks by Friday.",
        },
    )

    assert meeting_resp.status_code == 200
    meeting_body = meeting_resp.get_json()
    assert meeting_body["meeting_id"] > 0

    first_query = client.post("/query", json={"query": "What is the migration deadline?"}).get_json()
    thread_id = first_query["thread_id"]

    second_query_resp = client.post(
        "/query",
        json={
            "thread_id": thread_id,
            "query": "Who owns the migration tasks?",
        },
    )

    assert second_query_resp.status_code == 200
    second_query_body = second_query_resp.get_json()
    assert second_query_body["thread_id"] == thread_id

    thread_resp = client.get(f"/threads/{thread_id}")
    assert thread_resp.status_code == 200
    thread_body = thread_resp.get_json()
    assert len(thread_body["messages"]) >= 4
