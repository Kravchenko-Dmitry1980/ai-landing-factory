import json
import logging

import httpx

from app.config import Settings
from app.services.llm.base import LLMClient
from app.services.llm.errors import LLMResponseError, LLMUnavailableError

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClient):
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise LLMUnavailableError("OPENAI_API_KEY is not set")
        self._api_key = settings.openai_api_key
        self._model = settings.openai_model

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
    ) -> dict:
        del schema_name
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            logger.error("OpenAI error %s: %s", response.status_code, response.text[:500])
            raise LLMResponseError(f"OpenAI HTTP {response.status_code}")

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError("Malformed OpenAI response") from exc

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMResponseError("OpenAI returned non-JSON content") from exc
