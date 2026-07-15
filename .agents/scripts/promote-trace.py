#!/usr/bin/env python3
"""Promote a decision trace into a compact semantic note."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_core import promote_trace


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a trace into semantic memory.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--area")
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()

    path = promote_trace(
        Path(args.root),
        Path(args.trace),
        args.category,
        args.area,
        args.topic,
        agent=args.agent,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
