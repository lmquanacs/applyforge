from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """Send a prompt and return the text response."""
