import json
from lib.llm import BaseLLMClient


class ResumeService:
    def __init__(self, llm: BaseLLMClient):
        self._llm = llm

    def generate_feedback(self, resume_text: str) -> dict:
        prompt = (
            "Act as an expert technical recruiter. Review the following resume, "
            "identify weak points, and suggest actionable improvements "
            "(e.g., adding metrics, improving action verbs). "
            "Return the response in structured JSON format.\n\n"
            f"RESUME:\n{resume_text}"
        )
        return json.loads(self._llm.invoke(prompt))
