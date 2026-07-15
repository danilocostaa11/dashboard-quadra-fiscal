#!/usr/bin/env python3
"""Build the generated Fable Harness code graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from code_graph_core import build_code_graph, graph_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Fable Harness code graph.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = build_code_graph(Path(args.root), args.agent)
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    else:
        print(graph_dir(Path(args.root).resolve(), args.agent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
