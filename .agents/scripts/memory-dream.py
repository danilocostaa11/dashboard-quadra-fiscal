#!/usr/bin/env python3
"""Plan, apply, search, and reactivate Fable Harness memory dreams."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from memory_core import apply_dream_run, create_dream_plan, maintain_memory_dream, reactivate_dormant_memory, search_dormant_memory


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Fable Harness memory dreams.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="Plan a memory dreaming consolidation run.")
    add_common_args(plan_parser)
    plan_parser.add_argument("--context", default="", help="Current task context used for relevance scoring.")
    plan_parser.add_argument("--json", action="store_true")

    maintain_parser = sub.add_parser("maintain", help="Plan memory dreaming, apply safe mechanical actions, and write agent review.")
    add_common_args(maintain_parser)
    maintain_parser.add_argument("--context", default="", help="Current task context used for relevance scoring.")
    maintain_parser.add_argument("--auto-safe", action="store_true", help="Apply context-cold safe mechanical actions.")
    maintain_parser.add_argument("--agent-review", action="store_true", help="Write agent-review.md for semantic decisions.")
    maintain_parser.add_argument("--json", action="store_true")

    apply_parser = sub.add_parser("apply", help="Apply a reviewed memory dreaming plan.")
    add_common_args(apply_parser)
    apply_parser.add_argument("--run", required=True, help="Reviewed memory dream run directory or run id.")
    apply_parser.add_argument("--apply", action="store_true", help="Confirm intentional mutation.")
    apply_parser.add_argument("--json", action="store_true")

    search_parser = sub.add_parser("search-dormant", help="Search dormant memory before declaring context unavailable.")
    add_common_args(search_parser)
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--json", action="store_true")

    reactivate_parser = sub.add_parser("reactivate", help="Reactivate dormant memory into compact notes.")
    add_common_args(reactivate_parser)
    reactivate_parser.add_argument("--query", required=True)
    reactivate_parser.add_argument("--category", required=True)
    reactivate_parser.add_argument("--area")
    reactivate_parser.add_argument("--topic", required=True)
    reactivate_parser.add_argument("--apply", action="store_true")
    reactivate_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        if args.command == "plan":
            result = create_dream_plan(root, args.agent, args.context)
            if args.json:
                print(json.dumps(result, sort_keys=True))
            else:
                print(result["run_dir"])
            return 0
        if args.command == "maintain":
            result = maintain_memory_dream(root, args.agent, args.context, args.auto_safe, args.agent_review)
            if args.json:
                print(json.dumps(result, sort_keys=True))
            else:
                print(result["run_dir"])
            return 0
        if args.command == "apply":
            if not args.apply:
                raise ValueError("refusing to mutate without --apply")
            result = apply_dream_run(root, args.run, args.agent)
            if args.json:
                print(json.dumps(result, sort_keys=True))
            else:
                print(result["dormant_manifest"])
            return 0
        if args.command == "search-dormant":
            results = search_dormant_memory(root, args.query, args.agent, args.limit)
            if args.json:
                print(json.dumps(results, ensure_ascii=False, sort_keys=True))
            else:
                for result in results:
                    print(f"{result['score']:.4f} {result['original_path']} -> {result['dormant_path']} - {result['title']}")
            return 0
        if args.command == "reactivate":
            result = reactivate_dormant_memory(
                root,
                args.query,
                args.category,
                args.area,
                args.topic,
                args.agent,
                args.apply,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            else:
                print(result["note_path"])
            return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("memory-dream.py is not implemented yet")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
