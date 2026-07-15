#!/usr/bin/env python3
"""Validate a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import find_local_dir, read_events, resolve_run_dir, sync_state, validate_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a loop-governance run.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--run", required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--max-repair-attempts", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    run_dir = resolve_run_dir(root, local_dir, args.run)
    try:
        state = sync_state(run_dir)
        events = read_events(run_dir)
        report = validate_run(state, events, args.strict, args.max_repair_attempts, root)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    report["run_dir"] = str(run_dir)
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(f"loop check {report['status']}: {run_dir}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        for warning in report["warnings"]:
            print(f"WARN: {warning}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
