import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from reflection_ai.domain.models import (
    EvaluationReport,
    MemoryAssertion,
    MemoryKind,
    ModelArtifact,
    Sensitivity,
    TemporalWindow,
    RetrievalCandidate,
)
from reflection_ai.domain.policy import DataUse, PolicyContext, PolicyEngine
from reflection_ai.engine.consolidation import ConsolidationPlanner
from reflection_ai.engine.evaluation import (
    EvaluationGate,
    precision_at_k,
    preference_adherence,
    recall_at_k,
)
from reflection_ai.engine.graph import TemporalRelationshipGraph
from reflection_ai.engine.jobs import InMemoryJobQueue, JobStatus
from reflection_ai.engine.registry import InMemoryModelRegistry
from reflection_ai.engine.runtime import LocalPersonalizationRuntime
from reflection_ai.engine.retrieval import RetrievalFusion, RetrievalPlan
from reflection_ai.engine.training import GatedTrainingPipeline, TrainingRequest
from reflection_ai.engine.worker import LocalWorker


def memory(
    memory_id: str,
    content: str,
    *,
    subject: str = "user-1",
    key: str = "style",
    confidence: float = 0.8,
    explicit: bool = False,
    temporal: TemporalWindow | None = None,
):
    return MemoryAssertion(
        id=memory_id,
        subject_id=subject,
        kind=MemoryKind.PREFERENCE,
        content=content,
        normalized_key=key,
        confidence=confidence,
        evidence_ids=(f"ev-{memory_id}",),
        explicit=explicit,
        temporal=temporal or TemporalWindow(),
    )


def artifact(artifact_id: str, version: int, subject: str = "user-1"):
    return ModelArtifact(
        id=artifact_id,
        subject_id=subject,
        base_model="small-model",
        uri=f"artifact://{artifact_id}",
        dataset_hash="a" * 64,
        version=version,
    )


def test_temporal_window_and_policy_are_explicit():
    now = datetime.now(timezone.utc)
    assert TemporalWindow(valid_from=now - timedelta(days=1)).active_at(now)
    assert not TemporalWindow(expires_at=now - timedelta(seconds=1)).active_at(now)

    engine = PolicyEngine()
    denied = engine.decide(PolicyContext(use=DataUse.TRAIN, personalization_consent=True))
    assert denied.reason == "training_consent_missing"
    allowed = engine.decide(
        PolicyContext(
            use=DataUse.TRAIN,
            personalization_consent=True,
            training_consent=True,
            sensitivity=Sensitivity.SENSITIVE,
        )
    )
    assert allowed.allowed
    assert "dataset_lineage" in allowed.obligations
    assert "encrypt_at_rest" in allowed.obligations


def test_job_queue_is_idempotent_leased_and_dead_letters():
    queue = InMemoryJobQueue()
    first = queue.enqueue("reflect", "user-1", {"evidence": ["e1"]}, "e1")
    duplicate = queue.enqueue("reflect", "user-1", {"evidence": ["e1"]}, "e1")
    assert duplicate == first
    claimed = queue.claim("worker-1")
    assert claimed.id == first
    with pytest.raises(PermissionError):
        queue.complete(first, "worker-2", {})
    queue.fail(first, "worker-1", "invalid structured output", retryable=False)
    assert queue.get(first).status == JobStatus.DEAD


def test_local_worker_executes_registered_handler():
    queue = InMemoryJobQueue()
    worker = LocalWorker(queue, "worker-1")
    worker.register("reflect", lambda payload: {"count": len(payload["evidence_ids"])})
    job_id = queue.enqueue("reflect", "user-1", {"evidence_ids": ["e1", "e2"]}, "reflection-1")
    assert worker.run_one()
    assert queue.get(job_id).status == JobStatus.COMPLETED
    assert queue.get(job_id).result == {"count": 2}


def test_local_vector_index_is_subject_and_time_scoped():
    runtime = LocalPersonalizationRuntime.create(64)
    now = datetime.now(timezone.utc)
    rows = [
        memory("m1", "Prefers concise technical answers"),
        memory("m2", "Prefers verbose poetry", subject="user-2"),
        memory(
            "m3",
            "Old preference for concise answers",
            temporal=TemporalWindow(expires_at=now - timedelta(days=1)),
        ),
    ]
    runtime.vector_index.upsert(rows, runtime.embedder.embed([item.content for item in rows]))
    query = runtime.embedder.embed(["concise technical answer"])[0]
    results = runtime.vector_index.search("user-1", query, limit=5, at=now)
    assert [item.memory.id for item in results] == ["m1"]
    assert results[0].score_components["vector_similarity"] > 0


def test_retrieval_fusion_combines_channels_and_filters_restricted_memory():
    normal = memory("m1", "Prefers concise answers")
    restricted = replace(memory("m2", "Private medical fact"), sensitivity=Sensitivity.RESTRICTED)
    semantic = [
        RetrievalCandidate(normal, 0.9, ranker="semantic"),
        RetrievalCandidate(restricted, 0.8, ranker="semantic"),
    ]
    lexical = [RetrievalCandidate(normal, 0.7, ranker="lexical")]
    fused = RetrievalFusion().fuse(
        RetrievalPlan("user-1", "concise answer"),
        {"semantic": semantic, "lexical": lexical},
    )
    assert [item.memory.id for item in fused] == ["m1"]
    assert fused[0].ranker == "rrf:lexical+semantic"


def test_temporal_graph_preserves_provenance_and_invalidation():
    graph = TemporalRelationshipGraph()
    edge_id = graph.link("user-1", "person", "project", "works_on", ["evidence-1"])
    assert graph.neighbors("user-1", "person")[0]["evidence_ids"] == ("evidence-1",)
    assert graph.neighbors("user-2", "person") == []
    graph.invalidate(edge_id, "correction-1")
    assert graph.neighbors("user-1", "person") == []


def test_consolidation_deduplicates_but_surfaces_ambiguous_conflicts():
    planner = ConsolidationPlanner()
    plan = planner.plan(
        [
            memory("m1", "Prefers concise answers", confidence=0.9, explicit=True),
            memory("m2", " prefers   concise answers ", confidence=0.7),
            memory("m3", "Prefers detailed answers", confidence=0.85, explicit=True),
        ]
    )
    assert any(action.memory_id == "m2" for action in plan.actions)
    assert plan.conflicts[0].memory_ids == ("m1", "m3")


def test_evaluation_metrics_and_registry_require_a_passing_incumbent_comparison():
    assert recall_at_k(["m1", "m2"], {"m1", "m3"}, 2) == 0.5
    assert precision_at_k(["m1", "m2"], {"m1"}, 2) == 0.5
    assert preference_adherence("A concise example", ["concise"], ["verbose"]) == 1

    gate = EvaluationGate()
    report = gate.evaluate(
        "a1",
        None,
        {
            "personalization": 0.8,
            "safety_violations": 0,
            "privacy_leakage": 0,
            "general_capability": 0.9,
        },
    )
    assert report.passed
    registry = InMemoryModelRegistry()
    registry.register(artifact("a1", 1))
    registry.promote("user-1", "a1", report)
    assert registry.resolve_artifact("user-1").id == "a1"

    registry.register(artifact("a2", 2))
    second_report = EvaluationReport("a2", "a1", {"personalization": 0.9}, True)
    registry.promote("user-1", "a2", second_report)
    assert registry.resolve_artifact("user-1").id == "a2"
    assert registry.rollback("user-1").id == "a1"


class FakeTrainer:
    async def train(self, dataset_uri, base_model, previous_artifact=None):
        return {"id": "candidate-1", "artifact_uri": "artifact://candidate-1"}


class PassingEvaluator:
    async def evaluate(self, candidate, incumbent, holdout_uri):
        return EvaluationReport(candidate.id, incumbent.id if incumbent else None, {}, True)


def test_training_pipeline_skips_without_consent_and_promotes_only_after_evaluation():
    registry = InMemoryModelRegistry()
    pipeline = GatedTrainingPipeline(FakeTrainer(), PassingEvaluator(), registry)
    request = TrainingRequest(
        subject_id="user-1",
        dataset_uri="dataset.jsonl",
        dataset_hash="b" * 64,
        holdout_uri="holdout.jsonl",
        base_model="small-model",
        example_count=25,
        personalization_consent=True,
        training_consent=False,
    )
    skipped = asyncio.run(pipeline.run(request))
    assert skipped.status == "skipped"
    promoted = asyncio.run(pipeline.run(replace(request, training_consent=True)))
    assert promoted.status == "promoted"
    assert registry.resolve_artifact("user-1").id == "candidate-1"
