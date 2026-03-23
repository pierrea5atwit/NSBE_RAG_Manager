"""

- Main file for LLM functions, API usage and programming for RAG setup
- 

"""

from flask import Flask, request, jsonify
from llm.ollama import OllamaClient
from llm.prompts import build_prompt

from vectorstore.embedded import Embedder
from vectorstore.chroma_client import ChromaStore

app = Flask(__name__)
ollama = OllamaClient(model_name="mistral")
embedder = Embedder()
chroma = ChromaStore()

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