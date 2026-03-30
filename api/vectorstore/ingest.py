from .embedded import Embedder
from .chroma_client import ChromaStore

embedder = None
chroma = None

def ingest_chunks(chunks: list[dict]):
    """
    chunks = [
      {"id": 1, "text": "...", "meeting_id": 5, "document_id": 2, "position": 0},
      ...
    ]
    """

    global embedder, chroma
    if embedder is None:
        embedder = Embedder()
    if chroma is None:
        chroma = ChromaStore()

    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed(texts)

    for chunk, emb in zip(chunks, embeddings):
        metadata = {
            "meeting_id": chunk["meeting_id"],
            "document_id": chunk["document_id"],
            "position": chunk["position"]
        }

        chroma.add_chunk(
            chunk_id=str(chunk["id"]),
            text=chunk["text"],
            embedding=emb,
            metadata=metadata
        )