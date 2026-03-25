"""Main API entrypoint for RAG querying."""

from flask import Flask, request, jsonify

try:
    from .llm.prompts import build_prompt
    from .startup_check import run_startup_checks
    from .warmup import warmup_models
    from .vectorstore.chroma_client import ChromaStore
except ImportError:
    from llm.prompts import build_prompt
    from startup_check import run_startup_checks
    from warmup import warmup_models
    from vectorstore.chroma_client import ChromaStore


# Required startup checks/warmup before serving requests.
run_startup_checks()
embedder, ollama = warmup_models()
chroma = ChromaStore()

app = Flask(__name__)

@app.post("/query")
def query():
    data = request.json
    query_text = data["query"]

    # 1. Embed query
    query_embedding = embedder.embed([query_text])[0]

    # 2. Retrieve chunks
    retrieved = chroma.query(query_embedding, top_k=10)

    # 3. Format for prompt
    formatted_chunks = [
        {
            "id": r["id"],
            "meeting_id": r["metadata"].get("meeting_id"),
            "text": r["text"]
        }
        for r in retrieved
    ]

    # 4. Build prompt
    user_prompt = build_prompt(query_text, formatted_chunks)

    # 5. Call LLM
    result = ollama.generate(user_prompt)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)