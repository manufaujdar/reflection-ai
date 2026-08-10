"""Deterministic consolidation planner with explicit unresolved-conflict output."""

from __future__ import annotations

import re
from dataclasses import dataclass

from reflection_ai.domain.models import MemoryAssertion


SPACE_RE = re.compile(r"\s+")


def normalize_content(value: str) -> str:
    return SPACE_RE.sub(" ", value.strip().lower())


@dataclass(frozen=True)
class ConsolidationAction:
    action: str
    memory_id: str
    target_id: str | None
    reason: str


@dataclass(frozen=True)
class ConsolidationConflict:
    normalized_key: str
    memory_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ConsolidationPlan:
    actions: tuple[ConsolidationAction, ...]
    conflicts: tuple[ConsolidationConflict, ...]


class ConsolidationPlanner:
    """Plans safe deduplication; ambiguous contradictions remain unresolved."""

    def plan(self, memories: list[MemoryAssertion]) -> ConsolidationPlan:
        groups: dict[str, list[MemoryAssertion]] = {}
        for memory in memories:
            if memory.status == "active":
                groups.setdefault(memory.normalized_key, []).append(memory)
        actions: list[ConsolidationAction] = []
        conflicts: list[ConsolidationConflict] = []
        for key, group in groups.items():
            if len(group) < 2:
                continue
            ordered = sorted(
                group,
                key=lambda item: (item.explicit, item.confidence, item.id),
                reverse=True,
            )
            winner = ordered[0]
            for candidate in ordered[1:]:
                if normalize_content(candidate.content) == normalize_content(winner.content):
                    actions.append(
                        ConsolidationAction(
                            action="supersede_duplicate",
                            memory_id=candidate.id,
                            target_id=winner.id,
                            reason="Same normalized key and equivalent content",
                        )
                    )
                    continue
                confidence_gap = winner.confidence - candidate.confidence
                if winner.explicit and not candidate.explicit and confidence_gap >= 0:
                    actions.append(
                        ConsolidationAction(
                            action="supersede_inference",
                            memory_id=candidate.id,
                            target_id=winner.id,
                            reason="Explicit evidence takes precedence over an inferred assertion",
                        )
                    )
                elif confidence_gap >= 0.2:
                    actions.append(
                        ConsolidationAction(
                            action="supersede_low_confidence",
                            memory_id=candidate.id,
                            target_id=winner.id,
                            reason="Confidence difference meets the deterministic threshold",
                        )
                    )
                else:
                    conflicts.append(
                        ConsolidationConflict(
                            normalized_key=key,
                            memory_ids=tuple(sorted({winner.id, candidate.id})),
                            reason="Contradictory assertions require user confirmation or stronger evidence",
                        )
                    )
        unique_conflicts = {(item.normalized_key, item.memory_ids): item for item in conflicts}
        return ConsolidationPlan(tuple(actions), tuple(unique_conflicts.values()))
