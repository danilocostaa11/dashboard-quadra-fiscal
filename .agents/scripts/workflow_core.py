#!/usr/bin/env python3
"""Workflow pattern helpers for Fable Harness loop governance."""

from __future__ import annotations


PATTERNS = {
    "classify-and-act": {"phase": "orient", "required": ["workflow.classified"]},
    "fan-out-and-synthesize": {
        "phase": "execution",
        "required": ["subagent.result.accepted", "synthesis.recorded"],
    },
    "adversarial-verification": {
        "phase": "verification",
        "required": ["adversarial.finding.recorded", "adversarial.resolution.recorded"],
    },
    "generate-and-filter": {
        "phase": "planning",
        "required": ["candidate.criteria.recorded", "candidate.selected"],
    },
    "tournament": {
        "phase": "planning",
        "required": ["tournament.match.recorded", "tournament.winner.selected"],
    },
    "loop-until-done": {"phase": "governance", "required": ["stop-condition.met"]},
}

DEFAULT_BUDGET = {
    "max_iterations": 3,
    "max_repairs": 2,
    "max_subagent_waves": 2,
    "low_confidence_threshold": 0.70,
}


def _clean_pattern(value: object) -> str:
    pattern = str(value or "").strip()
    if not pattern:
        return ""
    if pattern not in PATTERNS:
        raise ValueError(f"unknown workflow pattern: {pattern}")
    return pattern


def _merge_budget(raw_budget: object) -> dict[str, object]:
    budget: dict[str, object] = dict(DEFAULT_BUDGET)
    if isinstance(raw_budget, dict):
        for key, value in raw_budget.items():
            if value is not None:
                budget[str(key)] = value
    return budget


def normalize_workflow(raw: object) -> dict[str, object]:
    if not raw:
        return {
            "mode": "legacy-standard",
            "primary": None,
            "recipe": [],
            "routing": {"confidence": None, "reason": "", "fallback": ""},
            "budget": dict(DEFAULT_BUDGET),
        }
    if not isinstance(raw, dict):
        raise ValueError("workflow metadata must be an object")

    recipe: list[str] = []
    primary = _clean_pattern(raw.get("primary"))
    for item in raw.get("recipe") or []:
        pattern = _clean_pattern(item)
        if pattern and pattern not in recipe:
            recipe.append(pattern)
    if primary and primary not in recipe:
        recipe.append(primary)
    if not primary and recipe:
        primary = recipe[0]
    if not recipe:
        return normalize_workflow(None)

    routing_raw = raw.get("routing")
    routing = routing_raw if isinstance(routing_raw, dict) else {}
    return {
        "mode": "workflow-aware",
        "primary": primary,
        "recipe": recipe,
        "routing": {
            "confidence": routing.get("confidence"),
            "reason": str(routing.get("reason") or ""),
            "fallback": str(routing.get("fallback") or ""),
        },
        "budget": _merge_budget(raw.get("budget")),
    }


def pattern_set(workflow: dict[str, object]) -> set[str]:
    return {str(pattern) for pattern in workflow.get("recipe", []) if str(pattern) in PATTERNS}


def _event_indices(events: list[dict[str, object]], kind: str) -> list[int]:
    return [index for index, event in enumerate(events) if str(event.get("kind")) == kind]


def _has_event(events: list[dict[str, object]], kind: str) -> bool:
    return bool(_event_indices(events, kind))


def _first_index(events: list[dict[str, object]], kind: str) -> int | None:
    indices = _event_indices(events, kind)
    return indices[0] if indices else None


def _require_event(events: list[dict[str, object]], kind: str, errors: list[str], message: str) -> None:
    if not _has_event(events, kind):
        errors.append(message)


def _require_any(events: list[dict[str, object]], kinds: list[str], errors: list[str], message: str) -> None:
    if not any(_has_event(events, kind) for kind in kinds):
        errors.append(message)


def _metadata(event: dict[str, object]) -> dict[str, object]:
    metadata = event.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def workflow_errors(
    workflow: dict[str, object],
    events: list[dict[str, object]],
    state: dict[str, object],
    strict: bool,
) -> tuple[list[str], list[str]]:
    workflow = normalize_workflow(workflow)
    if workflow.get("mode") == "legacy-standard":
        return [], []

    errors: list[str] = []
    warnings: list[str] = []
    if not strict:
        warnings.append("workflow-aware run has pattern gates disabled outside strict mode")
        return errors, warnings

    recipe = pattern_set(workflow)

    if "classify-and-act" in recipe:
        classified = [event for event in events if str(event.get("kind")) == "workflow.classified"]
        _require_event(events, "workflow.classified", errors, "classify-and-act requires workflow.classified")
        budget = workflow.get("budget")
        budget_map = budget if isinstance(budget, dict) else {}
        threshold = _float_or_none(budget_map.get("low_confidence_threshold"))
        threshold = 0.70 if threshold is None else threshold
        routing = workflow.get("routing")
        routing_map = routing if isinstance(routing, dict) else {}
        for event in classified:
            metadata = _metadata(event)
            confidence = _float_or_none(metadata.get("confidence"))
            fallback = str(metadata.get("fallback") or routing_map.get("fallback") or "")
            if confidence is not None and confidence < threshold and not fallback:
                errors.append("classify-and-act low confidence route requires fallback metadata")

    if "generate-and-filter" in recipe:
        criteria_index = _first_index(events, "candidate.criteria.recorded")
        selected_index = _first_index(events, "candidate.selected")
        if selected_index is not None and (criteria_index is None or criteria_index > selected_index):
            errors.append("generate-and-filter selected a candidate before criteria were recorded")
        _require_event(events, "candidate.selected", errors, "generate-and-filter requires candidate.selected")

    if "fan-out-and-synthesize" in recipe:
        _require_event(
            events,
            "subagent.result.accepted",
            errors,
            "fan-out-and-synthesize requires accepted subagent result evidence",
        )
        _require_event(events, "synthesis.recorded", errors, "fan-out-and-synthesize requires synthesis.recorded")

    if "adversarial-verification" in recipe:
        _require_event(
            events,
            "adversarial.finding.recorded",
            errors,
            "adversarial-verification requires adversarial.finding.recorded",
        )
        _require_event(
            events,
            "adversarial.resolution.recorded",
            errors,
            "adversarial-verification requires adversarial.resolution.recorded",
        )

    if "tournament" in recipe:
        _require_event(events, "tournament.match.recorded", errors, "tournament selected a winner without a recorded match")
        _require_event(events, "tournament.winner.selected", errors, "tournament requires tournament.winner.selected")

    if "loop-until-done" in recipe:
        _require_any(
            events,
            ["stop-condition.met", "stop-condition.blocked"],
            errors,
            "loop-until-done requires stop-condition.met or stop-condition.blocked",
        )

    return errors, warnings
