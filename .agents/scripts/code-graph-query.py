#!/usr/bin/env python3
"""Query the generated Fable Harness code graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from code_graph_core import query_code_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Fable Harness code graph.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--path")
    parser.add_argument("--symbol")
    parser.add_argument("--kind")
    parser.add_argument("--relation")
    parser.add_argument("--from", dest="from_value")
    parser.add_argument("--to", dest="to_value")
    parser.add_argument("--impact")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = query_code_graph(
        Path(args.root),
        agent=args.agent,
        path=args.path,
        symbol=args.symbol,
        kind=args.kind,
        relation=args.relation,
        from_value=args.from_value,
        to_value=args.to_value,
        impact=args.impact,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        for node in result["nodes"]:
            print(f"node {node['id']} {node.get('kind', '')} {node.get('full_name', node.get('path', ''))}")
        for edge in result["edges"]:
            print(f"edge {edge['id']} {edge.get('relation', '')} {edge.get('from', '')} -> {edge.get('to', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
