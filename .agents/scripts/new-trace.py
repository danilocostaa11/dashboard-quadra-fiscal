#!/usr/bin/env python3
"""Create a Fable Harness decision trace and update the trace index."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "task"


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


def instruction_file_for(local_dir: Path) -> str:
    if local_dir.name == ".claude":
        return "CLAUDE.md"
    return "AGENTS.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a decision trace.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    traces = local_dir / "decision-traces"
    traces.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = slugify(args.slug or args.title)
    path = traces / f"{stamp}-{slug}.md"

    template_path = local_dir / "templates" / "decision-trace.md"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else "# {title}\n\n## Objective\n\n{objective}\n"
    content = template.replace("{title}", args.title).replace("{objective}", "Describe the task objective.")
    path.write_text(content, encoding="utf-8")

    index = traces / "_index.md"
    if not index.exists():
        index.write_text("# Decision Trace Index\n\n## Traces\n\n", encoding="utf-8")
    rel = path.name
    line = f"- {stamp[:10]}: [{args.title}]({rel})\n"
    index_text = index.read_text(encoding="utf-8")
    if rel not in index_text:
        index.write_text(index_text.rstrip() + "\n" + line, encoding="utf-8")

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
