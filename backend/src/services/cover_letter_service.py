from lib.llm import BaseLLMClient


class CoverLetterService:
    def __init__(self, llm: BaseLLMClient):
        self._llm = llm

    def generate(self, resume_text: str, job_description: str) -> str:
        prompt = (
            "You are an expert career coach. Using the candidate's resume and the job description below, "
            "write a highly tailored, professional cover letter.\n\n"
            f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{job_description}"
        )
        return self._llm.invoke(prompt)
