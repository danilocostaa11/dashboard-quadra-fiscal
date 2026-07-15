#!/usr/bin/env python3
"""Record a subagent result in the dispatch package and active trace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from memory_core import relpath, slugify


STATUSES = ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED")
SESSION_STATES = ("open", "closed", "keep-open", "close-unavailable")


def resolve_path(value: str, root: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def bullet_lines(items: list[str]) -> str:
    if not items:
        return "- none\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


def load_manifest(plan_dir: Path) -> dict[str, object]:
    path = plan_dir / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(plan_dir: Path, manifest: dict[str, object]) -> None:
    target = plan_dir / "manifest.json"
    tmp = plan_dir / "manifest.json.tmp"
    tmp.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def session_state(args: argparse.Namespace) -> tuple[str, str]:
    if args.closed:
        return "closed", "closed while recording result"
    if args.keep_open_reason:
        return "keep-open", args.keep_open_reason
    if args.close_unavailable_reason:
        return "close-unavailable", args.close_unavailable_reason
    return "open", ""


def update_dispatch(dispatch: Path, slug: str, status: str, accepted_by: str, result_rel: str, summary: str) -> None:
    text = dispatch.read_text(encoding="utf-8") if dispatch.exists() else "# Subagent Dispatch\n"
    lines = []
    updated = False
    for line in text.splitlines():
        if line.startswith(f"| {slug} |"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            brief = cells[1] if len(cells) > 1 else ""
            lines.append(f"| {slug} | {brief} | {status} | {accepted_by or 'pending'} |")
            updated = True
        else:
            lines.append(line)
    text = "\n".join(lines).rstrip() + "\n"
    if not updated:
        text += f"\n| {slug} | `{result_rel}` | {status} | {accepted_by or 'pending'} |\n"
    entry = f"- `{result_rel}`: {status}"
    if accepted_by:
        entry += f", accepted by {accepted_by}"
    if summary:
        entry += f" - {summary}"
    if "## Result Log" not in text:
        text += "\n## Result Log\n\n"
    text = text.rstrip() + "\n" + entry + "\n"
    dispatch.write_text(text, encoding="utf-8")


def append_trace(trace: Path, slug: str, status: str, result_rel: str, accepted_by: str, summary: str) -> None:
    if not trace.exists():
        return
    text = trace.read_text(encoding="utf-8")
    entry = f"- `{slug}`: {status}; evidence `{result_rel}`"
    if accepted_by:
        entry += f"; accepted by {accepted_by}"
    if summary:
        entry += f"; {summary}"
    if "## Subagent Results" not in text:
        text = text.rstrip() + "\n\n## Subagent Results\n\n"
    text = text.rstrip() + "\n" + entry + "\n"
    trace.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a subagent result.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--status", choices=STATUSES, required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--accepted-by", default="")
    parser.add_argument("--files-read", action="append", default=[])
    parser.add_argument("--commands-run", action="append", default=[])
    parser.add_argument("--finding", action="append", default=[])
    parser.add_argument("--risk", action="append", default=[])
    parser.add_argument("--suggested-memory-update", action="append", default=[])
    parser.add_argument("--session-id", default="")
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument("--closed", action="store_true")
    session_group.add_argument("--keep-open-reason", default="")
    session_group.add_argument("--close-unavailable-reason", default="")
    parser.add_argument("--trace")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan_dir = resolve_path(args.plan_dir, root)
    plan_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.domain)
    results_dir = plan_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    result_path = results_dir / f"{slug}-result.md"
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    session_status, session_reason = session_state(args)
    session_closed_at = timestamp if session_status == "closed" else ""
    session_record = {
        "session_id": args.session_id or None,
        "session_state": session_status,
        "session_reason": session_reason,
        "session_updated_at": timestamp,
    }
    if session_closed_at:
        session_record["session_closed_at"] = session_closed_at

    result_text = f"""# Subagent Result: {args.domain}

## Status

{args.status}

## Summary

{args.summary or "none"}

## Accepted By Orchestrator

{args.accepted_by or "pending"}

## Session

- ID: {args.session_id or "unknown"}
- State: {session_status}
- Reason: {session_reason or "none"}

## Files Read

{bullet_lines(args.files_read).rstrip()}

## Commands Run

{bullet_lines(args.commands_run).rstrip()}

## Findings

{bullet_lines(args.finding).rstrip()}

## Risks

{bullet_lines(args.risk).rstrip()}

## Suggested Memory Updates

{bullet_lines(args.suggested_memory_update).rstrip()}
"""
    result_path.write_text(result_text.rstrip() + "\n", encoding="utf-8")

    manifest = load_manifest(plan_dir)
    trace_value = args.trace or manifest.get("trace")
    result_rel = relpath(result_path, root)
    result_record = {
        "accepted_by": args.accepted_by or None,
        "domain": args.domain,
        "path": result_rel,
        "status": args.status,
        "summary": args.summary,
        "timestamp": timestamp,
        **session_record,
    }
    manifest.setdefault("results", [])
    assert isinstance(manifest["results"], list)
    manifest["results"].append(result_record)
    domain_status = manifest.get("domain_status")
    if isinstance(domain_status, dict):
        if slug not in domain_status:
            print(f"domain is not in dispatch manifest: {args.domain}", file=sys.stderr)
            return 2
        status_record = domain_status.get(slug)
        if not isinstance(status_record, dict):
            status_record = {}
        status_record.update({
            "accepted_by": args.accepted_by or None,
            "domain": args.domain,
            "result": result_rel,
            "status": args.status,
            "summary": args.summary,
            "updated_at": result_record["timestamp"],
            **session_record,
        })
        domain_status[slug] = status_record
    save_manifest(plan_dir, manifest)

    update_dispatch(
        plan_dir / "_dispatch.md",
        slug,
        args.status,
        args.accepted_by,
        result_rel,
        args.summary,
    )

    if trace_value:
        append_trace(
            resolve_path(str(trace_value), root),
            slug,
            args.status,
            result_rel,
            args.accepted_by,
            args.summary,
        )

    print(result_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
