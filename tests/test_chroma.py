import pytest
from api.vectorstore.chroma_client import ChromaStore

class FakeCollection:
    def __init__(self):
        self.data = []

    def add(self, ids, documents, embeddings, metadatas):
        self.data.append({
            "id": ids[0],
            "text": documents[0],
            "embedding": embeddings[0],
            "metadata": metadatas[0]
        })

    def query(self, query_embeddings, n_results):
        # Return the stored data as if they were top results
        return {
            "ids": [[item["id"] for item in self.data]],
            "documents": [[item["text"] for item in self.data]],
            "metadatas": [[item["metadata"] for item in self.data]],
            "distances": [[0.1 for _ in self.data]]
        }

class FakeClient:
    def get_or_create_collection(self, name, metadata):
        return FakeCollection()

@pytest.fixture
def chroma(monkeypatch):
    monkeypatch.setattr("api.vectorstore.chroma_client.chromadb.HttpClient", lambda *a, **k: FakeClient())
    return ChromaStore()

def test_add_and_query(chroma):
    chroma.add_chunk("1", "hello world", [0.1, 0.2], {"meeting_id": 5})
    results = chroma.query([0.1, 0.2], top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["metadata"]["meeting_id"] == 5
