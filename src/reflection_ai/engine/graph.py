"""Temporal relationship graph that preserves provenance and validity windows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4


def aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class Relationship:
    id: str
    subject_id: str
    source_id: str
    target_id: str
    relation: str
    evidence_ids: tuple[str, ...]
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    invalidated_by: str | None = None

    def active_at(self, moment: datetime) -> bool:
        point = aware(moment)
        start = aware(self.valid_from)
        end = aware(self.valid_to)
        return self.invalidated_by is None and not (
            (start and point < start) or (end and point >= end)
        )


class TemporalRelationshipGraph:
    def __init__(self) -> None:
        self._edges: dict[str, Relationship] = {}
        self._lock = RLock()

    def link(
        self,
        subject_id: str,
        source_id: str,
        target_id: str,
        relation: str,
        evidence_ids: list[str] | tuple[str, ...],
        valid_from: datetime | None = None,
        valid_to: datetime | None = None,
    ) -> str:
        if not evidence_ids:
            raise ValueError("Relationships require provenance evidence")
        edge = Relationship(
            id=str(uuid4()),
            subject_id=subject_id,
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            evidence_ids=tuple(evidence_ids),
            valid_from=valid_from,
            valid_to=valid_to,
        )
        with self._lock:
            self._edges[edge.id] = edge
        return edge.id

    def invalidate(self, edge_id: str, evidence_id: str, at: datetime | None = None) -> None:
        with self._lock:
            edge = self._edges.get(edge_id)
            if not edge:
                raise KeyError(edge_id)
            self._edges[edge_id] = Relationship(
                **{
                    **asdict(edge),
                    "evidence_ids": edge.evidence_ids,
                    "valid_to": at or datetime.now(timezone.utc),
                    "invalidated_by": evidence_id,
                }
            )

    def neighbors(
        self,
        subject_id: str,
        node_id: str,
        depth: int = 1,
        at: datetime | None = None,
    ) -> list[dict]:
        if depth < 1 or depth > 5:
            raise ValueError("depth must be between 1 and 5")
        moment = at or datetime.now(timezone.utc)
        visited_nodes = {node_id}
        frontier = {node_id}
        found: list[Relationship] = []
        with self._lock:
            for _ in range(depth):
                next_frontier: set[str] = set()
                for edge in self._edges.values():
                    if edge.subject_id != subject_id or not edge.active_at(moment):
                        continue
                    if edge.source_id in frontier or edge.target_id in frontier:
                        found.append(edge)
                        for candidate in (edge.source_id, edge.target_id):
                            if candidate not in visited_nodes:
                                next_frontier.add(candidate)
                                visited_nodes.add(candidate)
                frontier = next_frontier
                if not frontier:
                    break
        deduplicated = {edge.id: edge for edge in found}
        return [asdict(edge) for edge in deduplicated.values()]
