import base64

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from resume_parser import parse_pdf
from ai_generator import generate_feedback, generate_cover_letter, rewrite_bullet

logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()


@app.post("/parse-resume")
@tracer.capture_method
def handle_parse_resume():
    body = app.current_event.json_body
    file_bytes = base64.b64decode(body["file"])
    resume_text = parse_pdf(file_bytes)
    feedback = generate_feedback(resume_text)
    return {"resume_text": resume_text, "feedback": feedback}


@app.post("/generate-cover-letter")
@tracer.capture_method
def handle_generate_cover_letter():
    body = app.current_event.json_body
    cover_letter = generate_cover_letter(body["resume_text"], body["job_description"])
    return {"cover_letter": cover_letter}


@app.post("/rewrite-bullet")
@tracer.capture_method
def handle_rewrite_bullet():
    body = app.current_event.json_body
    variations = rewrite_bullet(body["bullet"], body["role"])
    return {"variations": variations}


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
