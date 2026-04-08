import os
import json
import boto3

from .base import BaseLLMClient


class BedrockClient(BaseLLMClient):
    def __init__(self):
        self._client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        self._model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

    def invoke(self, prompt: str) -> str:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = self._client.invoke_model(modelId=self._model_id, body=body)
        return json.loads(response["body"].read())["content"][0]["text"]
