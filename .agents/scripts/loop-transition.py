#!/usr/bin/env python3
"""Transition a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import STATES, find_local_dir, resolve_run_dir, transition_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Transition a loop-governance run.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--run", required=True)
    parser.add_argument("--to", required=True, choices=sorted(STATES))
    parser.add_argument("--reason", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    run_dir = resolve_run_dir(root, local_dir, args.run)
    try:
        state, event, _previous = transition_state(run_dir, args.to, args.reason)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result = {"run_dir": str(run_dir), "event": event, "state": state}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(args.to)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
