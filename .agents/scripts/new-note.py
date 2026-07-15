#!/usr/bin/env python3
"""Create or update a semantic note in category/area/topic layout."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_core import create_note


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Fable Harness semantic note.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--category", required=True)
    parser.add_argument("--area")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--title")
    parser.add_argument("--source-trace")
    args = parser.parse_args()

    path = create_note(
        Path(args.root),
        args.category,
        args.area,
        args.topic,
        title=args.title,
        source_trace=Path(args.source_trace) if args.source_trace else None,
        agent=args.agent,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
