from api.llm.ollama import OllamaClient

def test_ollama_client_parses_json( mocker ):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"response": '{"outline": {"title": "Test"}}'}
    mock_response.raise_for_status.return_value = None

    mocker.patch("requests.post", return_value=mock_response)

    client = OllamaClient(model_name="mistral")
    result = client.generate("test prompt")

    assert "outline" in result
    assert result["outline"]["title"] == "Test"
