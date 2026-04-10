import os
import anthropic
from codelens.core.chunking import FileChunk


class WorkerAgent:
    def __init__(self, config: dict, verbose: bool = False):
        self.config = config["agents"]["worker"]
        self.verbose = verbose
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def summarize(self, chunk: FileChunk, hint: str) -> str:
        if self.verbose:
            print(f"  [Worker] Summarizing: {chunk.path}")

        response = self.client.messages.create(
            model=self.config["model"],
            max_tokens=1024,
            temperature=self.config["temperature"],
            system=self._system_prompt(hint),
            messages=[{"role": "user", "content": self._build_prompt(chunk)}],
        )
        return response.content[0].text.strip()

    def estimate_tokens(self, chunk: FileChunk) -> int:
        return len(chunk.content) // 4

    def _system_prompt(self, hint: str) -> str:
        if hint == "spring-boot":
            return (
                "You are a senior Java Spring Boot engineer. "
                "Extract REST endpoints, business logic, data models, and key dependencies from the provided source file. "
                "Be concise. Return a structured summary."
            )
        return (
            "You are a senior software engineer. "
            "Summarize the purpose, key functions, and notable patterns in the provided source file. "
            "Be concise."
        )

    def _build_prompt(self, chunk: FileChunk) -> str:
        return f"File: {chunk.path}\n\n```\n{chunk.content[:8000]}\n```"
