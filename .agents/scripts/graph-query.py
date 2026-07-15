#!/usr/bin/env python3
"""Query the generated Fable Harness knowledge graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import query_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Fable Harness graph nodes and edges.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--kind")
    parser.add_argument("--path")
    parser.add_argument("--node")
    parser.add_argument("--relation")
    parser.add_argument("--q")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = query_graph(
        Path(args.root),
        agent=args.agent,
        kind=args.kind,
        path=args.path,
        node=args.node,
        relation=args.relation,
        q=args.q,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        for node in result["nodes"]:
            print(f"node {node['id']} {node.get('kind', '')} {node.get('path', node.get('title', ''))}")
        for edge in result["edges"]:
            print(f"edge {edge['id']} {edge.get('type', '')} {edge.get('from', '')} -> {edge.get('to', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
