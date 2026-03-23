import chromadb
from chromadb.config import Settings

class ChromaStore:
    def __init__(self, collection_name="meeting_chunks", host="chroma", port=8000):
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(allow_reset=True)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunk(self, chunk_id: str, text: str, embedding: list[float], metadata: dict):
        """
        Insert a chunk into Chroma.
        """
        self.collection.add(
            ids=[str(chunk_id)],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def query(self, query_embedding: list[float], top_k: int = 10):
        """
        Retrieve top-k similar chunks.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Convert Chroma output into a clean list of dicts
        retrieved = []
        for i in range(len(results["ids"][0])):
            retrieved.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return retrieved