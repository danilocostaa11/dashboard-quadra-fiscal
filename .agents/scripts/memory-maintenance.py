#!/usr/bin/env python3
"""Report memory growth and retrieval-maintenance candidates without deleting source files."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from memory_core import file_title, find_local_dir, relpath, source_lines
from memory_policy import has_high_severity, policy_candidates


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def frontmatter_value(text: str, key: str) -> str | None:
    in_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not in_frontmatter:
            in_frontmatter = True
            continue
        if stripped == "---" and in_frontmatter:
            break
        if in_frontmatter and stripped.startswith(f"{key}:"):
            return stripped.split(":", 1)[1].strip()
    return None


def resolve_source(note: Path, source: str) -> Path:
    path = Path(source.strip().strip("`"))
    if not path.is_absolute():
        path = note.parent / path
    return path.resolve()


def promoted_traces(root: Path, local_dir: Path) -> set[str]:
    traces: set[str] = set()
    log = local_dir / "memory" / "promotion_log.jsonl"
    if not log.exists():
        return traces
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        trace = str(item.get("trace", "")).replace("\\", "/")
        if trace:
            traces.add(trace)
            traces.add(Path(trace).name)
    return traces


def add_candidate(candidates: list[dict[str, object]], action: str, path: Path, root: Path, reason: str, size: int | None = None) -> None:
    item: dict[str, object] = {
        "action": action,
        "path": relpath(path, root),
        "reason": reason,
    }
    if size is not None:
        item["bytes"] = size
    candidates.append(item)


def build_report(root: Path, agent: str, max_note_bytes: int, max_trace_bytes: int, stale_days: int) -> dict[str, object]:
    local_dir = find_local_dir(root, agent)
    today = dt.date.today()
    candidates: list[dict[str, object]] = []
    note_count = 0
    trace_count = 0
    note_bytes = 0
    trace_bytes = 0

    notes = local_dir / "notes"
    if notes.exists():
        for note in sorted(notes.rglob("*.md")):
            if note.name == "_index.md":
                continue
            note_count += 1
            size = note.stat().st_size
            note_bytes += size
            text = note.read_text(encoding="utf-8")
            if size > max_note_bytes:
                add_candidate(candidates, "compact-note", note, root, f"note exceeds {max_note_bytes} bytes", size)
            verified = frontmatter_value(text, "last_verified")
            verified_date = parse_date(verified or "")
            if verified_date and (today - verified_date).days > stale_days:
                add_candidate(candidates, "revalidate-note", note, root, f"last_verified is older than {stale_days} days")
            for source in source_lines(text):
                if not resolve_source(note, source).exists():
                    add_candidate(candidates, "repair-source", note, root, f"missing source: {source}")

    promoted = promoted_traces(root, local_dir)
    traces = local_dir / "decision-traces"
    if traces.exists():
        for trace in sorted(traces.rglob("*.md")):
            if trace.name == "_index.md":
                continue
            trace_count += 1
            size = trace.stat().st_size
            trace_bytes += size
            rel = relpath(trace, root)
            if size > max_trace_bytes:
                add_candidate(candidates, "summarize-trace", trace, root, f"trace exceeds {max_trace_bytes} bytes", size)
            if rel in promoted or trace.name in promoted:
                add_candidate(candidates, "archive-promoted-trace", trace, root, "trace has promotion-log evidence; keep audit path but remove it from routine retrieval when ready")

    candidates.extend(policy_candidates(root, local_dir, max_trace_bytes=max_trace_bytes))

    manifest_path = local_dir / "memory" / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {"error": "manifest is not valid JSON"}

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": {
            "max_note_bytes": max_note_bytes,
            "max_trace_bytes": max_trace_bytes,
            "stale_days": stale_days,
            "mode": "report-only",
        },
        "counts": {
            "notes": note_count,
            "traces": trace_count,
            "note_bytes": note_bytes,
            "trace_bytes": trace_bytes,
            "memory_documents": manifest.get("document_count"),
            "memory_shards": len(manifest.get("shards", [])) if isinstance(manifest.get("shards"), list) else None,
        },
        "candidates": candidates,
    }


def write_report(root: Path, local_dir: Path, report: dict[str, object]) -> None:
    out = local_dir / "memory" / "maintenance"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Memory Maintenance Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Counts",
        "",
    ]
    counts = report["counts"]
    assert isinstance(counts, dict)
    for key, value in counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Candidates", ""])
    candidates = report["candidates"]
    assert isinstance(candidates, list)
    if not candidates:
        lines.append("- none")
    else:
        for item in candidates:
            assert isinstance(item, dict)
            lines.append(f"- {item['action']}: `{item['path']}` - {item['reason']}")
    (out / "latest-report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report memory maintenance candidates.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--max-note-bytes", type=int, default=8192)
    parser.add_argument("--max-trace-bytes", type=int, default=24576)
    parser.add_argument("--stale-days", type=int, default=90)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when high-severity hygiene issues are found.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    report = build_report(root, args.agent, args.max_note_bytes, args.max_trace_bytes, args.stale_days)
    write_report(root, local_dir, report)

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(local_dir / "memory" / "maintenance" / "latest-report.md")
    if args.strict and has_high_severity(report["candidates"]):  # type: ignore[arg-type]
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
