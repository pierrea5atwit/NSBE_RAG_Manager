from api.vectorstore.embedded import Embedder

def test_embedder_output_shape():
    embedder = Embedder()
    texts = ["hello world", "meeting notes"]
    embeddings = embedder.embed(texts)

    assert len(embeddings) == 2
    assert isinstance(embeddings[0], list)
    assert len(embeddings[0]) > 100  # MiniLM ~384 dims
