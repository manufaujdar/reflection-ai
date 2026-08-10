from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from reflection_ai.chat.models import AgentRun, ChatMessage, ChatSession, StyleProfile
from reflection_ai.chat.orchestrator import ChatDomainError, ChatNotFound, ChatOrchestrator
from reflection_ai.chat.questions import QUESTIONS, question_at
from reflection_ai.chat.schemas import (
    ChatReply,
    ChatSend,
    FeedbackCreate,
    FeedbackView,
    InspectorView,
    MessageView,
    OnboardingAnswerCreate,
    OnboardingState,
    QuestionView,
    SessionCreate,
    SessionView,
)
from reflection_ai.db import Profile, User, get_db, utcnow


router = APIRouter(prefix="/v1/chat", tags=["adaptive-chat"])


def _question_view(index: int) -> QuestionView | None:
    question = question_at(index)
    if not question:
        return None
    return QuestionView(
        id=question.id,
        prompt=question.prompt,
        answer_type=question.answer_type,
        options=list(question.options),
        optional=question.id in {"display_name", "boundaries"},
    )


def _session_view(session: ChatSession) -> SessionView:
    created_at = session.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return SessionView(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        status=session.status,
        onboarding_index=session.onboarding_index,
        onboarding_total=len(QUESTIONS),
        next_question=_question_view(session.onboarding_index),
        created_at=created_at,
    )


def _message_view(message: ChatMessage) -> MessageView:
    created_at = message.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return MessageView(
        id=message.id,
        role=message.role,
        content=message.content,
        redacted=message.redacted,
        created_at=created_at,
    )


def _error(error: Exception) -> HTTPException:
    if isinstance(error, ChatNotFound):
        return HTTPException(404, str(error))
    if isinstance(error, PermissionError):
        return HTTPException(403, str(error))
    return HTTPException(409, str(error))


def build_chat_router(orchestrator: ChatOrchestrator) -> APIRouter:
    @router.post("/sessions", response_model=SessionView, status_code=201)
    def create_session(body: SessionCreate, db: Session = Depends(get_db)):
        if not body.consent:
            raise HTTPException(403, "Consent is required to create a learning chat")
        user = db.scalar(
            select(User).where(
                User.application_id == body.application_id,
                User.tenant_id == body.tenant_id,
                User.external_id == body.external_user_id,
            )
        )
        if user:
            user.consent = body.consent
            user.training_consent = body.training_consent
        else:
            user = User(
                external_id=body.external_user_id,
                application_id=body.application_id,
                tenant_id=body.tenant_id,
                consent=body.consent,
                training_consent=body.training_consent,
                attributes={"learning_enabled": True, "created_by": "adaptive-chat"},
            )
            user.profile = Profile(preferences={})
            db.add(user)
        try:
            db.flush()
        except IntegrityError as error:
            db.rollback()
            raise HTTPException(409, "Unable to resolve chat subject") from error
        session = ChatSession(user_id=user.id, title=body.title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return _session_view(session)

    @router.get("/sessions/{session_id}", response_model=SessionView)
    def get_session(session_id: str, db: Session = Depends(get_db)):
        try:
            return _session_view(orchestrator.require_session(db, session_id))
        except ChatNotFound as error:
            raise _error(error) from error

    @router.get("/sessions/{session_id}/onboarding", response_model=OnboardingState)
    def onboarding_state(session_id: str, db: Session = Depends(get_db)):
        try:
            session = orchestrator.require_session(db, session_id)
        except ChatNotFound as error:
            raise _error(error) from error
        return OnboardingState(
            complete=session.status != "onboarding",
            progress=session.onboarding_index,
            total=len(QUESTIONS),
            next_question=_question_view(session.onboarding_index),
        )

    @router.post("/sessions/{session_id}/onboarding", response_model=OnboardingState)
    def answer_onboarding(
        session_id: str, body: OnboardingAnswerCreate, db: Session = Depends(get_db)
    ):
        try:
            session = orchestrator.require_session(db, session_id)
            session, memory_id = orchestrator.answer_onboarding(
                db, session, body.question_id, body.answer, body.skip
            )
        except (ChatNotFound, ChatDomainError, PermissionError) as error:
            raise _error(error) from error
        return OnboardingState(
            complete=session.status != "onboarding",
            progress=session.onboarding_index,
            total=len(QUESTIONS),
            next_question=_question_view(session.onboarding_index),
            learned_memory_id=memory_id,
        )

    @router.post("/sessions/{session_id}/messages", response_model=ChatReply)
    async def send_message(session_id: str, body: ChatSend, db: Session = Depends(get_db)):
        try:
            session = orchestrator.require_session(db, session_id)
            user_message, assistant, run = await orchestrator.send(
                db, session, body.message, body.request_id
            )
        except (ChatNotFound, ChatDomainError, PermissionError) as error:
            raise _error(error) from error
        return ChatReply(
            session_id=session.id,
            user_message=_message_view(user_message),
            assistant_message=_message_view(assistant),
            personalization={
                "style_version": run.trace.get("style_version"),
                "style_samples": run.trace.get("style_samples"),
                "style_instructions": run.trace.get("style_instructions", []),
                "memories_used": run.trace.get("memory_trace", []),
            },
            agent_run_id=run.id,
        )

    @router.get("/sessions/{session_id}/messages", response_model=list[MessageView])
    def list_messages(session_id: str, limit: int = 200, db: Session = Depends(get_db)):
        try:
            session = orchestrator.require_session(db, session_id)
        except ChatNotFound as error:
            raise _error(error) from error
        return [_message_view(message) for message in orchestrator.messages(db, session, limit)]

    @router.post("/messages/{message_id}/feedback", response_model=FeedbackView)
    def send_feedback(message_id: str, body: FeedbackCreate, db: Session = Depends(get_db)):
        message = db.get(ChatMessage, message_id)
        if not message or message.role != "assistant":
            raise HTTPException(404, "Assistant message not found")
        try:
            event, memory = orchestrator.feedback(db, message, body.rating, body.correction)
        except PermissionError as error:
            raise _error(error) from error
        return FeedbackView(event_id=event.id, memory_id=memory.id if memory else None, learned=True)

    @router.get("/sessions/{session_id}/personalization", response_model=InspectorView)
    def inspect_personalization(session_id: str, db: Session = Depends(get_db)):
        try:
            session = orchestrator.require_session(db, session_id)
            user = orchestrator.require_user(db, session.user_id)
        except ChatNotFound as error:
            raise _error(error) from error
        style = db.get(StyleProfile, user.id)
        memories = orchestrator.memories.list_active(db, user.id)
        runs = list(
            db.scalars(
                select(AgentRun)
                .where(AgentRun.session_id == session.id)
                .order_by(AgentRun.created_at.desc())
                .limit(10)
            ).all()
        )
        return InspectorView(
            user_id=user.id,
            learning_enabled=orchestrator.learning_enabled(user),
            style={
                "sample_count": style.sample_count if style else 0,
                "version": style.version if style else 0,
                "metrics": style.metrics if style else {},
                "instructions": style.instructions if style else [],
                "safe_scope": "observable writing mechanics only",
            },
            memories=[
                {
                    "id": item.id,
                    "type": item.memory_type,
                    "content": item.content,
                    "confidence": item.confidence,
                    "explicit": item.explicit,
                    "evidence_ids": orchestrator.memories.evidence_ids(db, item.id),
                }
                for item in memories
            ],
            recent_agent_runs=[
                {
                    "id": run.id,
                    "status": run.status,
                    "model": run.model,
                    "prompt_hash": run.prompt_hash,
                    "trace": run.trace,
                }
                for run in runs
            ],
        )

    @router.delete("/sessions/{session_id}", status_code=204)
    def archive_session(session_id: str, db: Session = Depends(get_db)):
        try:
            session = orchestrator.require_session(db, session_id)
        except ChatNotFound as error:
            raise _error(error) from error
        session.status = "archived"
        session.updated_at = utcnow()
        db.add(session)
        db.commit()
        return Response(status_code=204)

    @router.get("/capabilities")
    def chat_capabilities():
        return {
            "onboarding": True,
            "explicit_memory": True,
            "observable_style_learning": True,
            "agent_run_traces": True,
            "provider_agnostic": True,
            "weight_training_inline": False,
            "weight_training_reason": "requires consent, offline evaluation, promotion, and rollback",
            "authentication": False,
            "production_ready": False,
        }

    return router
