#!/usr/bin/env python3
"""Start a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import SCHEMA, append_event, display_path, find_local_dir, loop_runs_dir, now, slugify, write_json
from workflow_core import DEFAULT_BUDGET, PATTERNS, normalize_workflow


def checklist(task: str, trace: str | None, subagent_plan: str | None) -> str:
    return f"""# Loop Governance Checklist

Task: {task}

- [ ] Inspect evidence recorded before mutation.
- [ ] Decision evidence recorded before mutation.
- [ ] Mutation evidence recorded, if work changes files or state.
- [ ] Verification evidence recorded after mutation.
- [ ] Repair attempts recorded and bounded.
- [ ] Subagent results accepted or rejected by the orchestrator.
- [ ] Completed subagent sessions closed or explicitly justified.
- [ ] Closure evidence recorded before closing.

Trace: {trace or "none"}
Subagent plan: {subagent_plan or "none"}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Start a loop-governance run.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--task", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--trace")
    parser.add_argument("--subagent-plan")
    parser.add_argument("--pattern", choices=sorted(PATTERNS), default=None)
    parser.add_argument("--recipe", action="append", default=[])
    parser.add_argument("--budget-max-iterations", type=int, default=None)
    parser.add_argument("--budget-max-subagent-waves", type=int, default=None)
    parser.add_argument("--routing-confidence", type=float, default=None)
    parser.add_argument("--routing-reason", default="")
    parser.add_argument("--routing-fallback", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    runs = loop_runs_dir(local_dir)
    runs.mkdir(parents=True, exist_ok=True)
    stamp = now().replace(":", "").replace("+0000", "Z").replace("+00:00", "Z")
    run_id = slugify(args.run_id or f"{stamp}-{args.task}")
    run_dir = runs / run_id
    if run_dir.exists():
        print(f"loop run already exists: {run_dir}", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True)

    trace = display_path(root, args.trace)
    subagent_plan = display_path(root, args.subagent_plan)
    raw_workflow = None
    if args.pattern or args.recipe:
        budget = dict(DEFAULT_BUDGET)
        if args.budget_max_iterations is not None:
            budget["max_iterations"] = args.budget_max_iterations
        if args.budget_max_subagent_waves is not None:
            budget["max_subagent_waves"] = args.budget_max_subagent_waves
        raw_workflow = {
            "primary": args.pattern,
            "recipe": args.recipe,
            "budget": budget,
            "routing": {
                "confidence": args.routing_confidence,
                "reason": args.routing_reason,
                "fallback": args.routing_fallback,
            },
        }
    try:
        workflow = normalize_workflow(raw_workflow)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    state = {
        "schema": SCHEMA,
        "run_id": run_id,
        "task": args.task,
        "status": "created",
        "created_at": now(),
        "updated_at": now(),
        "local_dir": display_path(root, str(local_dir)) or local_dir.name,
        "trace": trace,
        "subagent_plan": subagent_plan,
        "workflow": workflow,
        "event_count": 0,
        "repair_attempts": 0,
        "flags": {
            "inspected": False,
            "decided": False,
            "mutated": False,
            "verified": False,
            "closure_passed": False,
            "subagent_results_pending": False,
        },
    }
    write_json(run_dir / "state.json", state)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "checklist.md").write_text(checklist(args.task, trace, subagent_plan), encoding="utf-8")
    state, event = append_event(run_dir, "loop.started", f"Started loop: {args.task}")
    result = {"run_dir": str(run_dir), "event": event, "state": state}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
