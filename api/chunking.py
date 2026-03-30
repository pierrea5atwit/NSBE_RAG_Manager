def chunk_text(text: str, chunk_size: int = 220, overlap: int = 40) -> list[str]:
    """Chunk text by words with overlap for retrieval continuity."""
    if not text or not text.strip():
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)

    for start in range(0, len(words), step):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break

    return chunks
