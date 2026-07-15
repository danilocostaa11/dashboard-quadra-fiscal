#!/usr/bin/env python3
"""Check whether a project has the expected Fable Harness closure surface."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from memory_policy import critical_closure_failures


REQUIRED_TEMPLATES = [
    "decision-trace.md",
    "semantic-note.md",
    "subagent-brief.md",
    "memory-closure.md",
    "workflow-profile.md",
]

REQUIRED_MEMORY_SCRIPTS = [
    "memory_policy.py",
    "memory_core.py",
    "new-note.py",
    "promote-trace.py",
    "memory-search.py",
    "rebuild-memory.py",
    "rag-eval.py",
    "rag-pipeline.py",
    "source-arbitrate.py",
    "graph-query.py",
    "graph-check.py",
    "code_graph_core.py",
    "code-graph-build.py",
    "code-graph-query.py",
    "code-graph-check.py",
    "release-notice.py",
    "workflow_core.py",
    "subagent-plan.py",
    "subagent-result.py",
    "subagent-sweep.py",
    "selective-revert.py",
    "memory-maintenance.py",
    "memory-touch.py",
    "memory-dream.py",
    "loop_core.py",
    "loop-start.py",
    "loop-event.py",
    "loop-transition.py",
    "loop-check.py",
]


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def instruction_file_for(local_dir: Path) -> str:
    if local_dir.name == ".claude":
        return "CLAUDE.md"
    return "AGENTS.md"


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def section(text: str, names: tuple[str, ...]) -> str:
    wanted = {name.lower() for name in names}
    current: str | None = None
    chunks: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            continue
        if current in wanted:
            chunks.append(line)
    return "\n".join(chunks).strip()


def meaningful(text: str) -> str:
    ignored = {
        "",
        "-",
        "- none",
        "none",
        "n/a",
        "na",
        "not applicable",
        "not recorded",
        "todo",
        "tbd",
    }
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower() in ignored:
            continue
        if stripped.startswith("|") or stripped.startswith("```"):
            continue
        lines.append(stripped)
    return "\n".join(lines).strip()


def trace_needs_promotion(text: str) -> bool:
    decision = section(text, ("Decide", "Decision", "Decisions", "Durable Decision", "Chosen Approach"))
    return bool(meaningful(decision))


def source_lines(text: str) -> list[str]:
    sources: list[str] = []
    in_sources = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("sources:"):
            in_sources = True
            continue
        if in_sources:
            if stripped.startswith("- "):
                value = stripped[2:].strip().strip("`").strip()
                if value:
                    sources.append(value)
                continue
            if stripped and not line.startswith(" "):
                break
    return sources


def source_points_to_trace(source: str, note: Path, root: Path, local_dir: Path, trace: Path) -> bool:
    normalized = source.replace("\\", "/").strip()
    exact = {
        trace.name,
        relpath(trace, root),
        relpath(trace, local_dir),
    }
    if normalized in exact:
        return True
    candidate = Path(source)
    if not candidate.is_absolute():
        candidate = (note.parent / candidate).resolve()
    return candidate == trace


def trace_is_promoted(root: Path, local_dir: Path, trace_path: Path) -> bool:
    trace = trace_path.resolve()
    candidates = {
        trace.name,
        relpath(trace, root),
        relpath(trace, local_dir),
    }

    log_path = local_dir / "memory" / "promotion_log.jsonl"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(item.get("trace", "")).replace("\\", "/") in candidates:
                return True

    notes = local_dir / "notes"
    if notes.exists():
        for note in notes.rglob("*.md"):
            if note.name == "_index.md":
                continue
            text = note.read_text(encoding="utf-8")
            if any(source_points_to_trace(source, note, root, local_dir, trace) for source in source_lines(text)):
                return True

    return False


def append_trace_promotion_failures(root: Path, local_dir: Path, trace_arg: str, missing: list[str]) -> None:
    trace_path = Path(trace_arg)
    if not trace_path.is_absolute():
        trace_path = root / trace_path
    trace_path = trace_path.resolve()
    if not trace_path.exists():
        return
    text = trace_path.read_text(encoding="utf-8")
    if trace_needs_promotion(text) and not trace_is_promoted(root, local_dir, trace_path):
        command = (
            f"{local_dir / 'scripts' / 'promote-trace.py'} --root {root} "
            f"--trace {trace_path} --category decisions --area workflow --topic <topic>"
        )
        missing.append(
            f"{trace_path}: durable trace evidence was not promoted. Run: {command}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fable Harness closure files.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--trace", help="Decision trace file expected to exist.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    missing = []

    instruction = instruction_file_for(local_dir)
    instruction_path = root / instruction
    if not instruction_path.exists():
        missing.append(str(instruction_path))
    elif "fable-harness:start" not in instruction_path.read_text(encoding="utf-8"):
        missing.append(f"{instruction_path} missing fable-harness block")

    for name in REQUIRED_TEMPLATES:
        path = local_dir / "templates" / name
        if not path.exists():
            missing.append(str(path))

    for path in [
        local_dir / "scripts" / "new-trace.py",
        local_dir / "scripts" / "check-closure.py",
        *[local_dir / "scripts" / name for name in REQUIRED_MEMORY_SCRIPTS],
        local_dir / "notes" / "_index.md",
        local_dir / "decision-traces" / "_index.md",
        local_dir / "memory" / "manifest.json",
    ]:
        if not path.exists():
            missing.append(str(path))

    if args.trace:
        trace_path = Path(args.trace)
        if not trace_path.is_absolute():
            trace_path = root / trace_path
        if not trace_path.exists():
            missing.append(args.trace)
        else:
            append_trace_promotion_failures(root, local_dir, str(trace_path), missing)
            for item in critical_closure_failures(root, local_dir, trace_path.resolve()):
                missing.append(f"{item['path']}: {item['reason']}")
    else:
        for item in critical_closure_failures(root, local_dir):
            missing.append(f"{item['path']}: {item['reason']}")

    if missing:
        print("Fable Harness closure check failed:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("Fable Harness closure check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
