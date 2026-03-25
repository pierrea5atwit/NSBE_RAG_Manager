from api.vectorstore import ingest


def test_embedding_and_storage_pipeline(monkeypatch):
    calls = {"embed_texts": None, "added": []}

    class FakeEmbedder:
        def embed(self, texts):
            calls["embed_texts"] = texts
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FakeChroma:
        def add_chunk(self, chunk_id, text, embedding, metadata):
            calls["added"].append((chunk_id, text, embedding, metadata))

    monkeypatch.setattr(ingest, "embedder", FakeEmbedder())
    monkeypatch.setattr(ingest, "chroma", FakeChroma())

    chunks = [
        {
            "id": 1,
            "text": "hello world",
            "meeting_id": 5,
            "document_id": 2,
            "position": 0,
        }
    ]

    ingest.ingest_chunks(chunks)

    assert calls["embed_texts"] == ["hello world"]
    assert len(calls["added"]) == 1
    assert calls["added"][0][0] == "1"
    assert calls["added"][0][1] == "hello world"
    assert calls["added"][0][2] == [0.1, 0.2, 0.3]
    assert calls["added"][0][3]["meeting_id"] == 5