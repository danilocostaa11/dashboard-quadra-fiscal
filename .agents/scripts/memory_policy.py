#!/usr/bin/env python3
"""Policy checks for Fable Harness traces and semantic notes."""

from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path


NOTE_TYPES = {"canonical-decision", "trace-summary", "operational-note", "migration-note"}
NOTE_STATUSES = {"active", "superseded", "archived"}
ATOMIC_NOTE_FIELDS = ["thesis", "atomic", "tags", "properties", "moc", "links", "validation"]
ATOMIC_VALIDATION_ITEMS = {"atomic", "thesis-title", "connects", "unique", "metadata"}
GENERIC_TRACE_TITLES = {"misc", "plus", "session", "work", "task", "update", "notes"}
DOMAIN_TERMS = {
    "architecture": {"architecture", "domain", "boundary", "service", "module"},
    "tooling": {"tooling", "workflow", "script", "command", "package", "install"},
    "policy": {"policy", "permission", "security", "compliance", "capability"},
    "questionnaire": {"questionnaire", "question", "answer", "block"},
    "release": {"release", "publish", "version", "npm", "pypi"},
    "testing": {"test", "tdd", "verify", "validation", "coverage"},
}


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def file_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def parse_frontmatter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    try:
        start = next(idx for idx, line in enumerate(lines) if line.strip() == "---")
    except StopIteration:
        return {}
    meta: dict[str, object] = {}
    current: str | None = None
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("- ") and current:
            if not isinstance(meta.get(current), list):
                meta[current] = []
            value = stripped[2:].strip()
            if value:
                meta[current].append(value)
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            current = key.strip()
            value = value.strip()
            meta[current] = value
    return meta


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def add_candidate(
    candidates: list[dict[str, object]],
    action: str,
    path: Path,
    root: Path,
    reason: str,
    severity: str = "warn",
    size: int | None = None,
) -> None:
    item: dict[str, object] = {
        "action": action,
        "path": relpath(path, root),
        "reason": reason,
        "severity": severity,
    }
    if size is not None:
        item["bytes"] = size
    candidates.append(item)


def expected_scope(note: Path, local_dir: Path) -> str:
    return relpath(note.with_suffix(""), local_dir / "notes")


def note_title_matches_thesis(title: str, thesis: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    return bool(thesis.strip()) and normalize(title) == normalize(thesis)


def is_active_canonical(meta: dict[str, object]) -> bool:
    return (
        str(meta.get("type", "")).strip() == "canonical-decision"
        and str(meta.get("status", "")).strip() == "active"
        and as_bool(meta.get("canonical"))
    )


def is_atomic_v1(meta: dict[str, object]) -> bool:
    return str(meta.get("memory_schema", "")).strip() == "atomic-v1"


def skip_policy_note(note: Path, local_dir: Path) -> bool:
    if note.name == "_index.md":
        return True
    try:
        parts = note.relative_to(local_dir / "notes").parts
    except ValueError:
        return False
    return bool(parts and parts[0] in {"_moc", "_inbox"})


def resolve_source(note: Path, source: str) -> Path:
    path = Path(source.strip().strip("`"))
    if not path.is_absolute():
        path = note.parent / path
    return path.resolve()


def note_policy_candidates(note: Path, root: Path, local_dir: Path, validate_sources: bool = False) -> list[dict[str, object]]:
    text = note.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    candidates: list[dict[str, object]] = []
    required = ["type", "status", "scope", "canonical", "sources", "supersedes", "last_verified"]
    missing = [key for key in required if key not in meta]
    if missing:
        add_candidate(candidates, "repair-note-schema", note, root, f"missing required frontmatter: {', '.join(missing)}", "high")
        return candidates
    note_type = str(meta.get("type", "")).strip()
    status = str(meta.get("status", "")).strip()
    if note_type not in NOTE_TYPES:
        add_candidate(candidates, "repair-note-schema", note, root, f"invalid note type: {note_type}", "high")
    if status not in NOTE_STATUSES:
        add_candidate(candidates, "repair-note-schema", note, root, f"invalid note status: {status}", "high")
    if as_bool(meta.get("canonical")) and note_type != "canonical-decision":
        add_candidate(candidates, "repair-note-schema", note, root, "canonical notes must use type canonical-decision", "high")
    if not str(meta.get("scope", "")).strip():
        add_candidate(candidates, "repair-note-schema", note, root, "scope must not be empty", "high")
    if is_active_canonical(meta) and not is_atomic_v1(meta):
        missing_atomic = [key for key in ["memory_schema", *ATOMIC_NOTE_FIELDS] if key not in meta]
        if missing_atomic:
            add_candidate(
                candidates,
                "upgrade-note-atomicity",
                note,
                root,
                f"legacy active canonical note is missing permanent-note metadata: {', '.join(missing_atomic)}",
                "warn",
            )
    if is_atomic_v1(meta):
        missing = [key for key in ATOMIC_NOTE_FIELDS if key not in meta]
        if missing:
            add_candidate(candidates, "repair-note-atomicity", note, root, f"missing atomic frontmatter: {', '.join(missing)}", "high")
        title = file_title(text, note.stem)
        thesis = str(meta.get("thesis", "")).strip()
        if not thesis:
            add_candidate(candidates, "repair-note-atomicity", note, root, "thesis must not be empty", "high")
        elif not note_title_matches_thesis(title, thesis):
            add_candidate(candidates, "repair-note-atomicity", note, root, "title must state the same thesis as thesis frontmatter", "high")
        if not as_bool(meta.get("atomic")):
            add_candidate(candidates, "repair-note-atomicity", note, root, "atomic must be true for permanent notes", "high")
        if not as_list(meta.get("tags", [])):
            add_candidate(candidates, "repair-note-atomicity", note, root, "tags must include at least one queryable tag", "high")
        if not as_list(meta.get("properties", [])):
            add_candidate(candidates, "repair-note-atomicity", note, root, "properties must include at least one queryable property", "high")
        moc = str(meta.get("moc", "")).strip()
        links = as_list(meta.get("links", []))
        if not moc:
            add_candidate(candidates, "repair-note-atomicity", note, root, "moc must point to a map of content", "high")
        if not links:
            add_candidate(candidates, "repair-note-atomicity", note, root, "links must connect the note to a MOC or related note", "high")
        validation = set(as_list(meta.get("validation", [])))
        missing_validation = sorted(ATOMIC_VALIDATION_ITEMS - validation)
        if missing_validation:
            add_candidate(candidates, "repair-note-atomicity", note, root, f"validation gate is missing: {', '.join(missing_validation)}", "high")
    if validate_sources:
        sources = as_list(meta.get("sources", []))
        if not sources:
            add_candidate(candidates, "repair-source", note, root, "note has no source evidence", "high")
        for source in sources:
            if not resolve_source(note, source).exists():
                add_candidate(candidates, "repair-source", note, root, f"missing source: {source}", "high")
    return candidates


def duplicate_canonical_candidates(root: Path, local_dir: Path) -> list[dict[str, object]]:
    notes = local_dir / "notes"
    by_scope: dict[str, list[Path]] = {}
    if not notes.exists():
        return []
    for note in notes.rglob("*.md"):
        if skip_policy_note(note, local_dir):
            continue
        meta = parse_frontmatter(note.read_text(encoding="utf-8"))
        if (
            str(meta.get("type", "")).strip() == "canonical-decision"
            and str(meta.get("status", "")).strip() == "active"
            and as_bool(meta.get("canonical"))
        ):
            scope = str(meta.get("scope", "")).strip() or expected_scope(note, local_dir)
            by_scope.setdefault(scope, []).append(note)
    candidates: list[dict[str, object]] = []
    for scope, paths in sorted(by_scope.items()):
        if len(paths) > 1:
            joined = ", ".join(relpath(path, root) for path in paths)
            add_candidate(
                candidates,
                "deduplicate-canonical-note",
                paths[0],
                root,
                f"duplicate active canonical note for scope {scope}: {joined}",
                "high",
            )
    return candidates


def allowed_umbrella_trace(title: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return normalized.startswith("session-index") or normalized.startswith("migration-trace")


def trace_policy_candidates(trace: Path, root: Path, max_trace_bytes: int = 24576) -> list[dict[str, object]]:
    text = trace.read_text(encoding="utf-8")
    title = file_title(text, trace.stem)
    normalized_title = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    candidates: list[dict[str, object]] = []
    if normalized_title in GENERIC_TRACE_TITLES:
        add_candidate(candidates, "rename-generic-trace", trace, root, f"generic trace title: {title}", "high")
    block_markers = re.findall(r"(?im)(?:^|\s)(?:#\d+|block[-_ ]?\d+)\b", text)
    if len(block_markers) >= 3 and not allowed_umbrella_trace(title):
        add_candidate(candidates, "split-umbrella-trace", trace, root, "trace contains multiple questionnaire/block markers", "high")
    lower = text.lower()
    domains = [
        domain
        for domain, terms in DOMAIN_TERMS.items()
        if any(re.search(rf"\b{re.escape(term)}\b", lower) for term in terms)
    ]
    if len(domains) >= 4 and not allowed_umbrella_trace(title):
        add_candidate(candidates, "review-mixed-domain-trace", trace, root, f"trace mixes domains: {', '.join(domains)}", "warn")
    size = trace.stat().st_size
    if size > max_trace_bytes and not allowed_umbrella_trace(title):
        add_candidate(candidates, "summarize-trace", trace, root, f"trace exceeds {max_trace_bytes} bytes", "high", size)
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", trace.name)
    if date_match:
        created = dt.date.fromisoformat(date_match.group(1))
        modified = dt.datetime.fromtimestamp(trace.stat().st_mtime).date()
        if modified > created and "Continuation Justification" not in text:
            add_candidate(candidates, "justify-trace-continuation", trace, root, "trace was updated on a later day without continuation justification", "high")
    return candidates


def policy_candidates(
    root: Path,
    local_dir: Path,
    max_trace_bytes: int = 24576,
    validate_sources: bool = False,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    notes = local_dir / "notes"
    if notes.exists():
        for note in sorted(notes.rglob("*.md")):
            if skip_policy_note(note, local_dir):
                continue
            candidates.extend(note_policy_candidates(note, root, local_dir, validate_sources))
    candidates.extend(duplicate_canonical_candidates(root, local_dir))
    traces = local_dir / "decision-traces"
    if traces.exists():
        for trace in sorted(traces.rglob("*.md")):
            if trace.name == "_index.md":
                continue
            candidates.extend(trace_policy_candidates(trace, root, max_trace_bytes))
    return candidates


def critical_closure_failures(root: Path, local_dir: Path, trace: Path | None = None) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    notes = local_dir / "notes"
    if notes.exists():
        for note in sorted(notes.rglob("*.md")):
            if skip_policy_note(note, local_dir):
                continue
            candidates.extend(note_policy_candidates(note, root, local_dir, validate_sources=True))
    candidates.extend(duplicate_canonical_candidates(root, local_dir))
    if trace and trace.exists():
        candidates.extend(trace_policy_candidates(trace, root))
    return [item for item in candidates if item.get("severity") == "high"]


def has_high_severity(candidates: list[dict[str, object]]) -> bool:
    return any(item.get("severity") == "high" for item in candidates)
