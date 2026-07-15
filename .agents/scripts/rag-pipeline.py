#!/usr/bin/env python3
"""Create a retrieve -> inspect sources -> answer/plan evidence pack."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from memory_core import find_local_dir, relpath, search_memory, slugify


def source_excerpt(root: Path, result: dict[str, object], max_lines: int = 16) -> str:
    path_value = str(result.get("path", ""))
    if not path_value:
        return ""
    path = (root / path_value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return ""
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = int(result.get("start_line", 1) or 1)
    end = int(result.get("end_line", start) or start)
    start = max(1, min(start, len(lines) or 1))
    end = max(start, min(end, len(lines)))
    if end - start + 1 > max_lines:
        end = start + max_lines - 1
    excerpt = []
    for number in range(start, end + 1):
        excerpt.append(f"{number}: {lines[number - 1]}")
    return "\n".join(excerpt)


def write_report(root: Path, agent: str, query: str, results: list[dict[str, object]]) -> Path:
    local_dir = find_local_dir(root, agent)
    reports_dir = local_dir / "memory" / "retrieval"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = reports_dir / f"{stamp}-{slugify(query)[:60]}.md"
    lines = [
        f"# Retrieval Pipeline: {query}",
        "",
        "## Retrieve",
        "",
    ]
    if not results:
        lines.append("- No local memory results matched the query.")
    for index, result in enumerate(results, start=1):
        lines.append(
            f"{index}. `{result.get('citation', result.get('path'))}` "
            f"score={result.get('score')} kind={result.get('kind')} type={result.get('type')}"
        )
        lines.append(f"   - heading: {result.get('heading', '')}")
        lines.append(f"   - snippet: {result.get('snippet', '')}")
        lines.append(f"   - score_breakdown: `{json.dumps(result.get('score_breakdown', {}), sort_keys=True)}`")
    lines.extend(["", "## Inspect Sources", ""])
    for index, result in enumerate(results, start=1):
        citation = result.get("citation", result.get("path"))
        lines.append(f"### Source {index}: `{citation}`")
        excerpt = source_excerpt(root, result)
        if excerpt:
            lines.extend(["", "```text", excerpt, "```", ""])
        else:
            lines.append("")
            lines.append("- Source excerpt unavailable; open the source path before relying on this result.")
            lines.append("")
    lines.extend([
        "## Answer Or Plan With Citations",
        "",
        "- Use the cited source lines above before answering or planning.",
        "- If the cited sources are weak, stale, missing, or contradictory, inspect project files, web sources, or ask the user before planning.",
    ])
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an explicit Fable Harness RAG pipeline.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    results = search_memory(root, args.query, agent=args.agent, limit=args.limit, max_shards=args.max_shards)
    report = write_report(root, args.agent, args.query, results)
    payload = {
        "report_path": relpath(report, root),
        "result_count": len(results),
        "citations": [result.get("citation") for result in results],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(payload["report_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
