from __future__ import annotations

from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider:
    """Thin abstraction layer to keep OpenAI replaceable later."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    @property
    def enabled(self) -> bool:
        return bool(self.client and self.settings.enable_openai_extraction)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured.")
        response = self.client.responses.create(
            model=self.settings.openai_chat_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={"format": {"type": "json_object"}},
        )
        logger.info("openai_chat_json_completed", model=self.settings.openai_chat_model)
        output_text = response.output_text
        import json

        return json.loads(output_text)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured.")
        response = self.client.embeddings.create(model=self.settings.openai_embedding_model, input=texts)
        return [item.embedding for item in response.data]
