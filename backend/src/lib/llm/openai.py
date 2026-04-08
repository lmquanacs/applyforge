import os
from openai import OpenAI

from .base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    def invoke(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        return response.choices[0].message.content
