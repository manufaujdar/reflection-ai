"""Central decisions for storing, retrieving, reflecting, and training on personal data."""

from dataclasses import dataclass
from enum import StrEnum

from reflection_ai.domain.models import Sensitivity


class DataUse(StrEnum):
    STORE = "store"
    RETRIEVE = "retrieve"
    REFLECT = "reflect"
    TRAIN = "train"
    EXPORT = "export"
    DELETE = "delete"


@dataclass(frozen=True)
class PolicyContext:
    use: DataUse
    personalization_consent: bool
    training_consent: bool = False
    learning_enabled: bool = True
    safety_mode: str = "standard"
    sensitivity: Sensitivity = Sensitivity.NORMAL
    allow_restricted_retrieval: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    obligations: tuple[str, ...] = ()


class PolicyEngine:
    protected_modes = frozenset({"deep_analysis", "dims", "clinical_protocol", "emergency"})

    def decide(self, context: PolicyContext) -> PolicyDecision:
        if context.use in {DataUse.DELETE, DataUse.EXPORT}:
            return PolicyDecision(True, "subject_control", ("audit",))
        if not context.personalization_consent:
            return PolicyDecision(False, "personalization_consent_missing")
        if (
            context.use in {DataUse.STORE, DataUse.REFLECT, DataUse.TRAIN}
            and not context.learning_enabled
        ):
            return PolicyDecision(False, "learning_disabled")
        if context.use == DataUse.TRAIN and not context.training_consent:
            return PolicyDecision(False, "training_consent_missing")
        if context.use == DataUse.RETRIEVE and context.safety_mode.lower() in self.protected_modes:
            return PolicyDecision(False, f"protected_mode:{context.safety_mode.lower()}")
        if (
            context.use == DataUse.RETRIEVE
            and context.sensitivity == Sensitivity.RESTRICTED
            and not context.allow_restricted_retrieval
        ):
            return PolicyDecision(False, "restricted_memory_not_allowed")
        obligations = ["tenant_scope", "audit"]
        if context.sensitivity != Sensitivity.NORMAL:
            obligations.extend(["redact_logs", "encrypt_at_rest"])
        if context.use == DataUse.TRAIN:
            obligations.extend(["holdout_evaluation", "rollback_target", "dataset_lineage"])
        return PolicyDecision(True, "allowed", tuple(obligations))
