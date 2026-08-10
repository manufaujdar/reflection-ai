from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


REPOSITORIES = {
    "mem0": "https://github.com/mem0ai/mem0",
    "letta": "https://github.com/letta-ai/letta",
    "hindsight": "https://github.com/vectorize-io/hindsight",
    "graphiti": "https://github.com/getzep/graphiti",
    "supermemory": "https://github.com/supermemoryai/supermemory",
    "langmem": "https://github.com/langchain-ai/langmem",
    "khoj": "https://github.com/khoj-ai/khoj",
    "lamp": "https://github.com/LaMP-Benchmark/LaMP",
}

SOURCE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html", ".java",
    ".js", ".jsx", ".kt", ".kts", ".mjs", ".php", ".py", ".rb", ".rs", ".scala",
    ".sh", ".sql", ".svelte", ".swift", ".ts", ".tsx", ".vue",
}
TEXT_EXTENSIONS = SOURCE_EXTENSIONS | {
    ".cfg", ".conf", ".csv", ".env", ".ini", ".json", ".md", ".rst", ".toml",
    ".txt", ".xml", ".yaml", ".yml",
}
KEYWORDS = {
    "memory", "personal", "persona", "profile", "preference", "feedback", "reflect",
    "retriev", "rerank", "embedding", "temporal", "contradict", "consolidat", "forget",
    "evaluation", "benchmark", "consent", "privacy", "identity", "training", "lora",
}
SYMBOL_PATTERNS = {
    "python": re.compile(r"^\s*(?:async\s+)?(def|class)\s+([A-Za-z_]\w*)"),
    "javascript": re.compile(
        r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?"
        r"(function|class|interface|type|enum|const)\s+([A-Za-z_$][\w$]*)"
    ),
    "go": re.compile(r"^\s*(func|type)\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)"),
    "rust": re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(fn|struct|enum|trait)\s+([A-Za-z_]\w*)"),
    "sql": re.compile(r"^\s*(CREATE\s+(?:TABLE|FUNCTION|VIEW|TYPE))\s+([^\s(]+)", re.I),
}


@dataclass
class FileRecord:
    path: str
    extension: str
    kind: str
    bytes: int
    lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    sha256: str


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def tracked_files(repo: Path) -> list[str]:
    raw = subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"])
    return [item.decode("utf-8", "surrogateescape") for item in raw.split(b"\0") if item]


def kind_for(path: Path) -> str:
    lowered = str(path).lower()
    if any(part in lowered for part in ("/test", "tests/", "__tests__", "/spec")):
        return "test"
    if any(part in lowered for part in ("generated", "dist/", "build/", "vendor/")):
        return "generated_or_vendor"
    if path.suffix.lower() in SOURCE_EXTENSIONS:
        return "source"
    if path.suffix.lower() in {".md", ".rst", ".txt"}:
        return "documentation"
    if path.suffix.lower() in {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".conf"}:
        return "configuration"
    return "asset_or_other"


def line_stats(text: str) -> tuple[int, int, int, int]:
    lines = text.splitlines()
    blank = comment = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith(("#", "//", "/*", "*", "<!--", "-- ")):
            comment += 1
    return len(lines), len(lines) - blank - comment, comment, blank


def language_for(suffix: str) -> str | None:
    if suffix == ".py":
        return "python"
    if suffix in {".js", ".jsx", ".mjs", ".ts", ".tsx"}:
        return "javascript"
    if suffix == ".go":
        return "go"
    if suffix == ".rs":
        return "rust"
    if suffix == ".sql":
        return "sql"
    return None


def write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def line_kind(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "blank"
    if stripped.startswith(("#", "//", "/*", "*", "<!--", "-- ")):
        return "comment"
    return "content"


def generate(repo_name: str, repo: Path, output_root: Path) -> None:
    output = output_root / "repos" / repo_name
    output.mkdir(parents=True, exist_ok=True)
    records: list[FileRecord] = []
    symbols: list[dict] = []
    relevant: list[dict] = []
    directories: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "bytes": 0, "lines": 0, "code_lines": 0}
    )
    line_handle = gzip.open(output / "line_index.tsv.gz", "wt", encoding="utf-8", newline="")
    line_writer = csv.DictWriter(
        line_handle,
        fieldnames=["path", "line", "kind", "bytes", "sha256"],
        delimiter="\t",
    )
    line_writer.writeheader()

    for relative in tracked_files(repo):
        source = repo / relative
        try:
            data = source.read_bytes()
        except OSError:
            continue
        suffix = source.suffix.lower()
        text = ""
        is_text = suffix in TEXT_EXTENSIONS or b"\0" not in data[:8192]
        if is_text:
            text = data.decode("utf-8", "replace")
            lines, code, comments, blank = line_stats(text)
            for line_number, line in enumerate(text.splitlines(), start=1):
                encoded_line = line.encode("utf-8")
                line_writer.writerow(
                    {
                        "path": relative,
                        "line": line_number,
                        "kind": line_kind(line),
                        "bytes": len(encoded_line),
                        "sha256": hashlib.sha256(encoded_line).hexdigest(),
                    }
                )
        else:
            lines = code = comments = blank = 0
        record = FileRecord(
            path=relative,
            extension=suffix,
            kind=kind_for(Path(relative)),
            bytes=len(data),
            lines=lines,
            code_lines=code,
            comment_lines=comments,
            blank_lines=blank,
            sha256=hashlib.sha256(data).hexdigest(),
        )
        records.append(record)

        parents = ["."]
        parent = Path(relative).parent
        if str(parent) != ".":
            parents.extend(str(Path(*parent.parts[:index])) for index in range(1, len(parent.parts) + 1))
        for directory in parents:
            summary = directories[directory]
            summary["files"] += 1
            summary["bytes"] += record.bytes
            summary["lines"] += record.lines
            summary["code_lines"] += record.code_lines

        lowered = relative.lower()
        matches = sorted(keyword for keyword in KEYWORDS if keyword in lowered)
        if matches:
            relevant.append({"path": relative, "matched_terms": ",".join(matches), "lines": lines})

        language = language_for(suffix)
        pattern = SYMBOL_PATTERNS.get(language or "")
        if pattern and text:
            for line_number, line in enumerate(text.splitlines(), start=1):
                match = pattern.match(line)
                if match:
                    symbols.append(
                        {
                            "path": relative,
                            "line": line_number,
                            "kind": match.group(1),
                            "name": match.group(2),
                        }
                    )

    write_tsv(output / "manifest.tsv", [asdict(record) for record in records], list(asdict(records[0]).keys()))
    write_tsv(output / "symbols.tsv", symbols, ["path", "line", "kind", "name"])
    write_tsv(output / "relevant_files.tsv", relevant, ["path", "matched_terms", "lines"])
    directory_rows = [
        {"directory": directory, **values}
        for directory, values in sorted(directories.items())
    ]
    write_tsv(
        output / "directory_summary.tsv",
        directory_rows,
        ["directory", "files", "bytes", "lines", "code_lines"],
    )
    line_handle.close()
    metadata = {
        "name": repo_name,
        "repository": REPOSITORIES[repo_name],
        "commit": git(repo, "rev-parse", "HEAD"),
        "branch": git(repo, "branch", "--show-current"),
        "commit_date": git(repo, "show", "-s", "--format=%cI", "HEAD"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tracked_files": len(records),
        "text_lines": sum(record.lines for record in records),
        "approximate_code_lines": sum(record.code_lines for record in records),
        "bytes": sum(record.bytes for record in records),
        "symbols": len(symbols),
        "relevant_paths": len(relevant),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    for name in REPOSITORIES:
        repo = args.sources / name
        if not (repo / ".git").exists():
            raise SystemExit(f"Missing clone: {repo}")
        generate(name, repo, args.output)


if __name__ == "__main__":
    main()
