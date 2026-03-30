import os

import requests
import streamlit as st

"""
This Streamlit app serves as a simple interface to test the local RAG (Retrieval-Augmented Generation) system. It allows users to ingest documents into the vector store and query the RAG agent, all while providing quick health checks for the API.


Start dependencies and API guide:

    docker compose up --build
    Ensure Ollama models are available (first run):
    ollama pull mistral
    ollama pull nomic-embed-text
    Re-open Streamlit and run health first from the app:
    http://localhost:5000/health should return ok
    Then run ingest/query in Streamlit.
"""


DEFAULT_API_BASE = os.getenv("RAG_API_BASE", "http://localhost:5000")


def show_connection_help(api_base_url: str, exc: Exception) -> None:
    st.error(f"Request error: {exc}")
    st.info(
        "Backend is unreachable. Start the API first, then retry. "
        f"Current target: {api_base_url}"
    )
    st.code(
        "docker compose up --build\n"
        "# or, local dev:\n"
        "python -m api.app",
        language="bash",
    )


st.set_page_config(page_title="Local RAG Test Bench", layout="wide")
st.title("Local RAG Test Bench")
st.caption("Ingest text into the vector pipeline, then query the RAG agent.")

api_base = st.text_input("API Base URL", value=DEFAULT_API_BASE).rstrip("/")

left, right = st.columns(2)

with left:
    st.subheader("Ingest Document")
    doc_title = st.text_input("Document title", value="Scratch Notes")
    doc_content = st.text_area(
        "Document content",
        height=220,
        placeholder="Paste meeting notes, docs, or transcripts here...",
    )

    if st.button("Ingest into Vector Store", use_container_width=True):
        if not doc_title.strip() or not doc_content.strip():
            st.error("Title and content are required.")
        else:
            payload = {
                "title": doc_title.strip(),
                "content": doc_content.strip(),
                "purpose": "streamlit_test",
            }
            try:
                response = requests.post(f"{api_base}/ingest/document", json=payload, timeout=30)
                body = response.json()
                if response.ok:
                    st.success(f"Ingested document {body.get('document_id')} with {body.get('chunks_ingested', 0)} chunks.")
                    st.json(body)
                else:
                    st.error(f"Ingest failed ({response.status_code})")
                    st.json(body)
            except requests.RequestException as exc:
                show_connection_help(api_base, exc)

with right:
    st.subheader("Ask RAG Agent")
    thread_id_input = st.text_input("Optional thread id", value="")
    query_text = st.text_area(
        "Question",
        height=120,
        placeholder="What did we decide about onboarding?",
    )

    if st.button("Query Agent", use_container_width=True):
        if not query_text.strip():
            st.error("A question is required.")
        else:
            payload = {"query": query_text.strip()}
            if thread_id_input.strip().isdigit():
                payload["thread_id"] = int(thread_id_input.strip())

            try:
                response = requests.post(f"{api_base}/query", json=payload, timeout=60)
                body = response.json()
                if response.ok:
                    st.success(f"Thread ID: {body.get('thread_id')}")
                    st.subheader("Agent Result")
                    st.json(body.get("result", body))
                else:
                    st.error(f"Query failed ({response.status_code})")
                    st.json(body)
            except requests.RequestException as exc:
                show_connection_help(api_base, exc)

st.divider()
st.subheader("Quick Checks")

if st.button("Run /health"):
    try:
        response = requests.get(f"{api_base}/health", timeout=10)
        st.write(f"HTTP {response.status_code}")
        st.json(response.json())
    except requests.RequestException as exc:
        show_connection_help(api_base, exc)

with st.expander("Sample cURL"):
    st.code(
        f"""curl -X POST {api_base}/ingest/document \\
  -H 'Content-Type: application/json' \\
  -d '{{\"title\":\"Demo\",\"content\":\"Onboarding will be two weeks.\"}}'\n\n"
        f"curl -X POST {api_base}/query \\
  -H 'Content-Type: application/json' \\
  -d '{{\"query\":\"What is the onboarding plan?\"}}'""",
        language="bash",
    )
