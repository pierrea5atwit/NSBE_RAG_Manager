"""Main API entrypoint for RAG querying and ingestion."""

from datetime import date, datetime
import json
import os

from flask import Flask, jsonify, request
from sqlalchemy import text

try:
    from .chunking import chunk_text
    from .db import (
        Chunk,
        Document,
        Event,
        Meeting,
        Message,
        SessionLocal,
        Task,
        Thread,
        engine,
        init_db,
    )
    from .llm.prompts import build_prompt
    from .startup_check import check_chroma, check_ollama, run_startup_checks
    from .warmup import warmup_models
    from .vectorstore.chroma_client import ChromaStore
except ImportError:
    from chunking import chunk_text
    from db import (
        Chunk,
        Document,
        Event,
        Meeting,
        Message,
        SessionLocal,
        Task,
        Thread,
        engine,
        init_db,
    )
    from llm.prompts import build_prompt
    from startup_check import check_chroma, check_ollama, run_startup_checks
    from warmup import warmup_models
    from vectorstore.chroma_client import ChromaStore


embedder = None
ollama = None
chroma = None


def bootstrap_runtime() -> None:
    """Initialize external dependencies when running the actual service."""
    global embedder, ollama, chroma
    run_startup_checks()
    init_db()
    embedder, ollama = warmup_models()
    chroma = ChromaStore()


if os.getenv("SKIP_APP_BOOTSTRAP", "0") != "1":
    bootstrap_runtime()

app = Flask(__name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def _parse_datetime(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _default_thread_title(query_text: str) -> str:
    trimmed = query_text.strip()
    if not trimmed:
        return "New Thread"
    return trimmed[:60]


def _serialize_chunks_for_prompt(retrieved: list[dict]) -> list[dict]:
    return [
        {
            "id": r["id"],
            "meeting_id": r.get("metadata", {}).get("meeting_id"),
            "text": r["text"],
        }
        for r in retrieved
    ]


def _add_chunks_to_vector_store(chunks: list[Chunk], meeting_id: int | None, document_id: int) -> None:
    chunk_texts = [c.chunk_text for c in chunks]
    embeddings = embedder.embed(chunk_texts)

    for c, emb in zip(chunks, embeddings):
        chroma.add_chunk(
            chunk_id=str(c.id),
            text=c.chunk_text,
            embedding=emb,
            metadata={
                "meeting_id": meeting_id,
                "document_id": document_id,
                "position": c.position,
            },
        )


@app.get("/health")
def health():
    db_ok = False
    chroma_ok = check_chroma(timeout=2)
    ollama_ok = check_ollama(timeout=2)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    overall = db_ok and chroma_ok and ollama_ok
    status = 200 if overall else 503
    return jsonify({"status": "ok" if overall else "degraded", "db": db_ok, "chroma": chroma_ok, "ollama": ollama_ok}), status


@app.post("/ingest/document")
def ingest_document():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    if not title or not content:
        return _json_error("title and content are required")

    meeting_id = payload.get("meeting_id")
    purpose = payload.get("purpose")

    db = SessionLocal()
    try:
        if meeting_id:
            meeting = db.get(Meeting, meeting_id)
            if not meeting:
                return _json_error("meeting_id not found", 404)

        document = Document(
            meeting_id=meeting_id,
            title=title,
            content=content,
            purpose=purpose,
        )
        db.add(document)
        db.flush()

        text_chunks = chunk_text(content)
        chunk_rows: list[Chunk] = []
        for idx, ctext in enumerate(text_chunks):
            row = Chunk(
                document_id=document.id,
                chunk_text=ctext,
                position=idx,
                chunk_metadata={"source": "document_ingest"},
            )
            db.add(row)
            db.flush()
            chunk_rows.append(row)

        if chunk_rows:
            _add_chunks_to_vector_store(chunk_rows, meeting_id, document.id)

        db.commit()
        return jsonify({"document_id": document.id, "meeting_id": meeting_id, "chunks_ingested": len(chunk_rows)})
    except Exception as exc:
        db.rollback()
        return _json_error(f"ingest failed: {exc}", 500)
    finally:
        db.close()


@app.post("/ingest/meeting")
def ingest_meeting():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    meeting_time_raw = payload.get("meeting_time")

    if not title or not content or not meeting_time_raw:
        return _json_error("title, meeting_time, and content are required")

    try:
        meeting_time = _parse_datetime(meeting_time_raw)
    except ValueError:
        return _json_error("meeting_time must be ISO-8601")

    db = SessionLocal()
    try:
        meeting = Meeting(
            title=title,
            purpose=payload.get("purpose"),
            participants=payload.get("participants"),
            platform=payload.get("platform"),
            category=payload.get("category"),
            meeting_time=meeting_time,
        )
        db.add(meeting)
        db.flush()

        document = Document(
            meeting_id=meeting.id,
            title=payload.get("document_title") or f"{title} Notes",
            content=content,
            purpose=payload.get("document_purpose") or "meeting_notes",
        )
        db.add(document)
        db.flush()

        text_chunks = chunk_text(content)
        chunk_rows: list[Chunk] = []
        for idx, ctext in enumerate(text_chunks):
            row = Chunk(
                document_id=document.id,
                chunk_text=ctext,
                position=idx,
                chunk_metadata={"source": "meeting_ingest"},
            )
            db.add(row)
            db.flush()
            chunk_rows.append(row)

        if chunk_rows:
            _add_chunks_to_vector_store(chunk_rows, meeting.id, document.id)

        db.commit()
        return jsonify({"meeting_id": meeting.id, "document_id": document.id, "chunks_ingested": len(chunk_rows)})
    except Exception as exc:
        db.rollback()
        return _json_error(f"meeting ingest failed: {exc}", 500)
    finally:
        db.close()

@app.post("/query")
def query():
    payload = request.get_json(silent=True) or {}
    query_text = (payload.get("query") or "").strip()
    if not query_text:
        return _json_error("query is required")

    db = SessionLocal()
    try:
        thread_id = payload.get("thread_id")
        thread = None

        if thread_id is not None:
            thread = db.get(Thread, thread_id)
            if not thread:
                return _json_error("thread_id not found", 404)
        else:
            thread = Thread(title=payload.get("thread_title") or _default_thread_title(query_text))
            db.add(thread)
            db.flush()

        db.add(Message(thread_id=thread.id, role="user", content=query_text))

        query_embedding = embedder.embed([query_text])[0]
        retrieved = chroma.query(query_embedding, top_k=10)
        formatted_chunks = _serialize_chunks_for_prompt(retrieved)

        threshold = float(os.getenv("CONFIDENCE_DISTANCE_THRESHOLD", "0.45"))
        avg_distance = sum(r.get("distance", 1.0) for r in retrieved) / max(1, len(retrieved))
        confidence = max(0.0, min(1.0, 1.0 - avg_distance))

        if not retrieved or avg_distance > threshold:
            fallback = {
                "outline": ["Insufficient evidence from indexed documents."],
                "report": "I am not confident in this answer because relevant context is missing or weak.",
                "todos": [],
                "events": [],
                "metadata": {
                    "confidence": confidence,
                    "avg_distance": avg_distance,
                    "reason": "low_similarity",
                },
            }
            db.add(Message(thread_id=thread.id, role="assistant", content=json.dumps(fallback)))
            db.commit()
            return jsonify({"thread_id": thread.id, "result": fallback})

        user_prompt = build_prompt(query_text, formatted_chunks)
        result = ollama.generate(user_prompt)
        if isinstance(result, dict):
            result.setdefault("metadata", {})
            result["metadata"]["confidence"] = confidence
            result["metadata"]["avg_distance"] = avg_distance

        db.add(Message(thread_id=thread.id, role="assistant", content=json.dumps(result)))
        db.commit()

        return jsonify({"thread_id": thread.id, "result": result})
    except Exception as exc:
        db.rollback()
        return _json_error(f"query failed: {exc}", 500)
    finally:
        db.close()


@app.get("/threads")
def list_threads():
    db = SessionLocal()
    try:
        rows = db.query(Thread).order_by(Thread.created_at.desc()).all()
        return jsonify(
            [
                {
                    "id": t.id,
                    "title": t.title,
                    "is_open": t.is_open,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in rows
            ]
        )
    finally:
        db.close()


@app.get("/threads/<int:thread_id>")
def get_thread(thread_id: int):
    db = SessionLocal()
    try:
        thread = db.get(Thread, thread_id)
        if not thread:
            return _json_error("thread not found", 404)
        msgs = (
            db.query(Message)
            .filter(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return jsonify(
            {
                "id": thread.id,
                "title": thread.title,
                "is_open": thread.is_open,
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in msgs
                ],
            }
        )
    finally:
        db.close()


@app.post("/threads/<int:thread_id>/message")
def add_thread_message(thread_id: int):
    payload = request.get_json(silent=True) or {}
    role = payload.get("role")
    content = (payload.get("content") or "").strip()
    if role not in {"user", "assistant", "system"}:
        return _json_error("role must be one of: user, assistant, system")
    if not content:
        return _json_error("content is required")

    db = SessionLocal()
    try:
        thread = db.get(Thread, thread_id)
        if not thread:
            return _json_error("thread not found", 404)
        msg = Message(thread_id=thread_id, role=role, content=content)
        db.add(msg)
        db.commit()
        return jsonify({"id": msg.id, "thread_id": thread_id, "role": role, "content": content}), 201
    except Exception as exc:
        db.rollback()
        return _json_error(f"could not append message: {exc}", 500)
    finally:
        db.close()


@app.get("/tasks")
def list_tasks():
    db = SessionLocal()
    try:
        rows = db.query(Task).order_by(Task.created_at.desc()).all()
        return jsonify(
            [
                {
                    "id": t.id,
                    "meeting_id": t.meeting_id,
                    "description": t.description,
                    "owners": t.owners,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "status": t.status,
                    "cmr": t.cmr,
                }
                for t in rows
            ]
        )
    finally:
        db.close()


@app.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    description = (payload.get("description") or "").strip()
    if not description:
        return _json_error("description is required")

    db = SessionLocal()
    try:
        task = Task(
            meeting_id=payload.get("meeting_id"),
            description=description,
            owners=payload.get("owners"),
            due_date=_parse_date(payload.get("due_date")),
            status=payload.get("status") or "unseen",
            cmr=payload.get("cmr"),
        )
        db.add(task)
        db.commit()
        return jsonify({"id": task.id}), 201
    except ValueError:
        db.rollback()
        return _json_error("due_date must be ISO date (YYYY-MM-DD)")
    except Exception as exc:
        db.rollback()
        return _json_error(f"could not create task: {exc}", 500)
    finally:
        db.close()


@app.patch("/tasks/<int:task_id>")
def patch_task(task_id: int):
    payload = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if not task:
            return _json_error("task not found", 404)

        if "description" in payload:
            task.description = (payload.get("description") or "").strip()
        if "owners" in payload:
            task.owners = payload.get("owners")
        if "status" in payload:
            task.status = payload.get("status")
        if "cmr" in payload:
            task.cmr = payload.get("cmr")
        if "due_date" in payload:
            task.due_date = _parse_date(payload.get("due_date"))

        db.commit()
        return jsonify({"id": task.id, "status": task.status})
    except ValueError:
        db.rollback()
        return _json_error("due_date must be ISO date (YYYY-MM-DD)")
    except Exception as exc:
        db.rollback()
        return _json_error(f"could not update task: {exc}", 500)
    finally:
        db.close()


@app.get("/events")
def list_events():
    db = SessionLocal()
    try:
        rows = db.query(Event).order_by(Event.created_at.desc()).all()
        return jsonify(
            [
                {
                    "id": e.id,
                    "related_task_ids": e.related_task_ids,
                    "event_date": e.event_date.isoformat() if e.event_date else None,
                    "deadline": e.deadline.isoformat() if e.deadline else None,
                    "status": e.status,
                    "metadata": e.event_metadata,
                }
                for e in rows
            ]
        )
    finally:
        db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)