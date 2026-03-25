import requests
import time

def check_ollama(timeout=10):
    url = "http://localhost:11434/api/tags"
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
    try:
        r = requests.get("http://localhost:8000/api/v1/heartbeat", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def run_startup_checks():
    print("Running startup checks...")

    if not check_ollama():
        raise RuntimeError(
            "Ollama is not running at http://localhost:11434/api/tags"
        )
    print("Ollama is running")

    if not check_chroma():
        raise RuntimeError(
            "ChromaDB is not running at http://localhost:8000/api/v1/heartbeat"
        )
    print("ChromaDB is reachable")

    print("Startup checks passed")