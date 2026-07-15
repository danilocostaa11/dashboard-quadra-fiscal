#!/usr/bin/env python3
"""Close or justify completed subagent sessions before final loop closure."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from memory_core import slugify


DONE_STATUSES = {"DONE", "DONE_WITH_CONCERNS"}
FINAL_SESSION_STATES = {"closed", "keep-open", "close-unavailable"}


def resolve_path(value: str, root: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def load_manifest(plan_dir: Path) -> dict[str, object]:
    path = plan_dir / "manifest.json"
    if not path.exists():
        raise ValueError(f"dispatch manifest not found: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"invalid dispatch manifest: {path}")
    return manifest


def save_manifest(plan_dir: Path, manifest: dict[str, object]) -> None:
    target = plan_dir / "manifest.json"
    tmp = plan_dir / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


def parse_domain_reasons(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if ":" not in value:
            raise ValueError(f"expected DOMAIN:REASON, got: {value}")
        domain, reason = value.split(":", 1)
        slug = slugify(domain)
        reason = reason.strip()
        if not slug or not reason:
            raise ValueError(f"expected non-empty DOMAIN:REASON, got: {value}")
        parsed[slug] = reason
    return parsed


def is_finalized(status_record: dict[str, object]) -> bool:
    state = str(status_record.get("session_state") or "").strip()
    if state == "closed":
        return True
    if state in {"keep-open", "close-unavailable"}:
        return bool(str(status_record.get("session_reason") or "").strip())
    return False


def append_dispatch_log(plan_dir: Path, report: dict[str, object]) -> None:
    dispatch = plan_dir / "_dispatch.md"
    text = dispatch.read_text(encoding="utf-8") if dispatch.exists() else "# Subagent Dispatch\n"
    if "## Session Closure Log" not in text:
        text = text.rstrip() + "\n\n## Session Closure Log\n"
    entry = (
        f"- {report['timestamp']}: closed={', '.join(report['closed']) or 'none'}; "
        f"kept-open={', '.join(report['kept_open']) or 'none'}; "
        f"close-unavailable={', '.join(report['close_unavailable']) or 'none'}; "
        f"unchanged={', '.join(report['unchanged']) or 'none'}"
    )
    text = text.rstrip() + "\n" + entry + "\n"
    dispatch.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Close or justify completed subagent sessions.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--close-completed", action="store_true")
    parser.add_argument("--close-unavailable", action="store_true")
    parser.add_argument("--keep-open", action="append", default=[], metavar="DOMAIN:REASON")
    parser.add_argument("--reason", default="final subagent session sweep")
    parser.add_argument("--closed-by", default="orchestrator")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan_dir = resolve_path(args.plan_dir, root)
    try:
        keep_open = parse_domain_reasons(args.keep_open)
        manifest = load_manifest(plan_dir)
    except (ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    domain_status = manifest.get("domain_status", {})
    if not isinstance(domain_status, dict):
        print("dispatch manifest has no domain_status object", file=sys.stderr)
        return 2

    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    report: dict[str, object] = {
        "timestamp": timestamp,
        "closed": [],
        "kept_open": [],
        "close_unavailable": [],
        "skipped": [],
        "unchanged": [],
    }

    for domain, raw_status in sorted(domain_status.items()):
        slug = str(domain)
        if not isinstance(raw_status, dict):
            report["skipped"].append(slug)
            continue
        status = str(raw_status.get("status", "")).strip()
        accepted_by = str(raw_status.get("accepted_by") or "").strip()
        if status not in DONE_STATUSES or not accepted_by:
            report["skipped"].append(slug)
            continue
        if is_finalized(raw_status):
            report["unchanged"].append(slug)
            continue
        if slug in keep_open:
            raw_status.update({
                "session_state": "keep-open",
                "session_reason": keep_open[slug],
                "session_updated_at": timestamp,
                "session_closed_by": args.closed_by,
            })
            report["kept_open"].append(slug)
            continue
        if not args.close_completed:
            report["skipped"].append(slug)
            continue
        if args.close_unavailable:
            raw_status.update({
                "session_state": "close-unavailable",
                "session_reason": args.reason,
                "session_updated_at": timestamp,
                "session_closed_by": args.closed_by,
            })
            report["close_unavailable"].append(slug)
        else:
            raw_status.update({
                "session_state": "closed",
                "session_reason": args.reason,
                "session_updated_at": timestamp,
                "session_closed_at": timestamp,
                "session_closed_by": args.closed_by,
            })
            report["closed"].append(slug)
        domain_status[slug] = raw_status

    manifest["domain_status"] = domain_status
    manifest["session_closure"] = report
    save_manifest(plan_dir, manifest)

    report_path = plan_dir / "session-closure.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_dispatch_log(plan_dir, report)

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
