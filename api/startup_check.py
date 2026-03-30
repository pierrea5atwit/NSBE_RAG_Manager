import requests
import time
import os


def _normalize_base_url(host: str, default_port: int) -> str:
    if host.startswith("http://") or host.startswith("https://"):
        return host
    return f"http://{host}:{default_port}"

def check_ollama(timeout=10):
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    url = f"{_normalize_base_url(ollama_host, 11434)}/api/tags"
    start = time.time()

    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(1)

    return False


def check_chroma(timeout=10):
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
    base = _normalize_base_url(chroma_host, chroma_port)
    try:
        r = requests.get(f"{base}/api/v1/heartbeat", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def run_startup_checks():
    print("Running startup checks...")

    if not check_ollama():
        raise RuntimeError(
            "Ollama is not running at /api/tags"
        )
    print("Ollama is running")

    if not check_chroma():
        raise RuntimeError(
            "ChromaDB is not running at /api/v1/heartbeat"
        )
    print("ChromaDB is reachable")

    print("Startup checks passed")