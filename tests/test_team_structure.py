import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "validate_team.py"
    spec = importlib.util.spec_from_file_location("validate_team", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_team_contracts_are_valid():
    result = subprocess.run(
        [sys.executable, "scripts/validate_team.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_handoff_records_trust_and_rollback_contract():
    handoff = (ROOT / ".ai" / "HANDOFF.md").read_text().lower()
    for term in ("consent", "isolation", "deletion", "provenance", "evaluation", "rollback"):
        assert term in handoff


def test_human_entrypoints_link_the_team_system():
    assert "docs/agent-team.md" in (ROOT / "README.md").read_text()
    assert "docs/agent-team.md" in (ROOT / "START_HERE.txt").read_text()


def test_validator_rejects_extra_frontmatter_fields():
    validator = load_validator()
    with pytest.raises(ValueError, match="malformed frontmatter line"):
        validator._frontmatter("---\nname: valid\nbroken\n---\nbody", Path("SKILL.md"))


def test_validator_rejects_malformed_ui_metadata():
    validator = load_validator()
    with pytest.raises(ValueError, match="malformed UI metadata"):
        validator._ui_metadata(
            'interface:\n  display_name: "Valid"\n default_prompt: "$valid"',
            Path("openai.yaml"),
        )
