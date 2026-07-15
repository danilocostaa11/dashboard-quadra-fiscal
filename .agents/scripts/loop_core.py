#!/usr/bin/env python3
"""Shared helpers for Fable Harness native loop governance scripts."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
from pathlib import Path

try:
    from workflow_core import workflow_errors
except Exception:
    workflow_errors = None


SCHEMA = "fable-harness-loop-governance-v1"
STATES = {
    "created",
    "oriented",
    "inspecting",
    "decided",
    "acting",
    "verifying",
    "repairing",
    "memory_closure",
    "closed",
    "blocked",
}
INSPECT_KINDS = {
    "file.read",
    "note.read",
    "trace.opened",
    "memory.search",
    "graph.query",
    "code-graph.query",
    "subagent.result.recorded",
    "subagent.result.accepted",
}
DECIDE_KINDS = {"decision.recorded", "loop.decided"}
MUTATION_KINDS = {
    "file.edited",
    "mutation.started",
    "mutation.finished",
    "command.mutating",
    "note.promoted",
    "memory.rebuilt",
}
VERIFY_KINDS = {
    "test.run",
    "test.passed",
    "test.failed",
    "verification.passed",
    "verification.failed",
    "check.passed",
    "check.failed",
    "closure.passed",
    "memory.closure.passed",
}
VERIFY_PASS_KINDS = {"test.passed", "verification.passed", "check.passed", "closure.passed", "memory.closure.passed"}
VERIFY_FAIL_KINDS = {"test.failed", "verification.failed", "check.failed"}
CLOSURE_KINDS = {"closure.passed", "memory.closure.passed"}
REPAIR_KINDS = {"repair.started"}
SUBAGENT_RESULT_KINDS = {"subagent.result.recorded"}
SUBAGENT_ACCEPTANCE_KINDS = {"subagent.result.accepted", "subagent.result.rejected"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "loop"


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def display_path(root: Path, value: str | None) -> str | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        return value.replace("\\", "/")
    try:
        return relpath(path.resolve(), root)
    except ValueError:
        return str(path)


def loop_runs_dir(local_dir: Path) -> Path:
    return local_dir / "loop" / "runs"


def resolve_run_dir(root: Path, local_dir: Path, run: str) -> Path:
    candidate = Path(run).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    direct = (root / candidate).resolve()
    if direct.exists():
        return direct
    return (loop_runs_dir(local_dir) / run).resolve()


def state_path(run_dir: Path) -> Path:
    return run_dir / "state.json"


def events_path(run_dir: Path) -> Path:
    return run_dir / "events.jsonl"


class LoopRunLock:
    def __init__(self, run_dir: Path, timeout_seconds: float = 10.0) -> None:
        self.path = run_dir / "run.lock"
        self.timeout_seconds = timeout_seconds
        self.handle: int | None = None

    def __enter__(self) -> "LoopRunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                self.handle = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.handle, str(os.getpid()).encode("utf-8"))
                return self
            except (FileExistsError, PermissionError) as exc:
                try:
                    age = time.time() - self.path.stat().st_mtime
                    if age > 60:
                        self.path.unlink()
                        continue
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out waiting for loop run lock: {self.path}") from exc
                time.sleep(0.025)

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.handle is not None:
            os.close(self.handle)
            self.handle = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def load_state(run_dir: Path) -> dict[str, object]:
    path = state_path(run_dir)
    if not path.exists():
        raise ValueError(f"loop state not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid loop state: {path}")
    if data.get("schema") != SCHEMA:
        raise ValueError(f"unsupported loop schema: {data.get('schema')}")
    return data


def write_state(run_dir: Path, state: dict[str, object]) -> None:
    state["updated_at"] = now()
    write_json(state_path(run_dir), state)


def read_events(run_dir: Path) -> list[dict[str, object]]:
    path = events_path(run_dir)
    if not path.exists():
        return []
    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if isinstance(event, dict):
            events.append(event)
    return events


def event_key(event: dict[str, object]) -> str:
    metadata = event.get("metadata")
    if isinstance(metadata, dict):
        domain = metadata.get("domain")
        if domain:
            return str(domain)
    if event.get("path"):
        return str(event["path"])
    return str(event.get("summary") or event.get("id") or "subagent-result")


def analyze_events(events: list[dict[str, object]]) -> dict[str, object]:
    first_inspect: int | None = None
    first_decide: int | None = None
    first_mutation: int | None = None
    last_mutation: int | None = None
    last_verify: int | None = None
    last_verify_after_mutation: int | None = None
    closure_passed = False
    repair_attempts = 0
    latest_verification_result = ""
    latest_verification_result_after_mutation = ""
    pending_results: set[str] = set()
    accepted_results: set[str] = set()

    for index, event in enumerate(events):
        kind = str(event.get("kind", "")).strip()
        if kind in INSPECT_KINDS and first_inspect is None:
            first_inspect = index
        if kind in DECIDE_KINDS and first_decide is None:
            first_decide = index
        if kind in MUTATION_KINDS:
            if first_mutation is None:
                first_mutation = index
            last_mutation = index
        if kind in VERIFY_KINDS:
            last_verify = index
            if kind in VERIFY_PASS_KINDS:
                latest_verification_result = "passed"
            elif kind in VERIFY_FAIL_KINDS:
                latest_verification_result = "failed"
            else:
                latest_verification_result = "observed"
            if last_mutation is not None and index > last_mutation:
                last_verify_after_mutation = index
                latest_verification_result_after_mutation = latest_verification_result
        if kind in CLOSURE_KINDS:
            closure_passed = True
        if kind in REPAIR_KINDS:
            repair_attempts += 1
        if kind in SUBAGENT_RESULT_KINDS:
            pending_results.add(event_key(event))
        if kind in SUBAGENT_ACCEPTANCE_KINDS:
            key = event_key(event)
            accepted_results.add(key)
            pending_results.discard(key)

    has_mutation = first_mutation is not None
    flags = {
        "inspected": first_inspect is not None,
        "decided": first_decide is not None,
        "mutated": has_mutation,
        "verified": last_verify is not None,
        "closure_passed": closure_passed,
        "subagent_results_pending": bool(pending_results - accepted_results),
    }
    return {
        "event_count": len(events),
        "flags": flags,
        "first_inspect": first_inspect,
        "first_decide": first_decide,
        "first_mutation": first_mutation,
        "last_mutation": last_mutation,
        "last_verify": last_verify,
        "last_verify_after_mutation": last_verify_after_mutation,
        "latest_verification_result": latest_verification_result,
        "latest_verification_result_after_mutation": latest_verification_result_after_mutation,
        "repair_attempts": repair_attempts,
        "pending_subagent_results": sorted(pending_results - accepted_results),
    }


def resolve_state_reference(root: Path | None, value: object) -> Path | None:
    if not root or not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def unaccepted_subagent_domains(root: Path | None, state: dict[str, object]) -> list[str]:
    plan_ref = resolve_state_reference(root, state.get("subagent_plan"))
    if not plan_ref:
        return []
    manifest_path = plan_ref / "manifest.json" if plan_ref.is_dir() else plan_ref
    if not manifest_path.exists():
        return [f"missing-manifest:{manifest_path}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"invalid-manifest:{manifest_path}"]
    if not isinstance(manifest, dict):
        return [f"invalid-manifest:{manifest_path}"]
    domain_status = manifest.get("domain_status", {})
    if not isinstance(domain_status, dict):
        return []
    unaccepted: list[str] = []
    for domain, raw_status in sorted(domain_status.items()):
        if not isinstance(raw_status, dict):
            unaccepted.append(str(domain))
            continue
        status = str(raw_status.get("status", "")).strip()
        accepted_by = str(raw_status.get("accepted_by", "")).strip()
        if status not in {"DONE", "DONE_WITH_CONCERNS"} or not accepted_by:
            unaccepted.append(str(domain))
    return unaccepted


def unclosed_subagent_sessions(root: Path | None, state: dict[str, object]) -> list[str]:
    plan_ref = resolve_state_reference(root, state.get("subagent_plan"))
    if not plan_ref:
        return []
    manifest_path = plan_ref / "manifest.json" if plan_ref.is_dir() else plan_ref
    if not manifest_path.exists():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(manifest, dict):
        return []
    domain_status = manifest.get("domain_status", {})
    if not isinstance(domain_status, dict):
        return []
    unclosed: list[str] = []
    for domain, raw_status in sorted(domain_status.items()):
        if not isinstance(raw_status, dict):
            continue
        status = str(raw_status.get("status", "")).strip()
        accepted_by = str(raw_status.get("accepted_by", "")).strip()
        if status not in {"DONE", "DONE_WITH_CONCERNS"} or not accepted_by:
            continue
        session_state = str(raw_status.get("session_state") or "").strip()
        session_reason = str(raw_status.get("session_reason") or "").strip()
        if session_state == "closed":
            continue
        if session_state in {"keep-open", "close-unavailable"} and session_reason:
            continue
        unclosed.append(str(domain))
    return unclosed


def sync_state(run_dir: Path) -> dict[str, object]:
    with LoopRunLock(run_dir):
        return sync_state_unlocked(run_dir)


def sync_state_unlocked(run_dir: Path) -> dict[str, object]:
    state = load_state(run_dir)
    events = read_events(run_dir)
    analysis = analyze_events(events)
    state["flags"] = analysis["flags"]
    state["event_count"] = analysis["event_count"]
    state["repair_attempts"] = analysis["repair_attempts"]
    if events:
        state["last_event"] = events[-1]
    write_state(run_dir, state)
    return state


def append_event_unlocked(
    run_dir: Path,
    kind: str,
    summary: str = "",
    paths: list[str] | None = None,
    tool: str | None = None,
    metadata: dict[str, str] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    state = load_state(run_dir)
    events = read_events(run_dir)
    timestamp = now()
    sequence = len(events) + 1
    event: dict[str, object] = {
        "schema": SCHEMA,
        "id": f"{timestamp}-{sequence:04d}",
        "timestamp": timestamp,
        "sequence": sequence,
        "kind": kind,
        "summary": summary,
    }
    clean_paths = [path for path in (paths or []) if path]
    if clean_paths:
        event["path"] = clean_paths[0]
        if len(clean_paths) > 1:
            event["paths"] = clean_paths
    if tool:
        event["tool"] = tool
    if metadata:
        event["metadata"] = metadata
    with events_path(run_dir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    events.append(event)
    analysis = analyze_events(events)
    state["flags"] = analysis["flags"]
    state["event_count"] = analysis["event_count"]
    state["repair_attempts"] = analysis["repair_attempts"]
    state["last_event"] = event
    write_state(run_dir, state)
    return state, event


def append_event(
    run_dir: Path,
    kind: str,
    summary: str = "",
    paths: list[str] | None = None,
    tool: str | None = None,
    metadata: dict[str, str] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    with LoopRunLock(run_dir):
        return append_event_unlocked(run_dir, kind, summary, paths, tool, metadata)


def transition_state(run_dir: Path, to_state: str, reason: str = "") -> tuple[dict[str, object], dict[str, object], str]:
    with LoopRunLock(run_dir):
        previous_state = load_state(run_dir)
        previous = str(previous_state.get("status"))
        state, event = append_event_unlocked(
            run_dir,
            "loop.transition",
            reason or f"{previous} -> {to_state}",
            metadata={"from": previous, "to": to_state},
        )
        state["status"] = to_state
        write_state(run_dir, state)
        return state, event, previous


def validate_run(
    state: dict[str, object],
    events: list[dict[str, object]],
    strict: bool,
    max_repair_attempts: int,
    root: Path | None = None,
) -> dict[str, object]:
    analysis = analyze_events(events)
    flags = dict(analysis["flags"])
    errors: list[str] = []
    warnings: list[str] = []
    first_mutation = analysis["first_mutation"]
    first_inspect = analysis["first_inspect"]
    first_decide = analysis["first_decide"]
    last_verify_after_mutation = analysis["last_verify_after_mutation"]

    if first_mutation is not None:
        if first_inspect is None or first_inspect > first_mutation:
            errors.append("mutation occurred before inspect evidence")
        if first_decide is None or first_decide > first_mutation:
            errors.append("mutation occurred before decision evidence")
        if last_verify_after_mutation is None:
            errors.append("mutation has no later verification evidence")
        if strict and analysis["latest_verification_result_after_mutation"] == "failed":
            errors.append("latest verification after mutation failed")

    repair_attempts = int(analysis["repair_attempts"])
    if repair_attempts > max_repair_attempts:
        errors.append(f"repair attempts exceeded limit: {repair_attempts}>{max_repair_attempts}")

    if strict and str(state.get("status")) == "closed" and not flags["closure_passed"]:
        errors.append("closed loop is missing closure evidence")

    pending = analysis["pending_subagent_results"]
    if strict and pending:
        errors.append("subagent results are recorded but not accepted or rejected: " + ", ".join(pending))

    unaccepted_domains = unaccepted_subagent_domains(root, state) if strict else []
    if unaccepted_domains:
        errors.append("subagent plan has unaccepted domains: " + ", ".join(unaccepted_domains))

    unclosed_sessions = (
        unclosed_subagent_sessions(root, state)
        if strict and str(state.get("status")) == "closed"
        else []
    )
    flags["subagent_sessions_open"] = bool(unclosed_sessions)
    if unclosed_sessions:
        errors.append("subagent sessions are not closed or justified: " + ", ".join(unclosed_sessions))

    if not events:
        warnings.append("loop has no events")

    if workflow_errors:
        try:
            workflow_failures, workflow_warnings = workflow_errors(
                state.get("workflow"),
                events,
                state,
                strict,
            )
        except ValueError as exc:
            workflow_failures = [str(exc)]
            workflow_warnings = []
        errors.extend(workflow_failures)
        warnings.extend(workflow_warnings)

    return {
        "status": "fail" if errors else "ok",
        "state_status": state.get("status"),
        "run_id": state.get("run_id"),
        "event_count": analysis["event_count"],
        "flags": flags,
        "repair_attempts": repair_attempts,
        "pending_subagent_results": pending,
        "unaccepted_subagent_domains": unaccepted_domains,
        "unclosed_subagent_sessions": unclosed_sessions,
        "errors": errors,
        "warnings": warnings,
    }
