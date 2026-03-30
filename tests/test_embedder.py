from api.vectorstore.embedded import Embedder

def test_embedder_output_shape(mocker):
    mock_response = mocker.Mock()
    mock_response.json.side_effect = [
        {"embedding": [0.1] * 384},
        {"embedding": [0.2] * 384},
    ]
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.post", return_value=mock_response)

    embedder = Embedder()
    texts = ["hello world", "meeting notes"]
    embeddings = embedder.embed(texts)

    assert len(embeddings) == 2
    assert isinstance(embeddings[0], list)
    assert len(embeddings[0]) > 100  # MiniLM ~384 dims
