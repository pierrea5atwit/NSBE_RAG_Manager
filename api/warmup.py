from api.vectorstore.embedded import Embedder
from api.llm.ollama import OllamaClient

def warmup_models():
    print("Warming up models...")

    embedder = Embedder()
    embedder.embed("warmup")
    print("Embedding model warmed up")

    llm = OllamaClient()
    llm.generate("warmup")
    print("LLM warmed up")

    print("Warmup complete")
    return embedder, llm