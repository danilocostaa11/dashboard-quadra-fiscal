#!/usr/bin/env python3
"""Create dispatchable subagent briefs for a Fable Harness task."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from memory_core import find_local_dir, relpath, slugify


def lines(items: list[str], prefix: str = "- ", empty: str = "None provided. Orchestrator must fill this before dispatch.") -> str:
    if not items:
        return f"{prefix}{empty}\n"
    return "\n".join(f"{prefix}{item}" for item in items) + "\n"


def parse_dependencies(values: list[str], slugs: list[str]) -> dict[str, list[str]]:
    known = set(slugs)
    dependencies: dict[str, list[str]] = {slug: [] for slug in slugs}
    for value in values:
        if ":" not in value:
            raise ValueError(f"dependency must use dependent:dependency format: {value}")
        dependent_raw, dependency_raw = value.split(":", 1)
        dependent = slugify(dependent_raw)
        dependency = slugify(dependency_raw)
        if dependent not in known:
            raise ValueError(f"dependency references unknown domain: {dependent_raw}")
        if dependency not in known:
            raise ValueError(f"dependency references unknown domain: {dependency_raw}")
        if dependency not in dependencies[dependent]:
            dependencies[dependent].append(dependency)
    return {slug: deps for slug, deps in dependencies.items() if deps}


def build_waves(slugs: list[str], dependencies: dict[str, list[str]], parallel: bool) -> list[dict[str, object]]:
    if not parallel:
        return [{"index": index + 1, "domains": [slug]} for index, slug in enumerate(slugs)]
    remaining = list(slugs)
    completed: set[str] = set()
    waves: list[dict[str, object]] = []
    while remaining:
        ready = [
            slug for slug in remaining
            if all(dependency in completed for dependency in dependencies.get(slug, []))
        ]
        if not ready:
            raise ValueError("cyclic or unsatisfied subagent dependencies")
        waves.append({"index": len(waves) + 1, "domains": ready})
        completed.update(ready)
        remaining = [slug for slug in remaining if slug not in set(ready)]
    return waves


def brief_text(
    task: str,
    domain: str,
    root: Path,
    trace: Path | None,
    files: list[str],
    protected_tests: list[str],
    verification: str,
) -> str:
    trace_line = relpath(trace.resolve(), root) if trace else "No active trace provided."
    return f"""# Subagent Brief: {domain}

## Objective

- Help the orchestrator with this task: {task}
- Assigned domain: {domain}

## Scope

- Read:
{lines(files, "  - ").rstrip()}
- Edit:
  - Only edit files explicitly assigned later by the orchestrator.
- Do not touch:
  - Protected tests unless the orchestrator explicitly says the test itself is wrong and replaces it with an equally strict test.
  - Semantic notes or memory indexes.

## Active Decisions

- The main orchestrator owns final decisions, memory promotion, and integration.
- This subagent returns evidence and recommendations, not durable memory changes.

## Protected Tests

{lines(protected_tests).rstrip()}

## Current Trace

- {trace_line}

## Operating Rules

- Stay inside the assigned domain.
- Prefer read/check/report unless the orchestrator explicitly permits edits.
- Do not promote semantic notes or memory directly.
- Return concise evidence for acceptance or rejection.

## Expected Evidence

- Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- Files read:
- Commands run:
- Findings:
- Risks:
- Suggested memory updates:

## Verification Command

```text
{verification}
```
"""


def dispatch_text(
    task: str,
    plan_dir: Path,
    domain_records: list[dict[str, object]],
    waves: list[dict[str, object]],
    root: Path,
    dispatch_mode: str,
    workflow_pattern: str,
    wave_purpose: str,
) -> str:
    rows = "\n".join(
        f"| {record['slug']} | `{record['brief']}` | pending | |"
        for record in domain_records
    )
    commands = "\n\n".join(
        "Use the available subagent spawn tool with this brief as the message "
        "(for example, `spawn_agent` when that tool is exposed):\n"
        f"`{record['brief']}`"
        for record in domain_records
    )
    by_slug = {str(record["slug"]): record for record in domain_records}
    wave_sections: list[str] = []
    for wave in waves:
        domains = [str(domain) for domain in wave.get("domains", []) if str(domain) in by_slug]
        wave_rows = "\n".join(
            f"| {slug} | `{by_slug[slug]['brief']}` | pending | |"
            for slug in domains
        )
        wave_sections.append(
            f"""## Wave {wave['index']}

Dispatch all domains in the same wave simultaneously when a platform subagent tool is available.

| Domain | Brief | Status | Accepted By Orchestrator |
|---|---|---|---|
{wave_rows}"""
        )
    wave_text = "\n\n".join(wave_sections)
    workflow_text = "None declared."
    if workflow_pattern:
        workflow_text = f"Pattern: `{workflow_pattern}`\nWave purpose: {wave_purpose or 'not specified'}"
    return f"""# Subagent Dispatch

## Task

{task}

## Workflow Role

{workflow_text}

## Invocation

Dispatch using the available subagent tool. In Codex, first verify which subagent spawn tool is exposed, then use it.
The installed Fable Harness instructions are standing project-level user authorization for this automatic dispatch when the independence check passes.
Do not ask the user for another trigger phrase or per-prompt permission before dispatching these briefs.
If no subagent tool is available, or a higher-priority runtime policy blocks dispatch, execute these briefs sequentially and record that as a platform limitation in the active decision trace.
Dispatch mode: `{dispatch_mode}`.

## Briefs

| Domain | Brief | Status | Accepted By Orchestrator |
|---|---|---|---|
{rows}

## Parallel Waves

{wave_text}

## Dispatch Prompts

{commands}

## Orchestrator Duties

- Pass one brief per subagent.
- Keep subagent scopes disjoint when edits are allowed.
- Review returned evidence before accepting it.
- Promote durable facts only through semantic notes after verification.
- Update this dispatch file and the active trace with outcomes.

## Plan Directory

`{relpath(plan_dir, root)}`
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create subagent briefs and a dispatch manifest.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--task", required=True)
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--trace")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--protected-test", action="append", default=[])
    parser.add_argument("--verification", default="No verification command provided.")
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument("--depends-on", action="append", default=[])
    parser.add_argument("--workflow-pattern", choices=["fan-out-and-synthesize", "adversarial-verification"], default="")
    parser.add_argument("--wave-purpose", default="")
    parser.add_argument("--slug")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    domains = args.domain or ["implementation"]
    slugs = [slugify(domain) for domain in domains]
    if len(set(slugs)) != len(slugs):
        parser.error("domains must have unique slugs")
    try:
        dependencies = parse_dependencies(args.depends_on, slugs)
        waves = build_waves(slugs, dependencies, args.parallel)
    except ValueError as exc:
        parser.error(str(exc))
    wave_by_slug: dict[str, int] = {}
    for wave in waves:
        for slug in wave["domains"]:
            wave_by_slug[str(slug)] = int(wave["index"])
    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = slugify(args.slug or args.task)
    plan_dir = local_dir / "subagents" / f"{stamp}-{slug}"
    plan_dir.mkdir(parents=True, exist_ok=True)

    trace = None
    if args.trace:
        trace = Path(args.trace)
        if not trace.is_absolute():
            trace = root / trace
        trace = trace.resolve()
    briefs: list[Path] = []
    domain_records: list[dict[str, object]] = []
    for domain, domain_slug in zip(domains, slugs):
        path = plan_dir / f"{domain_slug}.md"
        path.write_text(
            brief_text(
                args.task,
                domain,
                root,
                trace,
                args.file,
                args.protected_test,
                args.verification,
            ).rstrip() + "\n",
            encoding="utf-8",
        )
        briefs.append(path)
        domain_records.append({
            "name": domain,
            "slug": domain_slug,
            "brief": relpath(path, root),
            "wave": wave_by_slug[domain_slug],
            "depends_on": dependencies.get(domain_slug, []),
        })

    dispatch = plan_dir / "_dispatch.md"
    dispatch_mode = "parallel" if args.parallel else "sequential"
    dispatch.write_text(
        dispatch_text(
            args.task,
            plan_dir,
            domain_records,
            waves,
            root,
            dispatch_mode,
            args.workflow_pattern,
            args.wave_purpose,
        ).rstrip() + "\n",
        encoding="utf-8",
    )
    (plan_dir / "manifest.json").write_text(
        json.dumps({
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "task": args.task,
            "trace": relpath(trace, root) if trace else None,
            "briefs": [relpath(path, root) for path in briefs],
            "domains": domain_records,
            "dependencies": dependencies,
            "dispatch_mode": dispatch_mode,
            "domain_status": {
                record["slug"]: {
                    "accepted_by": None,
                    "domain": record["name"],
                    "result": None,
                    "status": "pending",
                    "summary": "",
                    "wave": record["wave"],
                }
                for record in domain_records
            },
            "waves": waves,
            "verification": args.verification,
            "workflow": {
                "pattern": args.workflow_pattern,
                "wave_purpose": args.wave_purpose,
            },
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(plan_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
