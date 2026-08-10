"""SQLAlchemy read adapter; domain and engine code do not import ORM models directly."""

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from reflection_ai.db import Evidence, MemoryEvidence, MemoryRecord, utcnow
from reflection_ai.domain.models import (
    EvidenceRecord,
    MemoryAssertion,
    MemoryKind,
    Sensitivity,
    TemporalWindow,
)


class SqlAlchemyDomainMapper:
    @staticmethod
    def evidence(row: Evidence) -> EvidenceRecord:
        return EvidenceRecord(
            id=row.id,
            subject_id=row.user_id,
            kind=row.kind,
            content=row.content,
            content_hash=row.content_hash,
            observed_at=row.observed_at,
            sensitivity=Sensitivity(row.sensitivity),
            source=row.source,
            source_reference=row.source_reference,
            expires_at=row.expires_at,
            attributes={**row.attributes},
        )

    @staticmethod
    def memory(row: MemoryRecord, evidence_ids: list[str]) -> MemoryAssertion:
        return MemoryAssertion(
            id=row.id,
            subject_id=row.user_id,
            kind=MemoryKind(row.memory_type),
            content=row.content,
            normalized_key=row.normalized_key,
            confidence=row.confidence,
            evidence_ids=tuple(evidence_ids),
            temporal=TemporalWindow(row.valid_from, row.valid_to, row.expires_at),
            sensitivity=Sensitivity(row.sensitivity),
            status=row.status,
            explicit=row.explicit,
            supersedes_id=row.supersedes_id,
            attributes={**row.attributes},
        )


class SqlAlchemyMemoryReader:
    def __init__(self, db: Session) -> None:
        self.db = db

    def active(self, subject_id: str, at: datetime | None = None) -> list[MemoryAssertion]:
        moment = at or utcnow()
        rows = self.db.scalars(
            select(MemoryRecord).where(
                MemoryRecord.user_id == subject_id,
                MemoryRecord.status == "active",
                or_(MemoryRecord.valid_from.is_(None), MemoryRecord.valid_from <= moment),
                or_(MemoryRecord.valid_to.is_(None), MemoryRecord.valid_to > moment),
                or_(MemoryRecord.expires_at.is_(None), MemoryRecord.expires_at > moment),
            )
        ).all()
        assertions = []
        for row in rows:
            evidence_ids = list(
                self.db.scalars(
                    select(MemoryEvidence.evidence_id).where(MemoryEvidence.memory_id == row.id)
                ).all()
            )
            assertions.append(SqlAlchemyDomainMapper.memory(row, evidence_ids))
        return assertions
