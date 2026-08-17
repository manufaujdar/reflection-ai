from dataclasses import dataclass


@dataclass(frozen=True)
class OnboardingQuestion:
    id: str
    prompt: str
    answer_type: str
    options: tuple[str, ...]
    memory_type: str
    normalized_key: str
    template: str
    sensitivity: str = "normal"


QUESTIONS = (
    OnboardingQuestion(
        "display_name",
        "What should I call you here? A nickname is enough, and you may skip this.",
        "text",
        (),
        "fact",
        "preferred-display-name",
        "Address the user as {answer}",
        "sensitive",
    ),
    OnboardingQuestion(
        "response_depth",
        "How much detail do you usually want?",
        "choice",
        ("Concise", "Balanced", "Detailed"),
        "preference",
        "preferred-response-depth",
        "Prefer {answer} responses",
    ),
    OnboardingQuestion(
        "tone",
        "Which tone feels most natural to you?",
        "choice",
        ("Direct", "Warm", "Professional", "Casual"),
        "preference",
        "preferred-tone",
        "Use a {answer} tone",
    ),
    OnboardingQuestion(
        "format",
        "How should I organize information?",
        "choice",
        ("Short paragraphs", "Bullets", "Numbered steps", "A mix"),
        "preference",
        "preferred-information-format",
        "Prefer {answer} when organizing information",
    ),
    OnboardingQuestion(
        "examples",
        "When should I include examples?",
        "choice",
        ("Only when asked", "When helpful", "Often"),
        "behavior_rule",
        "preferred-example-frequency",
        "Include examples {answer}",
    ),
    OnboardingQuestion(
        "current_goal",
        "What are you mainly hoping this assistant will help with right now?",
        "text",
        (),
        "goal",
        "current-assistant-goal",
        "Current assistant goal: {answer}",
    ),
    OnboardingQuestion(
        "boundaries",
        "Any response habits or topics you want me to avoid? You may skip this.",
        "text",
        (),
        "behavior_rule",
        "user-stated-boundaries",
        "Respect this user-stated boundary: {answer}",
        "sensitive",
    ),
)


def question_at(index: int) -> OnboardingQuestion | None:
    return QUESTIONS[index] if 0 <= index < len(QUESTIONS) else None
