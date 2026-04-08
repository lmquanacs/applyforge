import json
from lib.llm import BaseLLMClient


class BulletService:
    def __init__(self, llm: BaseLLMClient):
        self._llm = llm

    def rewrite(self, bullet: str, role: str) -> list[str]:
        prompt = (
            f"Rewrite the following resume bullet point for a {role} role. "
            "Return exactly 3 ATS-optimized variations as a JSON array of strings.\n\n"
            f"BULLET: {bullet}"
        )
        return json.loads(self._llm.invoke(prompt))
