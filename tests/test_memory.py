import asyncio

import pytest
from pydantic import BaseModel

from reflection_ai.memory import HindsightMemoryStore, Mem0MemoryStore, make_memory_store


class FakeMem0:
    def __init__(self):
        self.added = []
        self.searches = []

    def add(self, content, **kwargs):
        self.added.append((content, kwargs))
        return {"results": [{"id": "mem-1"}]}

    def search(self, query, **kwargs):
        self.searches.append((query, kwargs))
        return {"results": [{"id": "mem-1", "memory": "Prefers concise answers"}]}


class FakeHindsight:
    def retain(self, **kwargs):
        return {"id": "hind-1", **kwargs}

    def recall(self, **kwargs):
        return [{"id": "hind-1", "content": "User is working on Reflection AI"}]


class FakeRecallItem(BaseModel):
    id: str
    text: str


class FakeRecallResponse:
    results = [FakeRecallItem(id="hind-2", text="Prefers evidence-backed answers")]


def test_mem0_adapter_reuses_client_contract():
    client = FakeMem0()
    store = Mem0MemoryStore(client=client)
    memory_id = asyncio.run(
        store.retain("user-1", "Prefers concise answers", {"source": "correction"})
    )
    results = asyncio.run(store.recall("user-1", "How should I answer?"))
    assert memory_id == "mem-1"
    assert client.added[0][1]["user_id"] == "user-1"
    assert client.searches[0][1]["filters"] == {"user_id": "user-1"}
    assert client.searches[0][1]["top_k"] == 5
    assert results[0]["memory"] == "Prefers concise answers"


def test_hindsight_adapter_reuses_retain_recall_contract():
    store = HindsightMemoryStore(client=FakeHindsight())
    memory_id = asyncio.run(
        store.retain("user-1", "Building Reflection AI", {"context": "project"})
    )
    results = asyncio.run(store.recall("user-1", "What project?"))
    assert memory_id == "hind-1"
    assert results[0]["content"] == "User is working on Reflection AI"


def test_memory_factory_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unsupported memory backend"):
        make_memory_store("unknown")


def test_hindsight_model_response_is_normalized():
    assert FakeRecallResponse().results
    from reflection_ai.memory import _as_results

    assert _as_results(FakeRecallResponse())[0]["text"] == "Prefers evidence-backed answers"
