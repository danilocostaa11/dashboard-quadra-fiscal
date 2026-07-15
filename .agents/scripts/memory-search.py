#!/usr/bin/env python3
"""Search compact semantic notes and traces using local sharded embeddings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import search_memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Fable Harness memory.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = search_memory(
        Path(args.root),
        args.query,
        agent=args.agent,
        limit=args.limit,
        max_shards=args.max_shards,
    )
    if args.json:
        print(json.dumps(results, ensure_ascii=False))
    else:
        for result in results:
            print(f"{result['score']:.4f} {result['path']} - {result['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
