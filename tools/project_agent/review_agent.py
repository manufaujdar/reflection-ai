#!/usr/bin/env python3
"""Local deterministic release, trust, and UI audit for Reflection AI."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FILES = (
    "LICENSE",
    "NOTICE",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "GOVERNANCE.md",
    "COMPLIANCE_AND_DEPLOYMENT.md",
    "PROVENANCE.md",
    "VALIDATION_PROTOCOL.md",
    "MODEL_CARD_TEMPLATE.md",
    "DATASET_CARD_TEMPLATE.md",
    "THIRD_PARTY_NOTICES.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    "src/reflection_ai/frontend/chat.html",
    "src/reflection_ai/frontend/chat.css",
    "src/reflection_ai/frontend/chat.js",
    "docs/adaptive-chatbot.md",
)
FORBIDDEN_TRACKED_SUFFIXES = (
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pem",
    ".key",
    ".p12",
    ".pt",
    ".pth",
    ".safetensors",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    area: str
    title: str
    detail: str
    next_action: str


class ConsoleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.labels_for: set[str] = set()
        self.control_ids: set[str] = set()
        self.buttons = 0
        self.details = 0
        self.live_regions = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "label" and attributes.get("for"):
            self.labels_for.add(str(attributes["for"]))
        if tag in {"input", "textarea", "select"} and attributes.get("id"):
            self.control_ids.add(str(attributes["id"]))
        if tag == "button":
            self.buttons += 1
        if tag == "details":
            self.details += 1
        if attributes.get("aria-live") or attributes.get("role") == "status":
            self.live_regions += 1


def _console_html(root: Path) -> str:
    path = root / "src" / "reflection_ai" / "web_ui.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "CONSOLE_HTML"
                for target in node.targets
            ):
                value = ast.literal_eval(node.value)
                if isinstance(value, str):
                    return value
    raise ValueError("CONSOLE_HTML string not found")


def _tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def audit_repository(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    findings: list[Finding] = []
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    if missing:
        findings.append(
            Finding(
                "high",
                "governance",
                "Required public-project files are missing",
                ", ".join(missing),
                "Add and review each missing governance or release file.",
            )
        )

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    if 'license = { file = "LICENSE" }' not in pyproject:
        findings.append(
            Finding(
                "high",
                "licensing",
                "Package metadata does not declare the repository license",
                "A LICENSE file alone is not enough for generated package metadata.",
                "Declare the Apache-2.0 license file in pyproject.toml.",
            )
        )

    readme = (root / "README.md").read_text(encoding="utf-8").lower()
    required_boundaries = {
        "not production": "Production-readiness limitation is missing",
        "consent": "Consent boundary is missing",
        "deletion": "Deletion boundary is missing",
        "rollback": "Rollback boundary is missing",
        "synthetic": "Synthetic-only development guidance is missing",
    }
    for term, title in required_boundaries.items():
        if term not in readme:
            findings.append(
                Finding(
                    "high",
                    "truthfulness",
                    title,
                    f"README.md does not contain the expected boundary term {term!r}.",
                    "Document the boundary in the project overview and quick start.",
                )
            )

    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for signal, title in {
        "permissions:\n  contents: read": "CI does not declare least-privilege permissions",
        "persist-credentials: false": "Checkout credentials remain persisted",
        "review_agent.py audit --json": "Deterministic repository audit is absent from CI",
        "compileall": "Python compilation check is absent from CI",
    }.items():
        if signal not in workflow:
            findings.append(
                Finding(
                    "medium",
                    "automation",
                    title,
                    f"Expected CI signal not found: {signal!r}.",
                    "Add the check to the least-privilege CI workflow.",
                )
            )

    tracked = _tracked_files(root)
    unsafe = sorted(path for path in tracked if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES))
    if unsafe:
        findings.append(
            Finding(
                "high",
                "privacy",
                "Sensitive artifact types are tracked",
                ", ".join(unsafe),
                "Remove the artifacts from version control and rotate secrets if necessary.",
            )
        )

    console = _console_html(root)
    parser = ConsoleParser()
    parser.feed(console)
    ui_checks = {
        '<meta name="viewport"': ("high", "responsive", "Viewport metadata is missing"),
        ":focus-visible": ("medium", "accessibility", "Visible keyboard focus styling is missing"),
        "aria-live": ("medium", "accessibility", "Async result announcements are missing"),
        "Not production-ready": ("high", "truthfulness", "Local-console risk warning is missing"),
        "@media": ("medium", "responsive", "Mobile layout rules are missing"),
        "textContent": ("high", "security", "Safe text rendering boundary is missing"),
    }
    for signal, (severity, area, title) in ui_checks.items():
        if signal not in console:
            findings.append(
                Finding(
                    severity,
                    area,
                    title,
                    f"The console does not contain {signal!r}.",
                    "Update the local console and preserve its synthetic-only boundary.",
                )
            )
    if "innerHTML" in console:
        findings.append(
            Finding(
                "high",
                "security",
                "Console uses dynamic innerHTML",
                "Untrusted API values could become executable markup.",
                "Render API values with textContent only.",
            )
        )

    chat_html = (root / "src" / "reflection_ai" / "frontend" / "chat.html").read_text(
        encoding="utf-8"
    )
    chat_css = (root / "src" / "reflection_ai" / "frontend" / "chat.css").read_text(
        encoding="utf-8"
    )
    chat_js = (root / "src" / "reflection_ai" / "frontend" / "chat.js").read_text(
        encoding="utf-8"
    )
    chat_checks = {
        '<meta name="viewport"': ("high", "responsive", "Chat viewport metadata is missing"),
        "aria-live": ("medium", "accessibility", "Chat announcements are missing"),
        "no authentication or encryption": (
            "high",
            "truthfulness",
            "Chat research-mode disclosure is missing",
        ),
        "textContent": ("high", "security", "Chat safe rendering boundary is missing"),
        ":focus-visible": ("medium", "accessibility", "Chat keyboard focus is not visible"),
        "@media": ("medium", "responsive", "Chat mobile layout rules are missing"),
    }
    chat_bundle = chat_html + chat_css + chat_js
    for signal, (severity, area, title) in chat_checks.items():
        if signal not in chat_bundle:
            findings.append(
                Finding(
                    severity,
                    area,
                    title,
                    f"The adaptive chat frontend does not contain {signal!r}.",
                    "Update the chat frontend while preserving its local research boundary.",
                )
            )
    if "innerHTML" in chat_js:
        findings.append(
            Finding(
                "high",
                "security",
                "Chat uses dynamic innerHTML",
                "Conversation or inspector values could become executable markup.",
                "Build dynamic nodes and assign untrusted values with textContent.",
            )
        )
    unlabeled = sorted(parser.control_ids - parser.labels_for)
    if unlabeled:
        findings.append(
            Finding(
                "medium",
                "accessibility",
                "Form controls lack matching labels",
                ", ".join(unlabeled),
                "Add explicit label elements using matching for/id values.",
            )
        )

    severity_deductions = {"high": 3, "medium": 2, "low": 1}
    scores = {
        "governance": 10,
        "privacy": 10,
        "security": 10,
        "truthfulness": 10,
        "automation": 10,
        "accessibility": 10,
        "responsive": 10,
        "maintainability": 9,
    }
    for finding in findings:
        if finding.area in scores:
            scores[finding.area] = max(
                0, scores[finding.area] - severity_deductions[finding.severity]
            )
    return {
        "tool": "reflection-ai-project-review-agent",
        "mode": "local_deterministic_audit",
        "root": str(root),
        "files_reviewed": list(REQUIRED_FILES) + ["README.md", "pyproject.toml"],
        "signals": {
            "tracked_files": len(tracked),
            "console_buttons": parser.buttons,
            "console_disclosures": parser.details,
            "console_live_regions": parser.live_regions,
            "console_controls": sorted(parser.control_ids),
            "chat_frontend_files": 3,
        },
        "scores": scores,
        "findings": [asdict(finding) for finding in findings],
        "external_model_calls": False,
        "release_ready": not any(item.severity == "high" for item in findings),
        "limitations": [
            "not a penetration test or accessibility certification",
            "does not establish privacy, legal, or production compliance",
            "does not evaluate model quality or inspect external services",
        ],
    }


def _print_human(report: dict[str, Any]) -> None:
    print(f"Reflection AI project audit: {report['root']}")
    print(f"Release-ready hygiene gate: {report['release_ready']}")
    for area, score in report["scores"].items():
        print(f"- {area}: {score}/10")
    if not report["findings"]:
        print("No deterministic findings.")
    for finding in report["findings"]:
        print(f"[{finding['severity']}] {finding['area']}: {finding['title']}")
        print(f"  {finding['detail']}")
        print(f"  Next: {finding['next_action']}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Reflection AI release hygiene.")
    parser.add_argument("command", choices=("audit",))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    report = audit_repository(args.root.resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0 if report["release_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
