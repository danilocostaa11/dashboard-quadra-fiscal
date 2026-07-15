#!/usr/bin/env python3
"""Evaluate Fable Harness retrieval with local recall/precision metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import normalize_graph_path, search_memory


def load_cases(path: Path) -> list[dict[str, object]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("cases", [])
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    cases: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            cases.append(item)
    return cases


def relevant_targets(case: dict[str, object]) -> list[str]:
    raw = case.get("relevant", [])
    if isinstance(raw, str):
        return [normalize_graph_path(raw)]
    if not isinstance(raw, list):
        return []
    return [normalize_graph_path(str(item)) for item in raw if str(item).strip()]


def result_matches(result: dict[str, object], target: str) -> bool:
    path = normalize_graph_path(str(result.get("path", "")))
    citation = normalize_graph_path(str(result.get("citation", "")))
    target_path = target.split("#", 1)[0]
    if path == target_path:
        return True
    if citation == target:
        return True
    return bool(target_path and citation.startswith(f"{target_path}#"))


def evaluate(root: Path, eval_file: Path, agent: str, k: int, max_shards: int) -> dict[str, object]:
    cases = load_cases(eval_file)
    per_query: list[dict[str, object]] = []
    precision_total = 0.0
    recall_total = 0.0
    hit_total = 0.0
    mrr_total = 0.0
    for case in cases:
        query = str(case.get("query", "")).strip()
        targets = relevant_targets(case)
        if not query or not targets:
            continue
        results = search_memory(root, query, agent=agent, limit=k, max_shards=max_shards)
        hit_ranks: list[int] = []
        matched_targets: set[str] = set()
        for rank, result in enumerate(results, start=1):
            for target in targets:
                if result_matches(result, target):
                    hit_ranks.append(rank)
                    matched_targets.add(target)
                    break
        hits = len(hit_ranks)
        precision = hits / max(1, k)
        recall = len(matched_targets) / max(1, len(targets))
        mrr = 1.0 / min(hit_ranks) if hit_ranks else 0.0
        precision_total += precision
        recall_total += recall
        hit_total += 1.0 if hits else 0.0
        mrr_total += mrr
        per_query.append({
            "query": query,
            "relevant": targets,
            "hits": hits,
            "precision_at_k": round(precision, 6),
            "recall_at_k": round(recall, 6),
            "mrr": round(mrr, 6),
            "top_results": [
                {
                    "path": result.get("path"),
                    "citation": result.get("citation"),
                    "score": result.get("score"),
                }
                for result in results
            ],
        })
    count = len(per_query)
    return {
        "query_count": count,
        "k": k,
        "precision_at_k": round(precision_total / count, 6) if count else 0.0,
        "recall_at_k": round(recall_total / count, 6) if count else 0.0,
        "hit_rate_at_k": round(hit_total / count, 6) if count else 0.0,
        "mrr": round(mrr_total / count, 6) if count else 0.0,
        "cases": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Fable Harness RAG retrieval.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--eval-file", required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    metrics = evaluate(Path(args.root), Path(args.eval_file), args.agent, args.k, args.max_shards)
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"queries={metrics['query_count']} "
            f"precision@{metrics['k']}={metrics['precision_at_k']:.4f} "
            f"recall@{metrics['k']}={metrics['recall_at_k']:.4f} "
            f"mrr={metrics['mrr']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
