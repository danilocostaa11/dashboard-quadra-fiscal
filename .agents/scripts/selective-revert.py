#!/usr/bin/env python3
"""Create and apply auditable selective rollback plans.

The script defaults to planning only. Mutating operations require the `apply`
subcommand and the explicit `--apply` flag.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


EXCLUDED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "rollback"


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


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


def resolve_inside(root: Path, value: str | Path) -> Path:
    raw = Path(value)
    path = raw if raw.is_absolute() else root / raw
    resolved = path.resolve()
    if not is_relative_to(resolved, root):
        raise ValueError(f"path is outside workspace: {value}")
    return resolved


def excluded_for_auto_collect(path: Path, root: Path, local_dir: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    if any(part in EXCLUDED_PARTS for part in parts):
        return True
    if len(parts) >= 2 and parts[0] == local_dir.name and parts[1] in {"rollback", "memory"}:
        return True
    return False


def collect_workspace_files(root: Path, local_dir: Path) -> list[str]:
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not excluded_for_auto_collect(path, root, local_dir):
            files.append(relpath(path, root))
    return files


def expand_requested_paths(root: Path, values: list[str], local_dir: Path, auto_collect: bool = False) -> list[str]:
    if not values and auto_collect:
        return collect_workspace_files(root, local_dir)
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        resolved = resolve_inside(root, value)
        if resolved.is_dir():
            for child in sorted(resolved.rglob("*")):
                if child.is_file():
                    rel = relpath(child, root)
                    if rel not in seen:
                        seen.add(rel)
                        result.append(rel)
            continue
        rel = relpath(resolved, root)
        if rel not in seen:
            seen.add(rel)
            result.append(rel)
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_if_file(source: Path, dest: Path) -> bool:
    if not source.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return True


def backup_current(root: Path, rel_paths: list[str], dest: Path) -> list[str]:
    copied: list[str] = []
    for rel in rel_paths:
        source = root / rel
        if copy_if_file(source, dest / rel):
            copied.append(rel)
    return copied


def read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit(result: dict[str, object], json_output: bool) -> None:
    if json_output:
        print(json.dumps(result, sort_keys=True))
    else:
        print(result["manifest"])


def run_git(root: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result


def require_git_repo(root: Path) -> None:
    result = run_git(root, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise ValueError("git mode requires a Git repository; create a checkpoint or run inside a Git repo")
    top = Path(result.stdout.strip()).resolve()
    if not is_relative_to(root, top) and top != root:
        raise ValueError(f"workspace root is outside Git repository root: {top}")


def ensure_no_staged_changes(root: Path, paths: list[str]) -> None:
    result = run_git(root, ["diff", "--cached", "--quiet", "--", *paths])
    if result.returncode == 1:
        raise ValueError("selected paths have staged changes; unstage them before selective revert")
    if result.returncode not in (0, 1):
        raise ValueError(result.stderr.strip() or "could not inspect staged changes")


def make_run_dir(local_dir: Path, kind: str, label: str) -> Path:
    path = local_dir / "rollback" / kind / f"{utc_stamp()}-{slugify(label)}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def checkpoint(root: Path, local_dir: Path, label: str, paths: list[str], json_output: bool) -> int:
    rel_paths = expand_requested_paths(root, paths, local_dir, auto_collect=True)
    run_dir = make_run_dir(local_dir, "checkpoints", label)
    files_dir = run_dir / "files"
    entries: list[dict[str, object]] = []
    for rel in rel_paths:
        source = root / rel
        entry: dict[str, object] = {"path": rel, "exists": source.is_file()}
        if source.is_file():
            copy_if_file(source, files_dir / rel)
            entry["bytes"] = source.stat().st_size
            entry["sha256"] = sha256_file(source)
            entry["snapshot"] = rel
        entries.append(entry)

    manifest = {
        "version": 1,
        "kind": "checkpoint",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "label": label,
        "root": str(root),
        "entries": entries,
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    (run_dir / "plan.md").write_text(
        "\n".join(
            [
                f"# Checkpoint: {label}",
                "",
                f"- Root: `{root}`",
                f"- Files recorded: {len(entries)}",
                "",
                "Use this checkpoint with:",
                "",
                f"`selective-revert.py plan --root {root} --checkpoint {manifest_path}`",
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    emit({"manifest": str(manifest_path), "entries": len(entries), "kind": "checkpoint"}, json_output)
    return 0


def load_manifest(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"manifest must contain a JSON object: {path}")
    return data


def resolve_manifest(root: Path, local_dir: Path, value: str) -> Path:
    raw = Path(value)
    if raw.is_absolute() or raw.exists() or raw.suffix == ".json":
        path = raw if raw.is_absolute() else root / raw
    else:
        path = local_dir / "rollback" / "checkpoints" / value / "manifest.json"
    resolved = path.resolve()
    if not is_relative_to(resolved, root):
        raise ValueError(f"manifest is outside workspace: {value}")
    if not resolved.is_file():
        raise ValueError(f"manifest not found: {value}")
    return resolved


def write_git_plan_md(path: Path, root: Path, paths: list[str], base: str, patch_path: Path) -> None:
    lines = [
        "# Selective Revert Plan",
        "",
        "- Mode: git",
        f"- Root: `{root}`",
        f"- Base: `{base}`",
        f"- Patch: `{patch_path}`",
        "",
        "## Selected Paths",
        "",
    ]
    lines.extend(f"- `{rel}`" for rel in paths)
    lines.extend(
        [
            "",
            "## Apply",
            "",
            "Inspect `reverse.patch` first. You may delete unrelated hunks from the patch, but keep paths inside the selected set.",
            "",
            f"`selective-revert.py apply --root {root} --plan {path / 'manifest.json'} --apply`",
        ]
    )
    (path / "plan.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def plan_git(root: Path, local_dir: Path, paths: list[str], base: str, label: str, json_output: bool) -> int:
    if not paths:
        raise ValueError("git selective revert requires at least one --path")
    require_git_repo(root)
    rel_paths = expand_requested_paths(root, paths, local_dir)
    ensure_no_staged_changes(root, rel_paths)
    run_dir = make_run_dir(local_dir, "plans", label)
    backup_current(root, rel_paths, run_dir / "backups" / "current")
    diff = run_git(root, ["diff", "--binary", "-R", base, "--", *rel_paths], check=True).stdout
    patch_path = run_dir / "reverse.patch"
    patch_path.write_text(diff, encoding="utf-8")
    check = run_git(root, ["apply", "--check", str(patch_path)])
    if check.returncode != 0:
        raise ValueError(check.stderr.strip() or "reverse patch does not apply cleanly")
    manifest = {
        "version": 1,
        "kind": "rollback-plan",
        "mode": "git",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root),
        "base": base,
        "paths": rel_paths,
        "reverse_patch": "reverse.patch",
        "backup_dir": "backups/current",
        "requires_apply_flag": True,
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    write_git_plan_md(run_dir, root, rel_paths, base, patch_path)
    emit({"manifest": str(manifest_path), "paths": rel_paths, "mode": "git"}, json_output)
    return 0


def text_diff_for_checkpoint(root: Path, checkpoint_dir: Path, operations: list[dict[str, object]]) -> str:
    chunks: list[str] = []
    for op in operations:
        rel = str(op["path"])
        action = str(op["action"])
        current = root / rel
        snap = checkpoint_dir / "files" / rel
        if action == "restore":
            current_text = read_text_or_none(current) if current.exists() else ""
            target_text = read_text_or_none(snap)
            if target_text is None or current_text is None:
                chunks.append(f"# Binary or unreadable restore: {rel}\n")
                continue
            chunks.extend(
                difflib.unified_diff(
                    current_text.splitlines(keepends=True),
                    target_text.splitlines(keepends=True),
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                )
            )
        elif action == "delete":
            chunks.append(f"# Delete created file with --allow-delete: {rel}\n")
    return "".join(chunks)


def plan_checkpoint(root: Path, local_dir: Path, checkpoint_value: str, paths: list[str], label: str, json_output: bool) -> int:
    checkpoint_manifest_path = resolve_manifest(root, local_dir, checkpoint_value)
    checkpoint_data = load_manifest(checkpoint_manifest_path)
    if checkpoint_data.get("kind") != "checkpoint":
        raise ValueError("checkpoint plan requires a checkpoint manifest")
    checkpoint_dir = checkpoint_manifest_path.parent
    entries = checkpoint_data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("checkpoint manifest is missing entries")
    by_path: dict[str, dict[str, object]] = {}
    for item in entries:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            by_path[str(item["path"])] = item

    rel_paths = expand_requested_paths(root, paths, local_dir) if paths else sorted(by_path)
    operations: list[dict[str, object]] = []
    for rel in rel_paths:
        if rel not in by_path:
            raise ValueError(f"path was not captured in checkpoint: {rel}")
        entry = by_path[rel]
        existed = bool(entry.get("exists"))
        current = root / rel
        if existed:
            snap = checkpoint_dir / "files" / rel
            if not snap.is_file():
                raise ValueError(f"checkpoint snapshot missing for: {rel}")
            current_hash = sha256_file(current) if current.is_file() else None
            snap_hash = sha256_file(snap)
            action = "noop" if current_hash == snap_hash else "restore"
            operations.append({"path": rel, "action": action})
        else:
            operations.append({"path": rel, "action": "delete" if current.exists() else "noop", "requires_allow_delete": current.exists()})

    run_dir = make_run_dir(local_dir, "plans", label)
    backup_current(root, rel_paths, run_dir / "backups" / "current")
    (run_dir / "reverse.patch").write_text(text_diff_for_checkpoint(root, checkpoint_dir, operations), encoding="utf-8")
    manifest = {
        "version": 1,
        "kind": "rollback-plan",
        "mode": "checkpoint",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root),
        "checkpoint_manifest": relpath(checkpoint_manifest_path, root),
        "paths": rel_paths,
        "operations": operations,
        "backup_dir": "backups/current",
        "requires_apply_flag": True,
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    lines = [
        "# Selective Revert Plan",
        "",
        "- Mode: checkpoint",
        f"- Root: `{root}`",
        f"- Checkpoint: `{checkpoint_manifest_path}`",
        "",
        "## Operations",
        "",
    ]
    lines.extend(f"- {item['action']}: `{item['path']}`" for item in operations)
    lines.extend(["", "## Apply", "", f"`selective-revert.py apply --root {root} --plan {manifest_path} --apply`"])
    (run_dir / "plan.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    emit({"manifest": str(manifest_path), "paths": rel_paths, "mode": "checkpoint"}, json_output)
    return 0


def patch_paths(patch_text: str) -> set[str]:
    paths: set[str] = set()
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            for token in parts[2:4]:
                if token.startswith(("a/", "b/")):
                    paths.add(token[2:])
    return paths


def apply_git_plan(root: Path, plan_path: Path) -> None:
    manifest = load_manifest(plan_path)
    patch = plan_path.parent / str(manifest.get("reverse_patch", "reverse.patch"))
    if not patch.is_file():
        raise ValueError(f"reverse patch not found: {patch}")
    allowed = {str(path).replace("\\", "/") for path in manifest.get("paths", []) if isinstance(path, str)}
    touched = patch_paths(patch.read_text(encoding="utf-8"))
    outside = sorted(touched - allowed)
    if outside:
        raise ValueError(f"reverse patch touches paths outside the plan: {', '.join(outside)}")
    check = run_git(root, ["apply", "--check", str(patch)])
    if check.returncode != 0:
        raise ValueError(check.stderr.strip() or "reverse patch does not apply cleanly")
    run_git(root, ["apply", str(patch)], check=True)


def apply_checkpoint_plan(root: Path, plan_path: Path, allow_delete: bool) -> None:
    manifest = load_manifest(plan_path)
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        raise ValueError("checkpoint rollback plan is missing operations")
    checkpoint_rel = manifest.get("checkpoint_manifest")
    if not isinstance(checkpoint_rel, str):
        raise ValueError("checkpoint rollback plan is missing checkpoint_manifest")
    checkpoint_path = resolve_inside(root, checkpoint_rel)
    checkpoint_dir = checkpoint_path.parent
    delete_ops = [op for op in operations if isinstance(op, dict) and op.get("action") == "delete"]
    if delete_ops and not allow_delete:
        raise ValueError("plan would delete files created after the checkpoint; rerun with --allow-delete")
    for op in operations:
        if not isinstance(op, dict) or not isinstance(op.get("path"), str):
            continue
        rel = str(op["path"])
        target = resolve_inside(root, rel)
        action = op.get("action")
        if action == "restore":
            source = checkpoint_dir / "files" / rel
            if not source.is_file():
                raise ValueError(f"checkpoint snapshot missing for: {rel}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif action == "delete":
            if target.is_dir():
                raise ValueError(f"refusing to delete directory: {rel}")
            if target.exists():
                target.unlink()


def apply_plan(root: Path, plan_value: str, allow_delete: bool, confirm_apply: bool) -> int:
    plan_path = resolve_inside(root, plan_value)
    if not plan_path.is_file():
        raise ValueError(f"plan manifest not found: {plan_value}")
    if not confirm_apply:
        raise ValueError("refusing to mutate without --apply")
    manifest = load_manifest(plan_path)
    if manifest.get("kind") != "rollback-plan":
        raise ValueError("apply requires a rollback-plan manifest")
    mode = manifest.get("mode")
    if mode == "git":
        apply_git_plan(root, plan_path)
    elif mode == "checkpoint":
        apply_checkpoint_plan(root, plan_path, allow_delete)
    else:
        raise ValueError(f"unknown rollback plan mode: {mode}")
    (plan_path.parent / "result.md").write_text(
        "\n".join(
            [
                "# Selective Revert Result",
                "",
                f"- Applied at: {dt.datetime.now(dt.timezone.utc).isoformat()}",
                f"- Mode: {mode}",
                f"- Plan: `{plan_path}`",
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    print(plan_path.parent / "result.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan and apply safe selective file reverts.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    sub = parser.add_subparsers(dest="command", required=True)

    checkpoint_parser = sub.add_parser("checkpoint", help="Record a native rollback checkpoint.")
    checkpoint_parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    checkpoint_parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)
    checkpoint_parser.add_argument("--label", required=True)
    checkpoint_parser.add_argument("--path", action="append", default=[])
    checkpoint_parser.add_argument("--json", action="store_true")

    plan_parser = sub.add_parser("plan", help="Create a rollback plan without mutating files.")
    plan_parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    plan_parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)
    plan_parser.add_argument("--path", action="append", default=[])
    plan_parser.add_argument("--base", default="HEAD")
    plan_parser.add_argument("--checkpoint")
    plan_parser.add_argument("--label", default="selective-revert")
    plan_parser.add_argument("--json", action="store_true")

    apply_parser = sub.add_parser("apply", help="Apply a previously generated rollback plan.")
    apply_parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    apply_parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--apply", action="store_true")
    apply_parser.add_argument("--allow-delete", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    try:
        if args.command == "checkpoint":
            return checkpoint(root, local_dir, args.label, args.path, args.json)
        if args.command == "plan":
            if args.checkpoint:
                return plan_checkpoint(root, local_dir, args.checkpoint, args.path, args.label, args.json)
            return plan_git(root, local_dir, args.path, args.base, args.label, args.json)
        if args.command == "apply":
            return apply_plan(root, args.plan, args.allow_delete, args.apply)
    except (RuntimeError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
