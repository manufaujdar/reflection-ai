"""Optional memory backends built on maintained open-source packages.

These adapters intentionally depend on public client APIs instead of copying upstream
implementations. Clients can be injected in tests or supplied by an application.
"""

import asyncio
from typing import Any


def _as_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (dict, list)) and hasattr(value, "results"):
        value = value.results
    if isinstance(value, dict):
        value = value.get("results", value.get("memories", []))
    if not isinstance(value, list):
        return []
    results = []
    for item in value:
        if isinstance(item, dict):
            results.append(item)
        elif hasattr(item, "model_dump"):
            results.append(item.model_dump(mode="json"))
        else:
            results.append({"content": str(item)})
    return results


class Mem0MemoryStore:
    """Reuse the Apache-2.0 Mem0 memory engine through its supported Python API."""

    def __init__(self, client: Any | None = None, config: dict[str, Any] | None = None):
        if client is None:
            try:
                from mem0 import Memory
            except ImportError as error:
                raise RuntimeError(
                    "Install Reflection AI with the 'memory-mem0' extra to use Mem0"
                ) from error
            client = Memory.from_config(config) if config else Memory()
        self.client = client

    async def retain(self, subject_id: str, content: str, metadata: dict[str, Any]) -> str:
        result = await asyncio.to_thread(
            self.client.add, content, user_id=subject_id, metadata=metadata
        )
        normalized = _as_results(result)
        if normalized:
            return str(normalized[0].get("id", normalized[0].get("memory_id", "stored")))
        if isinstance(result, dict):
            return str(result.get("id", result.get("memory_id", "stored")))
        if operation_id := getattr(result, "operation_id", None):
            return str(operation_id)
        if bank_id := getattr(result, "bank_id", None):
            return f"{bank_id}:stored"
        return "stored"

    async def recall(self, subject_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        result = await asyncio.to_thread(
            self.client.search, query, filters={"user_id": subject_id}, top_k=limit
        )
        return _as_results(result)[:limit]


class HindsightMemoryStore:
    """Reuse Hindsight's MIT-licensed retain/recall engine through its client API."""

    def __init__(self, base_url: str | None = None, client: Any | None = None):
        if client is None:
            try:
                from hindsight_client import Hindsight
            except ImportError as error:
                raise RuntimeError(
                    "Install Reflection AI with the 'memory-hindsight' extra to use Hindsight"
                ) from error
            if not base_url:
                raise ValueError("A Hindsight base_url is required")
            client = Hindsight(base_url=base_url)
        self.client = client

    async def retain(self, subject_id: str, content: str, metadata: dict[str, Any]) -> str:
        kwargs: dict[str, Any] = {}
        if context := metadata.get("context"):
            kwargs["context"] = str(context)
        if timestamp := metadata.get("timestamp"):
            kwargs["timestamp"] = str(timestamp)
        extra_metadata = {
            str(key): str(value)
            for key, value in metadata.items()
            if key not in {"context", "timestamp"}
        }
        if extra_metadata:
            kwargs["metadata"] = extra_metadata
        result = await asyncio.to_thread(
            self.client.retain, bank_id=subject_id, content=content, **kwargs
        )
        if isinstance(result, dict):
            return str(result.get("id", result.get("memory_id", "stored")))
        return "stored"

    async def recall(self, subject_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        result = await asyncio.to_thread(self.client.recall, bank_id=subject_id, query=query)
        return _as_results(result)[:limit]


def make_memory_store(
    backend: str, *, config: dict[str, Any] | None = None, client: Any | None = None
):
    if backend == "mem0":
        return Mem0MemoryStore(client=client, config=config)
    if backend == "hindsight":
        return HindsightMemoryStore(base_url=(config or {}).get("base_url"), client=client)
    raise ValueError(f"Unsupported memory backend: {backend}")
