from abc import ABC, abstractmethod

import httpx

from reflection_ai.config import Settings


class ModelProvider(ABC):
    @abstractmethod
    async def generate(
        self, system: str, prompt: str, history: list[dict[str, str]] | None = None
    ) -> str: ...


class MockProvider(ModelProvider):
    async def generate(
        self, system: str, prompt: str, history: list[dict[str, str]] | None = None
    ) -> str:
        return f"[personalized mock] {prompt}"


class OpenAICompatibleProvider(ModelProvider):
    """Works with hosted APIs and local servers exposing /v1/chat/completions."""

    def __init__(self, settings: Settings):
        if not settings.model_base_url:
            raise ValueError("REFLECTION_MODEL_BASE_URL is required")
        self.base_url = settings.model_base_url.rstrip("/")
        self.api_key = settings.model_api_key
        self.model = settings.model_name

    async def generate(
        self, system: str, prompt: str, history: list[dict[str, str]] | None = None
    ) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                *(history or []),
                {"role": "user", "content": prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


def make_provider(settings: Settings) -> ModelProvider:
    if settings.model_provider == "mock":
        return MockProvider()
    if settings.model_provider == "openai-compatible":
        return OpenAICompatibleProvider(settings)
    raise ValueError(f"Unsupported model provider: {settings.model_provider}")
