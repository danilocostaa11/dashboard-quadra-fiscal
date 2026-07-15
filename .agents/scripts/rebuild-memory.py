#!/usr/bin/env python3
"""Rebuild sharded vector memory and knowledge graph from notes/traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import build_memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild Fable Harness memory indexes.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    args = parser.parse_args()
    manifest = build_memory(Path(args.root), args.agent)
    print(json.dumps({
        "document_count": manifest["document_count"],
        "chunk_count": manifest.get("chunk_count", 0),
        "record_count": manifest.get("record_count", manifest["document_count"]),
        "chunking": manifest.get("chunking"),
        "cache_hits": manifest.get("cache", {}).get("hits", 0),
        "cache_misses": manifest.get("cache", {}).get("misses", 0),
        "shard_count": len(manifest["shards"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
