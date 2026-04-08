import os
from .base import BaseLLMClient


def get_llm_client() -> BaseLLMClient:
    provider = os.environ.get("LLM_PROVIDER", "bedrock")

    if provider == "openai":
        from .openai import OpenAIClient
        return OpenAIClient()

    if provider == "bedrock":
        from .bedrock import BedrockClient
        return BedrockClient()

    raise ValueError(f"Unsupported LLM_PROVIDER: '{provider}'. Choose 'bedrock' or 'openai'.")
