#!/usr/bin/env python3
"""Validate the repository-local Reflection AI delivery-team contracts."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
TEAM_FILE = ROOT / ".ai" / "TEAM.md"

EXPECTED_SKILLS = {
    "reflection-plan",
    "reflection-build",
    "reflection-engineer",
    "reflection-review",
    "reflection-qa",
    "reflection-release",
    "reflection-document",
    "reflection-research",
    "reflection-market",
    "reflection-design",
    "reflection-privacy",
    "reflection-evaluate",
    "reflection-security",
    "reflection-retro",
}

REPORT_ONLY = {
    "reflection-plan",
    "reflection-engineer",
    "reflection-review",
    "reflection-qa",
    "reflection-research",
    "reflection-market",
    "reflection-design",
    "reflection-privacy",
    "reflection-evaluate",
    "reflection-security",
}

COMMAND_GATED = {
    "reflection-build",
    "reflection-qa",
    "reflection-release",
    "reflection-document",
}

ROLE_TERMS = {
    "reflection-build": ("consent", "isolation", "deletion", "rollback"),
    "reflection-privacy": ("consent", "isolation", "deletion", "provenance"),
    "reflection-security": ("authentication", "authorization", "isolation", "deletion"),
    "reflection-evaluate": ("candidate", "incumbent", "rollback", "consent"),
    "reflection-release": ("candidate", "incumbent", "rollback", "consent"),
    "reflection-market": ("unsupported claims", "real user data"),
    "reflection-research": ("license", "provenance", "real user data"),
}


@dataclass(frozen=True)
class Skill:
    folder: str
    name: str
    description: str
    body: str
    ui: dict[str, str]


def _frontmatter(text: str, path: Path) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\n(?P<header>.*?)\n---\n(?P<body>.*)\Z", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    fields: dict[str, str] = {}
    for line in match.group("header").splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"{path}: malformed frontmatter line: {line!r}")
        fields[key.strip()] = value.strip()
    return fields, match.group("body")


def _ui_metadata(text: str, path: Path) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "interface:":
        raise ValueError(f"{path}: UI metadata must start with an interface mapping")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        match = re.fullmatch(r'  ([a-z_]+): "([^"]+)"', line)
        if not match:
            raise ValueError(f"{path}: malformed UI metadata line: {line!r}")
        key, value = match.groups()
        if key in fields:
            raise ValueError(f"{path}: duplicate UI metadata field {key!r}")
        fields[key] = value
    expected = {"display_name", "short_description", "default_prompt"}
    if set(fields) != expected:
        raise ValueError(f"{path}: UI metadata fields must be {sorted(expected)}")
    return fields


def load_skills() -> list[Skill]:
    skills: list[Skill] = []
    if not SKILLS_ROOT.is_dir():
        raise ValueError(f"missing skills directory: {SKILLS_ROOT}")
    for folder in sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir()):
        skill_path = folder / "SKILL.md"
        ui_path = folder / "agents" / "openai.yaml"
        if not skill_path.is_file():
            raise ValueError(f"{folder}: missing SKILL.md")
        if not ui_path.is_file():
            raise ValueError(f"{folder}: missing agents/openai.yaml")
        fields, body = _frontmatter(skill_path.read_text(), skill_path)
        if set(fields) != {"name", "description"}:
            raise ValueError(f"{skill_path}: frontmatter must contain only name and description")
        ui = _ui_metadata(ui_path.read_text(), ui_path)
        skills.append(Skill(folder.name, fields["name"], fields["description"], body, ui))
    return skills


def validate() -> list[str]:
    errors: list[str] = []
    try:
        skills = load_skills()
    except ValueError as exc:
        return [str(exc)]

    found = {skill.name for skill in skills}
    missing = sorted(EXPECTED_SKILLS - found)
    extra = sorted(found - EXPECTED_SKILLS)
    if missing:
        errors.append(f"missing expected skills: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected skills: {', '.join(extra)}")
    if len(found) != len(skills):
        errors.append("skill names must be unique")

    team = TEAM_FILE.read_text() if TEAM_FILE.is_file() else ""
    for expected in sorted(EXPECTED_SKILLS):
        if f"`{expected}`" not in team:
            errors.append(f"{TEAM_FILE}: roster does not reference {expected}")

    for skill in skills:
        label = str(SKILLS_ROOT / skill.folder)
        lower = re.sub(r"\s+", " ", f"{skill.description}\n{skill.body}".lower())
        if skill.name != skill.folder:
            errors.append(f"{label}: folder and frontmatter name differ")
        if not re.fullmatch(r"[a-z0-9-]{1,63}", skill.name):
            errors.append(f"{label}: invalid skill name")
        if len(skill.description) < 80 or "use " not in skill.description.lower():
            errors.append(f"{label}: description must explain purpose and trigger")
        if "todo" in lower or "[placeholder" in lower:
            errors.append(f"{label}: unresolved template marker")
        for reference in ("`AGENTS.md`", "`.ai/TEAM.md`", "`.ai/HANDOFF.md`"):
            if reference not in skill.body:
                errors.append(f"{label}: missing reference to {reference}")
        if "shared invariant" not in lower or "release-blocking" not in lower:
            errors.append(f"{label}: must make the shared invariant release-blocking")
        if skill.name in REPORT_ONLY and "report-only" not in lower:
            errors.append(f"{label}: report-only role must prohibit edits")
        if skill.name in COMMAND_GATED:
            for command in ("pytest", "ruff check ."):
                if command not in lower:
                    errors.append(f"{label}: missing required command {command!r}")
        for term in ROLE_TERMS.get(skill.name, ()):
            if term not in lower:
                errors.append(f"{label}: missing role safety term {term!r}")
        if not 25 <= len(skill.ui["short_description"]) <= 64:
            errors.append(f"{label}: short_description must be 25-64 characters")
        if f"${skill.name}" not in skill.ui["default_prompt"]:
            errors.append(f"{label}: default prompt must invoke ${skill.name}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Team validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Team validation passed: {len(EXPECTED_SKILLS)} skills and roster are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
