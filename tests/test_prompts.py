from llm.prompts import build_prompt, SYSTEM_PROMPT

def test_system_prompt_contains_schema():
    assert "JSON Schema" in SYSTEM_PROMPT
    assert "outline" in SYSTEM_PROMPT
    assert "todos" in SYSTEM_PROMPT

def test_prompt_builder_includes_query_and_context():
    query = "What did we decide about onboarding?"
    chunks = [
        {"id": 1, "meeting_id": 5, "text": "We agreed to onboard interns June 1st."}
    ]

    prompt = build_prompt(query, chunks)

    assert query in prompt
    assert "onboard interns" in prompt
    assert "[chunk id=1, meeting_id=5]" in prompt
