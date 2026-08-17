from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from reflection_ai.config import get_settings
from reflection_ai.chat.models import AgentRun, ChatMessage, ChatSession, OnboardingAnswer, StyleProfile
from reflection_ai.chat.orchestrator import ChatOrchestrator
from reflection_ai.chat.router import build_chat_router
from reflection_ai.db import (
    Evidence,
    Event,
    MemoryAudit,
    MemoryEvidence,
    MemoryRecord,
    Profile,
    ReflectionProposal,
    TrainingRun,
    User,
    get_db,
    init_db,
)
from reflection_ai.personalization import (
    ContextCompiler,
    DomainConflict,
    DomainNotFound,
    EvidenceService,
    MemoryService,
    ReflectionService,
    RetentionService,
    redact_training_text,
)
from reflection_ai.providers import make_provider
from reflection_ai.schemas import (
    ContextRequest,
    ContextResponse,
    EvidenceCreate,
    EvidenceView,
    EventCreate,
    EventView,
    GenerateRequest,
    GenerateResponse,
    MemoryCreate,
    MemorySearchResponse,
    MemoryView,
    ProposalCreate,
    ProposalView,
    ReflectionAnalyzeRequest,
    ReflectionAnalyzeResponse,
    RetentionResult,
    SubjectResolveRequest,
    TrainingView,
    UserCreate,
    UserPolicyUpdate,
    UserPolicyView,
    UserView,
)
from reflection_ai.services import PersonalizationService, TrainingService, event_count
from reflection_ai.web_ui import CONSOLE_HTML


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Reflection AI", version="0.2.0", lifespan=lifespan)
settings = get_settings()
personalization = PersonalizationService(settings, make_provider(settings))
training = TrainingService(settings)
evidence_service = EvidenceService()
memory_service = MemoryService()
reflection = ReflectionService(memory_service)
context_compiler = ContextCompiler()
retention = RetentionService()
chat = ChatOrchestrator(
    settings,
    personalization.provider,
    evidence_service,
    memory_service,
    reflection,
    context_compiler,
)
app.include_router(build_chat_router(chat))

CHAT_FRONTEND = Path(__file__).parent / "frontend"
app.mount("/chat-assets", StaticFiles(directory=CHAT_FRONTEND), name="chat-assets")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def local_console() -> str:
    return CONSOLE_HTML


@app.get("/chat", response_class=FileResponse, include_in_schema=False)
def chat_frontend():
    return CHAT_FRONTEND / "chat.html"


def require_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def user_view(user: User) -> UserView:
    return UserView(
        id=user.id,
        application_id=user.application_id,
        tenant_id=user.tenant_id,
        external_id=user.external_id,
        consent=user.consent,
        training_consent=user.training_consent,
        preferences=user.profile.preferences if user.profile else {},
    )


def evidence_view(evidence: Evidence, duplicate: bool = False) -> EvidenceView:
    return EvidenceView(
        id=evidence.id,
        kind=evidence.kind,
        source=evidence.source,
        sensitivity=evidence.sensitivity,
        content_hash=evidence.content_hash,
        observed_at=as_utc(evidence.observed_at),
        expires_at=as_utc(evidence.expires_at),
        created_at=as_utc(evidence.created_at),
        duplicate=duplicate,
    )


def memory_view(
    db: Session, memory: MemoryRecord, evidence_ids: list[str] | None = None
) -> MemoryView:
    return MemoryView(
        id=memory.id,
        memory_type=memory.memory_type,
        content=memory.content,
        normalized_key=memory.normalized_key,
        status=memory.status,
        confidence=memory.confidence,
        explicit=memory.explicit,
        sensitivity=memory.sensitivity,
        valid_from=as_utc(memory.valid_from),
        valid_to=as_utc(memory.valid_to),
        expires_at=as_utc(memory.expires_at),
        supersedes_id=memory.supersedes_id,
        evidence_ids=evidence_ids
        if evidence_ids is not None
        else memory_service.evidence_ids(db, memory.id),
        created_at=as_utc(memory.created_at),
    )


def proposal_view(proposal: ReflectionProposal) -> ProposalView:
    return ProposalView(
        id=proposal.id,
        action=proposal.action,
        target_memory_id=proposal.target_memory_id,
        memory_type=proposal.memory_type,
        content=proposal.content,
        normalized_key=proposal.normalized_key,
        confidence=proposal.confidence,
        reason=proposal.reason,
        evidence_ids=proposal.evidence_ids,
        status=proposal.status,
        created_at=as_utc(proposal.created_at),
        decided_at=as_utc(proposal.decided_at),
    )


def domain_error(error: Exception) -> HTTPException:
    if isinstance(error, DomainNotFound):
        return HTTPException(404, str(error))
    if isinstance(error, PermissionError):
        return HTTPException(403, str(error))
    return HTTPException(409, str(error))


def find_subject(db: Session, application_id: str, tenant_id: str, external_id: str) -> User | None:
    return db.scalar(
        select(User).where(
            User.application_id == application_id,
            User.tenant_id == tenant_id,
            User.external_id == external_id,
        )
    )


def learning_enabled(user: User) -> bool:
    return user.attributes.get("learning_enabled", True) is not False


def safe_event_payload(data: dict) -> dict:
    payload = {**data}
    redacted = False
    for field in ("input_text", "output_text"):
        if payload.get(field):
            payload[field], changed = redact_training_text(payload[field])
            redacted = redacted or changed
    if redacted:
        payload["attributes"] = {**payload.get("attributes", {}), "secret_redacted": True}
    return payload


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/capabilities")
def capabilities() -> dict[str, object]:
    """Expose client-safe invariants so integrations do not guess policy behavior."""

    return {
        "provider_agnostic": True,
        "consent_required_for_storage": True,
        "training_consent_required": True,
        "deletion_supported": True,
        "evidence_linked_memory": True,
        "production_ready": False,
    }


@app.post("/v1/users", response_model=UserView, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    user = User(**body.model_dump())
    user.profile = Profile(preferences={})
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "external_id already exists")
    db.refresh(user)
    return user_view(user)


@app.post("/v1/subjects/resolve", response_model=UserView)
def resolve_subject(body: SubjectResolveRequest, db: Session = Depends(get_db)):
    existing = find_subject(db, body.application_id, body.tenant_id, body.external_id)
    if existing:
        existing.consent = body.consent
        existing.training_consent = body.training_consent
        existing.attributes = {**existing.attributes, **body.attributes}
        db.commit()
        db.refresh(existing)
        return user_view(existing)
    return create_user(UserCreate(**body.model_dump()), db)


@app.post("/v1/context", response_model=ContextResponse)
def get_context(body: ContextRequest, db: Session = Depends(get_db)):
    user = find_subject(db, body.application_id, body.tenant_id, body.external_user_id)
    if not user:
        raise HTTPException(404, "Subject not registered")
    ranked = (
        memory_service.search(db, user.id, body.memory_query, body.memory_limit)
        if user.consent and body.memory_query and body.safety.allow_personalization
        else []
    )
    compiled, trace = context_compiler.compile(ranked, body.memory_char_budget)
    return personalization.build_context(user, body, compiled, trace)


@app.get("/v1/users/{user_id}", response_model=UserView)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return user_view(require_user(db, user_id))


@app.get("/v1/users/{user_id}/policy", response_model=UserPolicyView)
def get_policy(user_id: str, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    return UserPolicyView(
        personalization_consent=user.consent,
        training_consent=user.training_consent,
        learning_enabled=learning_enabled(user),
        default_retention_days=user.attributes.get("default_retention_days"),
    )


@app.patch("/v1/users/{user_id}/policy", response_model=UserPolicyView)
def update_policy(user_id: str, body: UserPolicyUpdate, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    attributes = {**user.attributes}
    if body.learning_enabled is not None:
        attributes["learning_enabled"] = body.learning_enabled
    if "default_retention_days" in body.model_fields_set:
        if body.default_retention_days is None:
            attributes.pop("default_retention_days", None)
        else:
            attributes["default_retention_days"] = body.default_retention_days
    user.attributes = attributes
    db.commit()
    db.refresh(user)
    return get_policy(user_id, db)


@app.delete("/v1/users/{user_id}", status_code=204)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    memory_ids = list(
        db.scalars(select(MemoryRecord.id).where(MemoryRecord.user_id == user.id)).all()
    )
    proposal_ids = list(
        db.scalars(select(ReflectionProposal.id).where(ReflectionProposal.user_id == user.id)).all()
    )
    db.query(AgentRun).filter(AgentRun.user_id == user.id).delete()
    db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.query(OnboardingAnswer).filter(OnboardingAnswer.user_id == user.id).delete()
    db.query(ChatSession).filter(ChatSession.user_id == user.id).delete()
    db.query(StyleProfile).filter(StyleProfile.user_id == user.id).delete()
    if memory_ids:
        db.query(MemoryEvidence).filter(MemoryEvidence.memory_id.in_(memory_ids)).delete(
            synchronize_session=False
        )
        db.query(MemoryAudit).filter(MemoryAudit.memory_id.in_(memory_ids)).delete(
            synchronize_session=False
        )
    if proposal_ids:
        db.query(MemoryAudit).filter(MemoryAudit.proposal_id.in_(proposal_ids)).delete(
            synchronize_session=False
        )
    db.query(ReflectionProposal).filter(ReflectionProposal.user_id == user.id).delete()
    db.query(MemoryRecord).filter(MemoryRecord.user_id == user.id).delete()
    db.query(Evidence).filter(Evidence.user_id == user.id).delete()
    db.query(Event).filter(Event.user_id == user.id).delete()
    db.query(TrainingRun).filter(TrainingRun.user_id == user.id).delete()
    if user.profile:
        db.delete(user.profile)
    db.delete(user)
    db.commit()
    training.delete_subject_artifacts(user_id)


@app.post("/v1/users/{user_id}/events", response_model=EventView, status_code=201)
def add_event(user_id: str, body: EventCreate, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    if not user.consent:
        raise HTTPException(403, "Personalization consent is required")
    if not learning_enabled(user):
        raise HTTPException(403, "Learning is disabled for this subject")
    if body.idempotency_key:
        existing = db.scalar(
            select(Event).where(
                Event.user_id == user.id, Event.idempotency_key == body.idempotency_key
            )
        )
        if existing:
            return EventView(id=existing.id, created_at=as_utc(existing.created_at), duplicate=True)
    event = Event(user_id=user.id, **safe_event_payload(body.model_dump()))
    db.add(event)
    db.commit()
    db.refresh(event)
    retained_evidence = evidence_service.retain_event(db, user, event)
    if event.kind in {"preference", "correction"}:
        proposals, _, _ = reflection.analyze(db, user, [retained_evidence.id], limit=1)
        for proposal in proposals:
            if proposal.status == "pending":
                reflection.apply(db, user, proposal.id)
    if event_count(db, user.id) % settings.profile_refresh_events == 0:
        personalization.refresh_profile(db, user)
    return EventView(id=event.id, created_at=as_utc(event.created_at), duplicate=False)


@app.post("/v1/users/{user_id}/generate", response_model=GenerateResponse)
async def generate(user_id: str, body: GenerateRequest, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    profile = user.profile
    ranked = memory_service.search(db, user.id, body.prompt, limit=8) if user.consent else []
    compiled, memory_trace = context_compiler.compile(ranked)
    system = personalization.system_prompt(profile, body.system_prompt)
    if compiled:
        system = f"{system}\n\n{compiled}"
    text = await personalization.provider.generate(system, body.prompt)
    event_id = None
    if user.consent and learning_enabled(user):
        event = Event(
            user_id=user.id,
            kind="interaction",
            **safe_event_payload(
                {"input_text": body.prompt, "output_text": text, "attributes": body.metadata}
            ),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        evidence_service.retain_event(db, user, event)
        event_id = event.id
    return GenerateResponse(
        text=text,
        applied_profile_version=profile.version,
        event_id=event_id,
        memory_trace=memory_trace,
    )


@app.post("/v1/users/{user_id}/profile/refresh", response_model=UserView)
def refresh_profile(user_id: str, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    if not user.consent:
        raise HTTPException(403, "Personalization consent is required")
    if not learning_enabled(user):
        raise HTTPException(403, "Learning is disabled for this subject")
    personalization.refresh_profile(db, user)
    db.refresh(user)
    return user_view(user)


@app.post("/v1/users/{user_id}/training-runs", response_model=TrainingView, status_code=201)
def train(user_id: str, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    if not user.consent or not user.training_consent:
        raise HTTPException(403, "Personalization and training consent are required")
    if not learning_enabled(user):
        raise HTTPException(403, "Learning is disabled for this subject")
    run = training.run(db, user)
    return TrainingView.model_validate(run, from_attributes=True)


@app.post("/v1/users/{user_id}/evidence", response_model=EvidenceView, status_code=201)
def retain_evidence(user_id: str, body: EvidenceCreate, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    try:
        evidence, duplicate = evidence_service.retain(db, user, body)
    except (PermissionError, DomainConflict) as error:
        raise domain_error(error) from error
    return evidence_view(evidence, duplicate)


@app.post("/v1/users/{user_id}/memories", response_model=MemoryView, status_code=201)
def create_memory(user_id: str, body: MemoryCreate, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    if not user.consent:
        raise HTTPException(403, "Personalization consent is required")
    if not learning_enabled(user):
        raise HTTPException(403, "Learning is disabled for this subject")
    try:
        memory = memory_service.create_explicit(db, user, body)
    except (DomainConflict, DomainNotFound) as error:
        raise domain_error(error) from error
    return memory_view(db, memory, body.evidence_ids)


@app.get("/v1/users/{user_id}/memories", response_model=list[MemorySearchResponse])
def search_memories(
    user_id: str,
    query: str = "",
    limit: int = 8,
    db: Session = Depends(get_db),
):
    user = require_user(db, user_id)
    if not user.consent:
        raise HTTPException(403, "Personalization consent is required")
    ranked = memory_service.search(db, user.id, query, min(max(limit, 1), 25))
    return [
        MemorySearchResponse(
            memory=memory_view(db, item.memory, item.evidence_ids),
            score=item.score,
            explanation=item.explanation,
        )
        for item in ranked
    ]


@app.delete("/v1/users/{user_id}/memories/{memory_id}", response_model=MemoryView)
def revoke_memory(user_id: str, memory_id: str, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    try:
        memory = memory_service.revoke(db, user, memory_id, "User-requested revocation")
    except DomainNotFound as error:
        raise domain_error(error) from error
    return memory_view(db, memory)


@app.post(
    "/v1/users/{user_id}/reflection/proposals",
    response_model=ProposalView,
    status_code=201,
)
def create_proposal(user_id: str, body: ProposalCreate, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    if not user.consent:
        raise HTTPException(403, "Personalization consent is required")
    if not learning_enabled(user):
        raise HTTPException(403, "Learning is disabled for this subject")
    try:
        proposal = reflection.propose(db, user, body)
    except (DomainConflict, DomainNotFound) as error:
        raise domain_error(error) from error
    return proposal_view(proposal)


@app.get(
    "/v1/users/{user_id}/reflection/proposals",
    response_model=list[ProposalView],
)
def list_proposals(
    user_id: str,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    user = require_user(db, user_id)
    query = select(ReflectionProposal).where(ReflectionProposal.user_id == user.id)
    if status:
        query = query.where(ReflectionProposal.status == status)
    proposals = db.scalars(query.order_by(ReflectionProposal.created_at.desc())).all()
    return [proposal_view(item) for item in proposals]


@app.post(
    "/v1/users/{user_id}/reflection/proposals/{proposal_id}/apply",
    response_model=MemoryView,
)
def apply_proposal(user_id: str, proposal_id: str, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    if not learning_enabled(user):
        raise HTTPException(403, "Learning is disabled for this subject")
    try:
        memory = reflection.apply(db, user, proposal_id)
    except (DomainConflict, DomainNotFound) as error:
        raise domain_error(error) from error
    return memory_view(db, memory)


@app.post(
    "/v1/users/{user_id}/reflection/analyze",
    response_model=ReflectionAnalyzeResponse,
)
def analyze_evidence(
    user_id: str,
    body: ReflectionAnalyzeRequest,
    db: Session = Depends(get_db),
):
    user = require_user(db, user_id)
    if not user.consent:
        raise HTTPException(403, "Personalization consent is required")
    if not learning_enabled(user):
        raise HTTPException(403, "Learning is disabled for this subject")
    try:
        proposals, inspected, skipped = reflection.analyze(db, user, body.evidence_ids, body.limit)
    except (DomainConflict, DomainNotFound) as error:
        raise domain_error(error) from error
    return ReflectionAnalyzeResponse(
        proposals=[proposal_view(item) for item in proposals],
        inspected_evidence=inspected,
        skipped_evidence=skipped,
    )


@app.post("/v1/users/{user_id}/retention/purge", response_model=RetentionResult)
def purge_retention(user_id: str, db: Session = Depends(get_db)):
    user = require_user(db, user_id)
    evidence_deleted, memories_revoked = retention.purge(db, user)
    return RetentionResult(
        evidence_deleted=evidence_deleted,
        memories_revoked=memories_revoked,
    )
