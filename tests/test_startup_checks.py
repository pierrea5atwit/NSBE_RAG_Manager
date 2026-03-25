import pytest

from api.startup_check import check_ollama, check_chroma, run_startup_checks
from api.warmup import warmup_models


def test_check_ollama_uses_tags_url(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        class FakeResponse:
            status_code = 200

        return FakeResponse()

    monkeypatch.setattr("api.startup_check.requests.get", fake_get)

    assert check_ollama() is True
    assert captured["url"] == "http://localhost:11434/api/tags"


def test_check_chroma_uses_heartbeat_url(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        class FakeResponse:
            status_code = 200

        return FakeResponse()

    monkeypatch.setattr("api.startup_check.requests.get", fake_get)

    assert check_chroma() is True
    assert captured["url"] == "http://localhost:8000/api/v1/heartbeat"


def test_run_startup_checks_raises_if_ollama_unavailable(monkeypatch):
    monkeypatch.setattr("api.startup_check.check_ollama", lambda: False)
    monkeypatch.setattr("api.startup_check.check_chroma", lambda: True)

    with pytest.raises(RuntimeError):
        run_startup_checks()


def test_run_startup_checks_raises_if_chroma_unavailable(monkeypatch):
    monkeypatch.setattr("api.startup_check.check_ollama", lambda: True)
    monkeypatch.setattr("api.startup_check.check_chroma", lambda: False)

    with pytest.raises(RuntimeError):
        run_startup_checks()


def test_warmup_models_calls_embed_and_generate(monkeypatch):
    calls = {"embed": [], "generate": []}

    class FakeEmbedder:
        def embed(self, text):
            calls["embed"].append(text)
            return [[0.1, 0.2, 0.3]]

    class FakeOllamaClient:
        def generate(self, prompt):
            calls["generate"].append(prompt)
            return {"ok": True}

    monkeypatch.setattr("api.warmup.Embedder", FakeEmbedder)
    monkeypatch.setattr("api.warmup.OllamaClient", FakeOllamaClient)

    warmup_models()

    assert calls["embed"] == ["warmup"]
    assert calls["generate"] == ["warmup"]