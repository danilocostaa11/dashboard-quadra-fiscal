#!/usr/bin/env python3
"""Record Fable Harness memory use without editing the source memory file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from memory_core import record_memory_touch


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a note, trace, or dormant memory touch.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--path", required=True, help="Memory path that was loaded or used.")
    parser.add_argument("--reason", default="", help="Short reason for the memory touch.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = record_memory_touch(Path(args.root), args.path, args.reason, args.agent)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{result['path']} use_count={result['use_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
