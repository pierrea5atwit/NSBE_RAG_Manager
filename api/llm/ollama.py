import requests
import json
from .prompts import SYSTEM_PROMPT


class OllamaClient:
    def __init__(self, model_name="mistral", host="http://localhost:11434"):
        self.model_name = model_name
        self.url = f"{host}/api/generate"

    def generate(self, user_prompt: str) -> dict:
        """
        Send a prompt to Ollama and return parsed JSON.
        """

        payload = {
            "model": self.model_name,
            "system": SYSTEM_PROMPT,
            "prompt": user_prompt,
            "stream": False
        }

        response = requests.post(self.url, json=payload)
        response.raise_for_status()

        raw_text = response.json().get("response", "")

        # Try parsing JSON
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # You can add fallback logic here if needed
            raise ValueError(f"Model did not return valid JSON:\n{raw_text}")