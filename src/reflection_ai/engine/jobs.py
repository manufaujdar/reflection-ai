"""Small idempotent queue baseline with leases, retries, and dead-letter behavior."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    DEAD = "dead"


@dataclass(frozen=True)
class JobRecord:
    id: str
    kind: str
    subject_id: str
    payload: dict[str, Any]
    idempotency_key: str
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    max_attempts: int = 3
    available_at: datetime = field(default_factory=utcnow)
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    result: dict[str, Any] = field(default_factory=dict)
    last_error: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


class InMemoryJobQueue:
    """A deterministic development queue; production adapters should use durable storage."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._idempotency: dict[tuple[str, str], str] = {}
        self._lock = RLock()

    def enqueue(
        self,
        kind: str,
        subject_id: str,
        payload: dict[str, Any],
        idempotency_key: str,
        max_attempts: int = 3,
    ) -> str:
        if not kind or not subject_id or not idempotency_key:
            raise ValueError("kind, subject_id, and idempotency_key are required")
        with self._lock:
            key = (subject_id, idempotency_key)
            if existing := self._idempotency.get(key):
                return existing
            job = JobRecord(
                id=str(uuid4()),
                kind=kind,
                subject_id=subject_id,
                payload={**payload},
                idempotency_key=idempotency_key,
                max_attempts=max_attempts,
            )
            self._jobs[job.id] = job
            self._idempotency[key] = job.id
            return job.id

    def claim(self, worker_id: str, lease_seconds: int = 60) -> JobRecord | None:
        now = utcnow()
        with self._lock:
            candidates = sorted(
                self._jobs.values(), key=lambda item: (item.available_at, item.created_at)
            )
            for job in candidates:
                lease_expired = job.lease_expires_at is not None and job.lease_expires_at <= now
                claimable = job.status == JobStatus.QUEUED or (
                    job.status == JobStatus.RUNNING and lease_expired
                )
                if claimable and job.available_at <= now:
                    claimed = replace(
                        job,
                        status=JobStatus.RUNNING,
                        attempts=job.attempts + 1,
                        lease_owner=worker_id,
                        lease_expires_at=now + timedelta(seconds=lease_seconds),
                        updated_at=now,
                    )
                    self._jobs[job.id] = claimed
                    return claimed
            return None

    def _owned(self, job_id: str, worker_id: str) -> JobRecord:
        job = self._jobs.get(job_id)
        if not job:
            raise KeyError(job_id)
        if job.status != JobStatus.RUNNING or job.lease_owner != worker_id:
            raise PermissionError("Worker does not own this running job")
        return job

    def complete(self, job_id: str, worker_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._owned(job_id, worker_id)
            self._jobs[job_id] = replace(
                job,
                status=JobStatus.COMPLETED,
                result={**result},
                lease_owner=None,
                lease_expires_at=None,
                updated_at=utcnow(),
            )

    def fail(self, job_id: str, worker_id: str, error: str, retryable: bool = True) -> None:
        with self._lock:
            job = self._owned(job_id, worker_id)
            dead = not retryable or job.attempts >= job.max_attempts
            delay = min(2 ** max(job.attempts - 1, 0), 60)
            self._jobs[job_id] = replace(
                job,
                status=JobStatus.DEAD if dead else JobStatus.QUEUED,
                available_at=utcnow() if dead else utcnow() + timedelta(seconds=delay),
                lease_owner=None,
                lease_expires_at=None,
                last_error=error,
                updated_at=utcnow(),
            )

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)
