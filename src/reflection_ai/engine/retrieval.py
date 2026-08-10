"""Provider-independent multi-channel retrieval fusion with policy filtering."""

from __future__ import annotations

from dataclasses import dataclass

from reflection_ai.domain.models import RetrievalCandidate, Sensitivity
from reflection_ai.domain.policy import DataUse, PolicyContext, PolicyEngine


@dataclass(frozen=True)
class RetrievalPlan:
    subject_id: str
    query: str
    limit: int = 8
    safety_mode: str = "standard"
    allow_restricted: bool = False


class RetrievalFusion:
    """Reciprocal-rank fusion avoids assuming incomparable provider scores are calibrated."""

    def __init__(self, policy: PolicyEngine | None = None, rank_constant: int = 60) -> None:
        self.policy = policy or PolicyEngine()
        self.rank_constant = rank_constant

    def fuse(
        self,
        plan: RetrievalPlan,
        channels: dict[str, list[RetrievalCandidate]],
    ) -> list[RetrievalCandidate]:
        combined: dict[str, dict] = {}
        for channel_name, candidates in channels.items():
            seen_in_channel: set[str] = set()
            for rank, candidate in enumerate(candidates, start=1):
                memory = candidate.memory
                if memory.id in seen_in_channel or memory.subject_id != plan.subject_id:
                    continue
                seen_in_channel.add(memory.id)
                decision = self.policy.decide(
                    PolicyContext(
                        use=DataUse.RETRIEVE,
                        personalization_consent=True,
                        safety_mode=plan.safety_mode,
                        sensitivity=Sensitivity(memory.sensitivity),
                        allow_restricted_retrieval=plan.allow_restricted,
                    )
                )
                if not decision.allowed or not memory.usable_at():
                    continue
                entry = combined.setdefault(
                    memory.id,
                    {"memory": memory, "rrf": 0.0, "components": {}, "channels": []},
                )
                contribution = 1 / (self.rank_constant + rank)
                entry["rrf"] += contribution
                entry["components"][f"rrf:{channel_name}"] = contribution
                entry["channels"].append(channel_name)
        results = [
            RetrievalCandidate(
                memory=entry["memory"],
                score=round(entry["rrf"], 8),
                score_components={
                    key: round(value, 8) for key, value in entry["components"].items()
                },
                ranker="rrf:" + "+".join(sorted(entry["channels"])),
            )
            for entry in combined.values()
        ]
        return sorted(results, key=lambda item: item.score, reverse=True)[: max(plan.limit, 0)]
