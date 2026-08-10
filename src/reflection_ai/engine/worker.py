"""Minimal worker loop that executes registered handlers against the job queue contract."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from reflection_ai.engine.jobs import InMemoryJobQueue


JobHandler = Callable[[dict[str, Any]], dict[str, Any]]


class LocalWorker:
    def __init__(self, queue: InMemoryJobQueue, worker_id: str) -> None:
        self.queue = queue
        self.worker_id = worker_id
        self.handlers: dict[str, JobHandler] = {}

    def register(self, kind: str, handler: JobHandler) -> None:
        if kind in self.handlers:
            raise ValueError(f"Handler already registered for {kind}")
        self.handlers[kind] = handler

    def run_one(self) -> bool:
        job = self.queue.claim(self.worker_id)
        if not job:
            return False
        handler = self.handlers.get(job.kind)
        if not handler:
            self.queue.fail(
                job.id,
                self.worker_id,
                f"No handler registered for {job.kind}",
                retryable=False,
            )
            return True
        try:
            result = handler({**job.payload})
        except Exception as error:
            self.queue.fail(job.id, self.worker_id, str(error), retryable=True)
        else:
            self.queue.complete(job.id, self.worker_id, result)
        return True
