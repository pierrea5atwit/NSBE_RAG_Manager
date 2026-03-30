import requests
import os

class Embedder:
    def __init__(self, model="nomic-embed-text", host=None):
        self.model = model
        host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"http://{host}"
        if ":" not in host.split("//", 1)[-1]:
            host = f"{host}:11434"
        self.url = f"{host}/api/embeddings"

    def embed(self, texts):
        """
        Accepts a list of strings and returns a list of embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for t in texts:
            payload = {
                "model": self.model,
                "prompt": t
            }
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            emb = response.json().get("embedding")
            embeddings.append(emb)

        return embeddings