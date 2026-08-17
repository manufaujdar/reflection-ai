from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    external_user_id: str = Field(min_length=1, max_length=200)
    application_id: str = Field(default="reflection-chat", min_length=1, max_length=100)
    tenant_id: str = Field(default="local", min_length=1, max_length=200)
    title: str = Field(default="New reflection", min_length=1, max_length=200)
    consent: bool
    training_consent: bool = False


class QuestionView(BaseModel):
    id: str
    prompt: str
    answer_type: str
    options: list[str]
    optional: bool


class SessionView(BaseModel):
    id: str
    user_id: str
    title: str
    status: str
    onboarding_index: int
    onboarding_total: int
    next_question: QuestionView | None
    created_at: datetime


class OnboardingAnswerCreate(BaseModel):
    question_id: str = Field(min_length=1, max_length=100)
    answer: str = Field(default="", max_length=5_000)
    skip: bool = False


class OnboardingState(BaseModel):
    complete: bool
    progress: int
    total: int
    next_question: QuestionView | None
    learned_memory_id: str | None = None


class ChatSend(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    request_id: str | None = Field(default=None, max_length=300)


class MessageView(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    redacted: bool
    created_at: datetime


class ChatReply(BaseModel):
    session_id: str
    user_message: MessageView
    assistant_message: MessageView
    personalization: dict[str, Any]
    agent_run_id: str


class FeedbackCreate(BaseModel):
    rating: float = Field(ge=-1, le=1)
    correction: str | None = Field(default=None, max_length=10_000)


class FeedbackView(BaseModel):
    event_id: str
    memory_id: str | None = None
    learned: bool


class LearningUpdate(BaseModel):
    enabled: bool


class LearningView(BaseModel):
    enabled: bool


class InspectorView(BaseModel):
    user_id: str
    learning_enabled: bool
    style: dict[str, Any]
    learning: dict[str, Any]
    memories: list[dict[str, Any]]
    recent_agent_runs: list[dict[str, Any]]
