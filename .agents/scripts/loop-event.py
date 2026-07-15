#!/usr/bin/env python3
"""Record an event in a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import append_event, find_local_dir, resolve_run_dir


def parse_metadata(values: list[str], domain: str | None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if domain:
        metadata["domain"] = domain
    for value in values:
        if "=" not in value:
            raise ValueError(f"metadata must use key=value: {value}")
        key, item = value.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"metadata key must not be empty: {value}")
        metadata[key] = item.strip()
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a loop-governance event.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--run", required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--tool")
    parser.add_argument("--domain")
    parser.add_argument("--metadata", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    run_dir = resolve_run_dir(root, local_dir, args.run)
    try:
        metadata = parse_metadata(args.metadata, args.domain)
        state, event = append_event(run_dir, args.kind, args.summary, args.path, args.tool, metadata)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result = {"run_dir": str(run_dir), "event": event, "state": state}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(event["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
