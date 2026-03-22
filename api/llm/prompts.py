SYSTEM_PROMPT = """
You are an AI assistant that analyzes organizational documents, meeting notes, and user queries.
Your job is to produce structured JSON outputs that follow the exact schema below.

You MUST return valid JSON. Do not include commentary, markdown, or explanations.

JSON Schema:
{
  "outline": {
    "title": "string",
    "sections": [
      {
        "heading": "string",
        "bullets": ["string"]
      }
    ]
  },
  "report": {
    "summary": "string",
    "details": "string"
  },
  "todos": [
    {
      "description": "string",
      "owner": "string or null",
      "due_date": "YYYY-MM-DD or null",
      "status": "pending | in_progress | done | unknown",
      "source_meeting_id": "integer or null",
      "confidence": "float between 0 and 1"
    }
  ],
  "events": [
    {
      "title": "string",
      "date": "YYYY-MM-DD or null",
      "deadline": "YYYY-MM-DD or null",
      "status": "planned | unplanned | complete | cancelled | unknown",
      "related_tasks": ["string"],
      "confidence": "float between 0 and 1"
    }
  ],
  "metadata": {
    "query_interpreted_as": "semantic | structured",
    "retrieval": {
      "top_k": "integer",
      "avg_similarity": "float",
      "min_similarity": "float",
      "max_similarity": "float"
    },
    "notes": "string"
  }
}

Rules:
- If unsure, set confidence to a low value (0.0–0.3).
- If the query cannot be answered from the provided context, say so in metadata.notes.
- Never hallucinate owners, dates, or deadlines.
- Use null when information is missing.
- Keep all text concise and factual.

"""


def build_prompt(query: str, retrieved_chunks: list[dict]) -> str:
    """
    Build the user prompt that includes the query and retrieved context.
    """

    context_blocks = []
    for ch in retrieved_chunks:
        block = (
            f"[chunk id={ch.get('id')}, meeting_id={ch.get('meeting_id')}]\n"
            f"{ch.get('text')}"
        )
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."

    prompt = f"""
User Query:
{query}

Relevant Context:
{context_text}

Instructions:
Analyze the user query using the provided context. If the query is structured,
interpret it as structured. If semantic, interpret it as semantic.

Fill out the JSON schema completely. Use null for missing fields.
Return ONLY valid JSON.
"""

    return prompt.strip()