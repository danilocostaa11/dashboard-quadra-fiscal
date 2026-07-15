#!/usr/bin/env python3
"""Compare retrieved harness memory with real project sources before edits."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from memory_core import find_local_dir, relpath, search_memory, slugify, top_terms


NEGATIVE_PATTERNS = [
    r"\bmust\s+not\b",
    r"\bshould\s+not\b",
    r"\bdo\s+not\b",
    r"\bdoes\s+not\b",
    r"\bnever\b",
    r"\bforbid(?:den|s)?\b",
    r"\bdisabled?\b",
    r"\bfalse\b",
    r"\bavoid\b",
    r"\bwithout\b",
]

POSITIVE_PATTERNS = [
    r"\bmust\s+use\b",
    r"\bshould\s+use\b",
    r"\buses?\b",
    r"\benabled?\b",
    r"\btrue\b",
    r"\brequir(?:e|es|ed)\b",
]


def polarity(text: str) -> str:
    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in NEGATIVE_PATTERNS):
        return "negative"
    if any(re.search(pattern, lowered) for pattern in POSITIVE_PATTERNS):
        return "positive"
    return "neutral"


def resolve_source(root: Path, value: str) -> Path | None:
    raw = Path(value)
    candidate = raw if raw.is_absolute() else root / raw
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved if resolved.is_file() else None


def source_paths(root: Path, sources: list[str], globs: list[str]) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for value in sources:
        resolved = resolve_source(root, value)
        if resolved and resolved not in seen:
            paths.append(resolved)
            seen.add(resolved)
    for pattern in globs:
        for candidate in sorted(root.glob(pattern)):
            if not candidate.is_file() or ".git" in candidate.parts:
                continue
            resolved = candidate.resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                continue
            if resolved not in seen:
                paths.append(resolved)
                seen.add(resolved)
    return paths


def matching_lines(path: Path, query_terms: set[str], max_lines: int = 8) -> list[dict[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []
    matches: list[dict[str, object]] = []
    fallback: list[dict[str, object]] = []
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        entry = {"line": line_no, "text": stripped, "polarity": polarity(stripped)}
        if len(fallback) < max_lines:
            fallback.append(entry)
        haystack = stripped.lower()
        if not query_terms or any(term in haystack for term in query_terms):
            matches.append(entry)
            if len(matches) >= max_lines:
                break
    return matches or fallback[:max_lines]


def project_claims(root: Path, paths: list[Path], query_terms: set[str]) -> list[dict[str, object]]:
    claims: list[dict[str, object]] = []
    for path in paths:
        for item in matching_lines(path, query_terms):
            citation = f"{relpath(path, root)}#L{item['line']}"
            claims.append({
                "path": relpath(path, root),
                "line": item["line"],
                "text": item["text"],
                "polarity": item["polarity"],
                "citation": citation,
            })
    return claims


def rag_claims(results: list[dict[str, object]]) -> list[dict[str, object]]:
    claims: list[dict[str, object]] = []
    for result in results:
        snippet = str(result.get("snippet") or result.get("summary") or "")
        if not snippet.strip():
            continue
        claims.append({
            "path": result.get("path", ""),
            "heading": result.get("heading", ""),
            "text": snippet,
            "polarity": polarity(snippet),
            "citation": result.get("citation", result.get("path", "")),
            "score": result.get("score"),
        })
    return claims


def conflict_pairs(rag_items: list[dict[str, object]], source_items: list[dict[str, object]]) -> list[dict[str, object]]:
    conflicts: list[dict[str, object]] = []
    opposites = {("positive", "negative"), ("negative", "positive")}
    for rag in rag_items:
        for source in source_items:
            if (str(rag.get("polarity")), str(source.get("polarity"))) not in opposites:
                continue
            conflicts.append({
                "rag": rag,
                "project": source,
                "reason": "opposite polarity over retrieved project-relevant evidence",
            })
    return conflicts


def write_report(
    root: Path,
    agent: str,
    query: str,
    results: list[dict[str, object]],
    rag_items: list[dict[str, object]],
    source_items: list[dict[str, object]],
    conflicts: list[dict[str, object]],
    decision: str,
) -> Path:
    local_dir = find_local_dir(root, agent)
    reports_dir = local_dir / "memory" / "retrieval"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = reports_dir / f"{stamp}-source-arbitration-{slugify(query)[:52]}.md"

    lines = [
        f"# Source Arbitration: {query}",
        "",
        "## Light Gate",
        "",
        f"- Decision: `{decision}`",
        f"- RAG results inspected: {len(results)}",
        f"- Project source claims inspected: {len(source_items)}",
        f"- Material conflicts: {len(conflicts)}",
        "",
    ]
    if not conflicts:
        lines.extend([
            "No material conflict detected by the lightweight gate.",
            "",
            "Keep inspecting real project files before editing.",
            "",
        ])
    lines.extend(["## RAG Evidence", ""])
    if not rag_items:
        lines.append("- No retrieved RAG evidence was available.")
    for item in rag_items:
        lines.append(f"- RAG says `{item['citation']}` polarity={item['polarity']} score={item.get('score')}: {item['text']}")
    lines.extend(["", "## Project Source Evidence", ""])
    if not source_items:
        lines.append("- No project source evidence was provided. Inspect real project files before planning or editing.")
    for item in source_items:
        lines.append(f"- Project source says `{item['citation']}` polarity={item['polarity']}: {item['text']}")
    lines.extend(["", "## Evidence Dispute", ""])
    if not conflicts:
        lines.append("- No full Evidence Dispute is required by the lightweight gate.")
    for index, conflict in enumerate(conflicts, start=1):
        rag = conflict["rag"]
        project = conflict["project"]
        lines.extend([
            f"### Conflict {index}",
            "",
            f"- RAG says `{rag['citation']}`: {rag['text']}",
            f"- Project source says `{project['citation']}`: {project['text']}",
            f"- Difference: {conflict['reason']}",
            "- User gate: Ask the user before replacing project facts with RAG-derived facts.",
            "",
        ])
    lines.extend([
        "## Recommendation Matrix",
        "",
        "| Option | What changes | Pros | Cons |",
        "|---|---|---|---|",
        "| Keep project source | Treat current code/docs as operational truth and update memory if stale | Safest for current behavior | May preserve an outdated or inconsistent project fact |",
        "| Update project source from RAG | Change code/docs to match retrieved canonical memory | Aligns project with prior decisions | Requires user approval and verification because RAG may be stale |",
        "| Update memory from project source | Mark RAG memory stale/superseded and promote current source truth | Keeps retrieval honest | Can erase a useful architectural correction if source is wrong |",
        "| Gather more evidence | Add tests, inspect more files, or ask the user | Best for low-confidence conflicts | Slower |",
        "",
        "## Next Step",
        "",
        "- If `decision` is `full-dispute-required`, present the dispute, recommendation, pros, and cons to the user before mutating code/docs.",
        "- If `decision` is `light-gate-only`, continue with normal planning, but keep cited project files as the stronger operational evidence.",
    ])
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Fable Harness source arbitration.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--query", required=True)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--source-glob", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    query_terms = set(top_terms(args.query, limit=24))
    results = search_memory(root, args.query, agent=args.agent, limit=args.limit, max_shards=args.max_shards)
    paths = source_paths(root, args.source, args.source_glob)
    rag_items = rag_claims(results)
    source_items = project_claims(root, paths, query_terms)
    conflicts = conflict_pairs(rag_items, source_items)
    if conflicts:
        decision = "full-dispute-required"
    elif not source_items:
        decision = "source-inspection-required"
    else:
        decision = "light-gate-only"
    report = write_report(root, args.agent, args.query, results, rag_items, source_items, conflicts, decision)
    payload = {
        "decision": decision,
        "report_path": relpath(report, root),
        "rag_result_count": len(results),
        "project_source_count": len(paths),
        "project_claim_count": len(source_items),
        "material_conflict_count": len(conflicts),
        "conflicts": conflicts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(payload["report_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
