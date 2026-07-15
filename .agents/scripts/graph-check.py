#!/usr/bin/env python3
"""Validate the generated Fable Harness knowledge graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import check_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fable Harness graph integrity.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_graph(Path(args.root), agent=args.agent, strict=args.strict)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Fable Harness graph check {result['status']}.")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
