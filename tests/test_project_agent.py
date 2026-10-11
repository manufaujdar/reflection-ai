import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "tools" / "project_agent" / "review_agent.py"


def load_agent():
    spec = importlib.util.spec_from_file_location("reflection_project_agent", AGENT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_repository_audit_has_no_high_severity_findings():
    report = load_agent().audit_repository(ROOT)
    high = [item for item in report["findings"] if item["severity"] == "high"]
    assert high == []
    assert report["external_model_calls"] is False


def test_repository_audit_cli_returns_json():
    result = subprocess.run(
        [sys.executable, str(AGENT), "audit", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["tool"] == "reflection-ai-project-review-agent"


def test_console_keeps_accessibility_and_security_boundaries():
    html = load_agent()._console_html(ROOT)
    assert ":focus-visible" in html
    assert "aria-live" in html
    assert "textContent" in html
    assert "innerHTML" not in html
    assert "Not production-ready" in html


def test_chat_frontend_keeps_accessibility_security_and_truth_boundaries():
    html = (ROOT / "src/reflection_ai/frontend/chat.html").read_text()
    css = (ROOT / "src/reflection_ai/frontend/chat.css").read_text()
    javascript = (ROOT / "src/reflection_ai/frontend/chat.js").read_text()
    assert "aria-live" in html
    assert "no authentication or encryption" in html
    assert ":focus-visible" in css
    assert "@media" in css
    assert "textContent" in javascript
    assert "innerHTML" not in javascript
