import re

from sqlalchemy.orm import Session

from reflection_ai.chat.models import StyleProfile
from reflection_ai.db import utcnow


SENTENCE_RE = re.compile(r"[.!?]+")
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF]")


def measure_style(text: str) -> dict[str, float]:
    words = WORD_RE.findall(text)
    sentences = max(len(SENTENCE_RE.findall(text)), 1)
    lines = [line for line in text.splitlines() if line.strip()]
    bullets = sum(line.lstrip().startswith(("- ", "* ", "• ")) for line in lines)
    return {
        "word_count": float(len(words)),
        "sentence_words": round(len(words) / sentences, 3),
        "question_rate": round(text.count("?") / sentences, 3),
        "exclamation_rate": round(text.count("!") / sentences, 3),
        "bullet_rate": round(bullets / max(len(lines), 1), 3),
        "emoji_rate": round(len(EMOJI_RE.findall(text)) / max(len(words), 1), 3),
    }


def style_instructions(metrics: dict[str, float], samples: int, minimum: int = 3) -> list[str]:
    if samples < minimum:
        return []
    instructions = []
    words = metrics.get("word_count", 0)
    sentence_words = metrics.get("sentence_words", 0)
    if words <= 18 and sentence_words <= 14:
        instructions.append("Match the user's compact, direct writing cadence.")
    elif words >= 70 or sentence_words >= 24:
        instructions.append("The user tends to write expansively; allow fuller explanations.")
    if metrics.get("bullet_rate", 0) >= 0.25:
        instructions.append("Use scannable bullets when they clarify the answer.")
    if metrics.get("question_rate", 0) >= 0.5:
        instructions.append("Answer the central question before adding background.")
    if metrics.get("emoji_rate", 0) >= 0.025:
        instructions.append("Occasional restrained emoji are compatible with the user's style.")
    else:
        instructions.append("Avoid decorative emoji unless the user requests them.")
    return instructions


class StyleLearningAgent:
    """Learns only observable writing mechanics, never identity or sensitive traits."""

    def __init__(self, minimum_samples: int = 3):
        self.minimum_samples = minimum_samples

    def observe(self, db: Session, user_id: str, text: str) -> StyleProfile:
        observed = measure_style(text)
        profile = db.get(StyleProfile, user_id) or StyleProfile(user_id=user_id)
        old_count = profile.sample_count or 0
        new_count = old_count + 1
        current = profile.metrics or {}
        profile.metrics = {
            key: round((float(current.get(key, 0)) * old_count + value) / new_count, 4)
            for key, value in observed.items()
        }
        profile.sample_count = new_count
        profile.version = (profile.version or 0) + 1 if old_count else 1
        profile.instructions = style_instructions(
            profile.metrics, new_count, self.minimum_samples
        )
        profile.updated_at = utcnow()
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
