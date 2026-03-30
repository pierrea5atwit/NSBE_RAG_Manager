import os
import uuid

import pytest

from api.vectorstore.chroma_client import ChromaStore
from api.startup_check import check_chroma


pytestmark = pytest.mark.integration


def _integration_enabled() -> bool:
    return os.getenv("RUN_CHROMA_INTEGRATION", "0") == "1"


@pytest.mark.skipif(not _integration_enabled(), reason="Set RUN_CHROMA_INTEGRATION=1 to run live Chroma checks")
def test_chroma_healthcheck_and_roundtrip(monkeypatch):
    monkeypatch.setenv("CHROMA_HOST", os.getenv("CHROMA_HOST", "localhost"))
    monkeypatch.setenv("CHROMA_PORT", os.getenv("CHROMA_PORT", "8000"))

    assert check_chroma(timeout=5) is True

    collection_name = f"it_{uuid.uuid4().hex[:8]}"
    store = ChromaStore(collection_name=collection_name)

    store.add_chunk(
        chunk_id="it-1",
        text="alpha beta gamma",
        embedding=[0.01, 0.02, 0.03, 0.04],
        metadata={"meeting_id": 999, "document_id": 1, "position": 0},
    )

    results = store.query([0.01, 0.02, 0.03, 0.04], top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "it-1"
    assert results[0]["metadata"]["meeting_id"] == 999
