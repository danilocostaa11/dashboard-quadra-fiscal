#!/usr/bin/env python3
"""Warn when a newer Fable Harness GitHub release is available."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.request
from pathlib import Path


CURRENT_VERSION = "0.3.0"
LATEST_RELEASE_API = "https://api.github.com/repos/AAO-SH/fable-harness/releases/latest"
LATEST_RELEASE_URL = "https://github.com/AAO-SH/fable-harness/releases/latest"


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


def parse_time(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def now_utc(value: str | None) -> dt.datetime:
    parsed = parse_time(value or "")
    return parsed or dt.datetime.now(dt.timezone.utc)


def version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+){0,3}", str(value))
    if not match:
        return ()
    parts = [int(part) for part in match.group(0).split(".")]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer(latest: str, current: str) -> bool:
    latest_tuple = version_tuple(latest)
    current_tuple = version_tuple(current)
    return bool(latest_tuple and current_tuple and latest_tuple > current_tuple)


def state_path(local_dir: Path) -> Path:
    return local_dir / "harness" / "release-notice.json"


def read_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_latest_release(latest_json: str) -> dict[str, object]:
    if latest_json:
        candidate = Path(latest_json)
        text = candidate.read_text(encoding="utf-8-sig") if candidate.exists() else latest_json
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("latest release payload must be a JSON object")
        return data
    request = urllib.request.Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "fable-harness-release-notice",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("latest release payload must be a JSON object")
    return data


def notice_text(result: dict[str, object]) -> str:
    return (
        "Fable Harness update available: "
        f"installed {result['current_version']}, latest {result['latest_version']}.\n"
        f"Manual update: {result['latest_url']}\n"
        "No automatic update was applied."
    )


def check(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    path = state_path(local_dir)
    state = read_state(path)
    current_version = args.current_version or CURRENT_VERSION
    now = now_utc(args.now)
    interval = dt.timedelta(hours=args.interval_hours)
    last_checked = parse_time(str(state.get("last_checked_at") or ""))
    if last_checked and not args.force and now - last_checked < interval:
        return {
            "checked": False,
            "reason": "throttled",
            "current_version": current_version,
            "latest_version": state.get("latest_version"),
            "latest_url": state.get("latest_url", LATEST_RELEASE_URL),
            "update_available": bool(state.get("update_available")),
            "state_path": str(path),
        }

    result: dict[str, object] = {
        "checked": True,
        "reason": "checked",
        "current_version": current_version,
        "latest_version": None,
        "latest_url": LATEST_RELEASE_URL,
        "update_available": False,
        "state_path": str(path),
    }
    try:
        latest = load_latest_release(args.latest_json)
        latest_version = str(latest.get("tag_name") or latest.get("name") or "").strip()
        latest_url = str(latest.get("html_url") or LATEST_RELEASE_URL).strip()
        result["latest_version"] = latest_version
        result["latest_url"] = latest_url or LATEST_RELEASE_URL
        result["update_available"] = is_newer(latest_version, current_version)
    except Exception as exc:
        result["reason"] = "check-error"
        result["error"] = str(exc)

    state = {
        "checked_at": now.isoformat(),
        "current_version": result["current_version"],
        "last_checked_at": now.isoformat(),
        "latest_version": result["latest_version"],
        "latest_url": result["latest_url"],
        "update_available": result["update_available"],
        "reason": result["reason"],
    }
    if "error" in result:
        state["error"] = result["error"]
    write_state(path, state)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for newer Fable Harness releases without updating.")
    parser.add_argument("command", nargs="?", choices=["check"], default="check")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--current-version", default=CURRENT_VERSION)
    parser.add_argument("--interval-hours", type=float, default=24.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--latest-json", default="")
    parser.add_argument("--now")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check(args)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    elif result.get("checked") and result.get("update_available"):
        print(notice_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
