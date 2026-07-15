#!/usr/bin/env python3
"""Local-first memory core for Fable Harness scripts.

Storage is deliberately sharded JSONL. Manifests stay small; retrieval reads
candidate shards instead of one large vector file.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import time
from pathlib import Path


VECTOR_DIMS = 64
MEMORY_SCHEMA = "fable-harness-memory-v2"
GRAPH_SCHEMA = "fable-harness-graph-v3"
CHUNKING_STRATEGY = "markdown-heading-window-v2"
MAX_CHUNK_CHARS = 1800
CHUNK_OVERLAP_LINES = 2
HYBRID_SCORE_WEIGHTS = {
    "vector": 0.40,
    "lexical": 0.35,
    "graph": 0.15,
    "rerank": 0.10,
}
STOPWORDS = {
    "about", "after", "again", "also", "and", "are", "because", "before",
    "between", "but", "can", "codex", "did", "does", "done", "for", "from",
    "had", "has", "have", "into", "its", "not", "now", "the", "then",
    "this", "that", "they", "trace", "when", "where", "with", "work",
}
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "topic"


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


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def top_terms(text: str, limit: int = 16) -> list[str]:
    counts: dict[str, int] = {}
    for token in tokens(text):
        if token in STOPWORDS or len(token) < 3:
            continue
        counts[token] = counts.get(token, 0) + 1
    return [
        term
        for term, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def vector(text: str) -> list[list[float]]:
    values = [0.0] * VECTOR_DIMS
    for token in tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = digest[0] % VECTOR_DIMS
        sign = 1.0 if digest[1] % 2 == 0 else -1.0
        values[idx] += sign
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [[idx, round(value / norm, 6)] for idx, value in enumerate(values) if value]


def vector_dict(items: list[list[float]]) -> dict[int, float]:
    return {int(idx): float(value) for idx, value in items}


def cosine(left: list[list[float]], right: list[list[float]]) -> float:
    a = vector_dict(left)
    b = vector_dict(right)
    if not a or not b:
        return 0.0
    return sum(value * b.get(idx, 0.0) for idx, value in a.items())


def file_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def compact_summary(text: str, limit: int = 420) -> str:
    lines = []
    in_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not lines:
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
        if sum(len(item) for item in lines) > limit:
            break
    summary = " ".join(lines)
    return summary[:limit].rstrip()


def section(text: str, names: tuple[str, ...]) -> str:
    wanted = {name.lower() for name in names}
    current: str | None = None
    chunks: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            continue
        if current in wanted:
            chunks.append(line)
    return "\n".join(chunks).strip()


def source_lines(text: str) -> list[str]:
    sources: list[str] = []
    in_sources = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("sources:"):
            in_sources = True
            continue
        if in_sources:
            if stripped.startswith("- "):
                sources.append(stripped[2:].strip())
                continue
            if stripped and not line.startswith(" "):
                break
    return sources


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
            meta[current] = value.strip()
    return meta


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def note_moc_path(local_dir: Path, category: str) -> Path:
    return local_dir / "notes" / "_moc" / f"{slugify(category)}.md"


def note_metadata(text: str, path: Path, local_dir: Path, doc_type: str) -> dict[str, object]:
    if doc_type != "note":
        return {}
    meta = parse_frontmatter(text)
    return {
        "memory_schema": str(meta.get("memory_schema", "")).strip(),
        "thesis": str(meta.get("thesis", "")).strip(),
        "atomic": str(meta.get("atomic", "")).strip(),
        "tags": as_list(meta.get("tags", [])),
        "properties": as_list(meta.get("properties", [])),
        "moc": str(meta.get("moc", "")).strip(),
        "links": as_list(meta.get("links", [])),
        "validation": as_list(meta.get("validation", [])),
    }


def metadata_terms(metadata: dict[str, object]) -> list[str]:
    values = [
        str(metadata.get("thesis", "")),
        " ".join(str(tag) for tag in metadata.get("tags", [])),
        " ".join(str(prop) for prop in metadata.get("properties", [])),
        str(metadata.get("moc", "")),
        " ".join(str(link) for link in metadata.get("links", [])),
    ]
    seen: set[str] = set()
    terms: list[str] = []
    for token in tokens(" ".join(values)):
        lowered = token.lower()
        if lowered not in seen:
            seen.add(lowered)
            terms.append(lowered)
    return terms[:24]


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def citation_for(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    if not start_line:
        return path
    if not end_line or end_line == start_line:
        return f"{path}#L{start_line}"
    return f"{path}#L{start_line}-L{end_line}"


def markdown_sections(text: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    if not lines:
        return []
    sections: list[dict[str, object]] = []
    heading_stack: list[str] = []
    current_heading = "Document"
    current_start = 1

    for line_number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        if current_start < line_number:
            sections.append({
                "heading": current_heading,
                "start_line": current_start,
                "end_line": line_number - 1,
                "text": "\n".join(lines[current_start - 1:line_number - 1]),
            })
        level = len(match.group(1))
        title = match.group(2).strip()
        heading_stack = heading_stack[: max(level - 1, 0)]
        heading_stack.append(title)
        current_heading = " > ".join(heading_stack)
        current_start = line_number

    sections.append({
        "heading": current_heading,
        "start_line": current_start,
        "end_line": len(lines),
        "text": "\n".join(lines[current_start - 1:]),
    })
    return sections


def split_large_section(section: dict[str, object]) -> list[dict[str, object]]:
    text = str(section.get("text", ""))
    if len(text) <= MAX_CHUNK_CHARS:
        return [section]
    lines = text.splitlines()
    chunks: list[dict[str, object]] = []
    start = 0
    base_line = int(section.get("start_line", 1))
    while start < len(lines):
        chars = 0
        end = start
        while end < len(lines) and (chars + len(lines[end]) + 1 <= MAX_CHUNK_CHARS or end == start):
            chars += len(lines[end]) + 1
            end += 1
        chunks.append({
            "heading": section.get("heading", "Document"),
            "start_line": base_line + start,
            "end_line": base_line + end - 1,
            "text": "\n".join(lines[start:end]),
        })
        if end >= len(lines):
            break
        start = max(start + 1, end - CHUNK_OVERLAP_LINES)
    return chunks


def markdown_chunks(text: str) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    for section_item in markdown_sections(text):
        for chunk in split_large_section(section_item):
            chunk_text = str(chunk.get("text", "")).strip()
            if not chunk_text:
                continue
            if not has_substantive_chunk_content(chunk_text):
                continue
            chunks.append(chunk)
    return chunks


def has_substantive_chunk_content(text: str) -> bool:
    in_frontmatter = False
    seen_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            if not seen_frontmatter:
                seen_frontmatter = True
                in_frontmatter = True
                continue
            if in_frontmatter:
                in_frontmatter = False
                continue
        if in_frontmatter:
            continue
        if not stripped or stripped.startswith("#"):
            continue
        return True
    return False


def graph_terms_for_doc(doc: dict[str, object]) -> list[str]:
    text = str(doc.get("text", ""))
    semantic_labels = [label for _kind, label in semantic_items(text)]
    parts = [
        str(doc.get("title", "")),
        str(doc.get("summary", "")),
        str(doc.get("thesis", "")),
        " ".join(str(term) for term in doc.get("terms", [])),
        " ".join(str(tag) for tag in doc.get("tags", [])),
        " ".join(str(prop) for prop in doc.get("properties", [])),
        str(doc.get("moc", "")),
        " ".join(str(link) for link in doc.get("links", [])),
        " ".join(str(source) for source in doc.get("sources", [])),
        " ".join(referenced_paths(text)),
        " ".join(command_lines(text)),
        " ".join(decision_snippets(text)),
        " ".join(semantic_labels),
    ]
    return top_terms(" ".join(parts), limit=32)


def chunk_record(doc: dict[str, object], chunk: dict[str, object], index: int) -> dict[str, object]:
    chunk_text = str(chunk.get("text", ""))
    heading = str(chunk.get("heading") or doc.get("title") or "Document")
    start_line = int(chunk.get("start_line", 1))
    end_line = int(chunk.get("end_line", start_line))
    path = str(doc["path"])
    chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
    identity = f"{path}:{start_line}:{end_line}:{chunk_hash}"
    summary = compact_summary(chunk_text, limit=360) or heading
    graph_terms = top_terms(" ".join([
        heading,
        " ".join(str(term) for term in doc.get("graph_terms", [])),
        " ".join(str(source) for source in doc.get("sources", [])),
    ]), limit=32)
    record = {
        "id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        "type": doc["type"],
        "kind": "chunk",
        "path": path,
        "parent_id": doc["id"],
        "parent_path": path,
        "chunk_index": index,
        "title": doc["title"],
        "heading": heading,
        "summary": summary,
        "snippet": summary,
        "terms": top_terms(" ".join([heading, chunk_text]), limit=24),
        "graph_terms": graph_terms,
        "text_hash": doc["text_hash"],
        "chunk_hash": chunk_hash,
        "vector": vector(chunk_text),
        "sources": doc.get("sources", []),
        "start_line": start_line,
        "end_line": end_line,
        "citation": citation_for(path, start_line, end_line),
    }
    for key in ["memory_schema", "thesis", "atomic", "tags", "properties", "moc", "links", "validation"]:
        if key in doc:
            record[key] = doc[key]
    return record


def chunk_records_for_doc(doc: dict[str, object]) -> list[dict[str, object]]:
    text = str(doc.get("text", ""))
    return [
        chunk_record(doc, chunk, index)
        for index, chunk in enumerate(markdown_chunks(text), start=1)
    ]


def stable_id(kind: str, value: str) -> str:
    digest = hashlib.sha256(f"{kind}:{value}".encode("utf-8")).hexdigest()[:20]
    return f"{kind}:{digest}"


def edge_id(edge_type: str, source: str, target: str, evidence: str = "") -> str:
    digest = hashlib.sha256(f"{edge_type}:{source}:{target}:{evidence}".encode("utf-8")).hexdigest()[:20]
    return f"edge:{digest}"


def normalize_graph_path(path: str) -> str:
    return path.strip().strip("`").strip().replace("\\", "/")


def resolve_reference_path(root: Path, doc_path: str, reference: str) -> str:
    value = normalize_graph_path(reference)
    raw = Path(value)
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        resolved = (root / Path(doc_path).parent / raw).resolve()
    try:
        return relpath(resolved, root)
    except ValueError:
        return value


SCRIPT_PATH_RE = re.compile(r"(?P<path>(?:\.codex|\.claude|\.agents|scripts|src|tests|\.github)[\\/][A-Za-z0-9_.\\/-]+)")
SEMANTIC_PREFIXES = {
    "backlog": "backlog_item",
    "backlog item": "backlog_item",
    "capability": "capability",
    "constraint": "constraint",
    "feature": "feature",
    "risk": "risk",
    "verification": "verification",
}
SEMANTIC_RELATIONS = {
    "backlog_item": "related_to",
    "capability": "implements",
    "constraint": "depends_on",
    "feature": "implements",
    "risk": "blocked_by",
    "verification": "verifies",
}


def referenced_paths(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in SCRIPT_PATH_RE.finditer(text):
        ref = normalize_graph_path(match.group("path")).rstrip(".,);:")
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs


def semantic_items(text: str) -> list[tuple[str, str]]:
    chunks = section(text, (
        "durable fact or decision",
        "evidence",
        "risks",
        "residual risk",
        "verification",
        "constraints",
        "operational use",
        "revalidation",
    ))
    items: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in chunks.splitlines():
        value = line.strip().lstrip("-").strip()
        if not value or value.startswith("```"):
            continue
        match = re.match(r"(?i)^([a-z][a-z ]{2,24}):\s*(.+)$", value)
        if not match:
            continue
        prefix = match.group(1).strip().lower()
        kind = SEMANTIC_PREFIXES.get(prefix)
        label = match.group(2).strip()
        if not kind or not label:
            continue
        key = (kind, label.lower())
        if key not in seen:
            seen.add(key)
            items.append((kind, label[:240]))
    return items


def command_lines(text: str) -> list[str]:
    chunks = section(text, ("verify", "verification", "evidence"))
    commands: list[str] = []
    seen: set[str] = set()
    for command in re.findall(r"`([^`]+)`", chunks):
        value = command.strip()
        if not value:
            continue
        first = value.split()[0].lower() if value.split() else ""
        if first in {"python", "py", "node", "npm", "yarn", "pnpm", "pytest", "git"} or "test" in value.lower():
            if value not in seen:
                seen.add(value)
                commands.append(value)
    return commands


def decision_snippets(text: str, limit: int = 3) -> list[str]:
    chunks = section(text, ("decide", "decision", "decisions", "durable fact or decision", "durable decision"))
    snippets: list[str] = []
    for line in chunks.splitlines():
        value = line.strip().lstrip("-").strip()
        if not value or value.startswith("```"):
            continue
        snippets.append(value[:220])
        if len(snippets) >= limit:
            break
    return snippets


def dormant_manifest_path(local_dir: Path) -> Path:
    return local_dir / "memory" / "dormant" / "manifest.json"


def load_dormant_manifest(local_dir: Path) -> dict[str, object]:
    path = dormant_manifest_path(local_dir)
    if not path.exists():
        return {"version": 1, "items": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "items": []}
    if not isinstance(data, dict):
        return {"version": 1, "items": []}
    if not isinstance(data.get("items"), list):
        data["items"] = []
    data.setdefault("version", 1)
    return data


def write_dormant_manifest(local_dir: Path, manifest: dict[str, object]) -> None:
    manifest["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(dormant_manifest_path(local_dir), manifest)


def dormant_excluded_paths(local_dir: Path) -> set[str]:
    manifest = load_dormant_manifest(local_dir)
    items = manifest.get("items", [])
    if not isinstance(items, list):
        return set()
    excluded: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or item.get("state") != "dormant":
            continue
        original_path = item.get("original_path")
        if isinstance(original_path, str) and original_path.strip():
            excluded.add(normalize_graph_path(original_path))
    return excluded


def iter_markdown_docs(local_dir: Path, exclude_paths: set[str] | None = None) -> list[dict[str, object]]:
    docs: list[dict[str, object]] = []
    excluded = {normalize_graph_path(path) for path in (exclude_paths or set())}
    for base, doc_type in [(local_dir / "notes", "note"), (local_dir / "decision-traces", "trace")]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name == "_index.md":
                continue
            rel = relpath(path, local_dir.parent)
            if rel in excluded:
                continue
            text = path.read_text(encoding="utf-8")
            title = file_title(text, path.stem)
            metadata = note_metadata(text, path, local_dir, doc_type)
            term_text = " ".join([
                text,
                str(metadata.get("thesis", "")),
                " ".join(str(tag) for tag in metadata.get("tags", [])),
                " ".join(str(prop) for prop in metadata.get("properties", [])),
                str(metadata.get("moc", "")),
                " ".join(str(link) for link in metadata.get("links", [])),
            ])
            base_terms = top_terms(term_text)
            for term in metadata_terms(metadata):
                if term not in base_terms:
                    base_terms.append(term)
            doc = {
                "id": hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16],
                "type": doc_type,
                "path": rel,
                "title": title,
                "summary": compact_summary(text),
                "terms": base_terms[:32],
                "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "vector": vector(text),
                "sources": source_lines(text),
                "text": text,
            }
            doc.update({key: value for key, value in metadata.items() if value not in ("", [], None)})
            docs.append(doc)
    return docs


def reset_jsonl_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.glob("*.jsonl"):
        child.unlink()
    for child in path.glob("*.json"):
        child.unlink()


def append_jsonl(path: Path, item: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def ensure_memory_layout(local_dir: Path) -> None:
    memory = local_dir / "memory"
    (memory / "shards").mkdir(parents=True, exist_ok=True)
    (memory / "graph").mkdir(parents=True, exist_ok=True)
    (memory / "cache").mkdir(parents=True, exist_ok=True)
    manifest = memory / "manifest.json"
    if not manifest.exists():
        manifest.write_text(
            json.dumps({
                "version": 1,
                "storage": "sharded-jsonl",
                "embedding": "local-hash-v1",
                "vector_dims": VECTOR_DIMS,
                "document_count": 0,
                "shards": [],
            }, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def chunk_cache_path(local_dir: Path) -> Path:
    return local_dir / "memory" / "cache" / "documents.json"


def load_chunk_cache(local_dir: Path) -> dict[str, object]:
    path = chunk_cache_path(local_dir)
    if not path.exists():
        return {"version": 1, "chunking": CHUNKING_STRATEGY, "documents": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "chunking": CHUNKING_STRATEGY, "documents": {}}
    if not isinstance(data, dict):
        return {"version": 1, "chunking": CHUNKING_STRATEGY, "documents": {}}
    if not isinstance(data.get("documents"), dict):
        data["documents"] = {}
    return data


def write_chunk_cache(local_dir: Path, data: dict[str, object]) -> None:
    data["version"] = 1
    data["chunking"] = CHUNKING_STRATEGY
    data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    path = chunk_cache_path(local_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")


def iter_semantic_note_paths(notes: Path) -> list[Path]:
    if not notes.exists():
        return []
    return [
        path
        for path in sorted(notes.rglob("*.md"))
        if path.name != "_index.md" and "_moc" not in path.relative_to(notes).parts
    ]


def update_note_mocs(local_dir: Path) -> None:
    notes = local_dir / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[Path]] = {}
    for path in iter_semantic_note_paths(notes):
        rel_parts = path.relative_to(notes).parts
        if not rel_parts:
            continue
        category = rel_parts[0]
        if category.startswith("_"):
            continue
        groups.setdefault(category, []).append(path)
    moc_dir = notes / "_moc"
    moc_dir.mkdir(parents=True, exist_ok=True)
    for category, paths in sorted(groups.items()):
        lines = [
            f"# {category.replace('-', ' ').title()} MOC",
            "",
            "Map of content for this note cluster.",
            "",
            "## Notes",
            "",
        ]
        for path in sorted(paths):
            rel = relpath(path, moc_dir)
            title = file_title(path.read_text(encoding="utf-8"), path.stem)
            lines.append(f"- [{title}]({rel})")
        (moc_dir / f"{slugify(category)}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def update_notes_index(local_dir: Path) -> None:
    notes = local_dir / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    update_note_mocs(local_dir)
    lines = ["# Semantic Notes Index", "", "Compact project memory for future agents.", "", "## Notes", ""]
    for path in iter_semantic_note_paths(notes):
        rel = relpath(path, notes)
        title = file_title(path.read_text(encoding="utf-8"), path.stem)
        lines.append(f"- [{title}]({rel})")
    moc_paths = sorted((notes / "_moc").glob("*.md")) if (notes / "_moc").exists() else []
    if moc_paths:
        lines.extend(["", "## Maps Of Content", ""])
        for path in moc_paths:
            rel = relpath(path, notes)
            title = file_title(path.read_text(encoding="utf-8"), path.stem)
            lines.append(f"- [{title}]({rel})")
    (notes / "_index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_memory(root: Path, agent: str = "auto") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    ensure_memory_layout(local_dir)
    update_notes_index(local_dir)

    memory = local_dir / "memory"
    shards_dir = memory / "shards"
    graph_dir = memory / "graph"
    reset_jsonl_dir(shards_dir)
    reset_jsonl_dir(graph_dir)

    docs = iter_markdown_docs(local_dir, dormant_excluded_paths(local_dir))
    for doc in docs:
        doc["kind"] = "document"
        doc["graph_terms"] = graph_terms_for_doc(doc)

    old_cache = load_chunk_cache(local_dir)
    old_cache_docs = old_cache.get("documents", {})
    if not isinstance(old_cache_docs, dict):
        old_cache_docs = {}
    new_cache_docs: dict[str, object] = {}
    chunk_records_by_path: dict[str, list[dict[str, object]]] = {}
    cache_hits = 0
    cache_misses = 0
    for doc in docs:
        doc_path = str(doc["path"])
        cached = old_cache_docs.get(doc_path)
        chunks: list[dict[str, object]]
        if (
            isinstance(cached, dict)
            and cached.get("text_hash") == doc.get("text_hash")
            and cached.get("chunking") == CHUNKING_STRATEGY
            and isinstance(cached.get("chunks"), list)
        ):
            chunks = [item for item in cached["chunks"] if isinstance(item, dict)]  # type: ignore[index]
            cache_hits += 1
        else:
            chunks = chunk_records_for_doc(doc)
            cache_misses += 1
        chunk_records_by_path[doc_path] = chunks
        new_cache_docs[doc_path] = {
            "text_hash": doc.get("text_hash"),
            "chunking": CHUNKING_STRATEGY,
            "chunk_count": len(chunks),
            "chunks": chunks,
        }

    shard_meta: dict[str, dict[str, object]] = {}
    doc_id_by_path = {str(doc["path"]): str(doc["id"]) for doc in docs}
    nodes: dict[str, dict[str, object]] = {}
    edges: dict[str, dict[str, object]] = {}

    def append_shard_record(record: dict[str, object]) -> None:
        shard_id = str(record["id"])[:2]
        shard_path = shards_dir / f"{shard_id}.jsonl"
        append_jsonl(shard_path, record)
        meta = shard_meta.setdefault(shard_id, {
            "id": shard_id,
            "path": relpath(shard_path, root),
            "doc_count": 0,
            "terms": set(),
        })
        meta["doc_count"] = int(meta["doc_count"]) + 1
        meta["terms"].update(record.get("terms", []))  # type: ignore[union-attr]

    def add_node(item: dict[str, object]) -> None:
        node_id = str(item["id"])
        existing = nodes.get(node_id)
        if existing:
            existing.update({key: value for key, value in item.items() if key not in existing or existing[key] in ("", None)})
        else:
            nodes[node_id] = item

    def add_edge(source: str, target: str, edge_type: str, evidence: str = "") -> None:
        item = {
            "id": edge_id(edge_type, source, target, evidence),
            "from": source,
            "to": target,
            "type": edge_type,
        }
        if evidence:
            item["evidence"] = evidence[:240]
        edges[str(item["id"])] = item

    def add_source_edge(doc: dict[str, object], source: str) -> None:
        resolved = resolve_reference_path(root, str(doc["path"]), source)
        target = doc_id_by_path.get(resolved)
        if not target:
            target = stable_id("source", resolved)
            add_node({"id": target, "kind": "source", "path": resolved, "title": resolved})
        add_edge(str(doc["id"]), target, "sourced_by", source)

    def add_script_reference(doc: dict[str, object], reference: str) -> None:
        ref = normalize_graph_path(reference)
        target = stable_id("script", ref)
        add_node({"id": target, "kind": "script", "path": ref, "title": Path(ref).name})
        add_edge(str(doc["id"]), target, "depends_on", ref)

    def add_command_reference(doc: dict[str, object], command: str) -> None:
        target = stable_id("command", command)
        add_node({"id": target, "kind": "command", "command": command, "title": command})
        add_edge(str(doc["id"]), target, "verifies", command)

    def add_decision_reference(doc: dict[str, object], snippet: str) -> None:
        target = stable_id("decision", f"{doc['path']}:{snippet}")
        add_node({"id": target, "kind": "decision", "title": snippet[:120], "summary": snippet, "source": doc["path"]})
        add_edge(str(doc["id"]), target, "implements", snippet)

    def add_semantic_reference(doc: dict[str, object], kind: str, label: str) -> None:
        target = stable_id(kind, f"{doc['path']}:{label}")
        add_node({
            "id": target,
            "kind": kind,
            "title": label[:120],
            "summary": label,
            "source": doc["path"],
        })
        add_edge(str(doc["id"]), target, SEMANTIC_RELATIONS.get(kind, "related_to"), label)

    def first_text(item: dict[str, object], keys: tuple[str, ...]) -> str:
        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return ""

    def dormant_title(item: dict[str, object], path: str) -> str:
        title = first_text(item, ("title", "name"))
        return title or Path(path).name

    def subagent_domain_records(manifest: dict[str, object]) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        domains = manifest.get("domains")
        if isinstance(domains, list):
            for domain in domains:
                if not isinstance(domain, dict):
                    continue
                name = first_text(domain, ("name", "domain", "slug"))
                slug = first_text(domain, ("slug",)) or slugify(name)
                brief = first_text(domain, ("brief", "path"))
                wave = domain.get("wave")
                depends_on = domain.get("depends_on")
                records.append({
                    "name": name or slug,
                    "slug": slug,
                    "brief": brief,
                    "wave": wave,
                    "depends_on": depends_on if isinstance(depends_on, list) else [],
                })
        if records:
            return records
        briefs = manifest.get("briefs", [])
        if isinstance(briefs, list):
            for brief in briefs:
                if not isinstance(brief, str):
                    continue
                slug = Path(brief).stem
                records.append({
                    "name": slug.replace("-", " "),
                    "slug": slug,
                    "brief": normalize_graph_path(brief),
                    "wave": None,
                    "depends_on": [],
                })
        return records

    def add_subagent_package(plan_dir: Path, manifest: dict[str, object]) -> None:
        package_rel = relpath(plan_dir, root)
        package_id = stable_id("subagent_package", package_rel)
        task = first_text(manifest, ("task",)) or plan_dir.name
        add_node({
            "id": package_id,
            "kind": "subagent_package",
            "path": package_rel,
            "title": task,
            "dispatch_mode": manifest.get("dispatch_mode", "sequential"),
        })

        brief_by_slug: dict[str, str] = {}
        for record in subagent_domain_records(manifest):
            slug = str(record.get("slug") or slugify(str(record.get("name", ""))))
            brief_path = normalize_graph_path(str(record.get("brief") or ""))
            if not brief_path:
                brief_path = f"{package_rel}/{slug}.md"
            brief_id = stable_id("subagent_brief", brief_path)
            brief_by_slug[slug] = brief_id
            node = {
                "id": brief_id,
                "kind": "subagent_brief",
                "path": brief_path,
                "title": str(record.get("name") or slug),
                "domain": str(record.get("name") or slug),
            }
            if record.get("wave") not in (None, ""):
                node["wave"] = record["wave"]
            add_node(node)
            add_edge(package_id, brief_id, "delegates_to", str(record.get("name") or slug))
            for dependency in record.get("depends_on", []):
                if not isinstance(dependency, str):
                    continue
                dep_id = brief_by_slug.get(dependency) or stable_id("subagent_brief", f"{package_rel}/{dependency}.md")
                add_node({
                    "id": dep_id,
                    "kind": "subagent_brief",
                    "path": f"{package_rel}/{dependency}.md",
                    "title": dependency,
                    "domain": dependency,
                })
                add_edge(brief_id, dep_id, "depends_on", dependency)

        results = manifest.get("results", [])
        if isinstance(results, list):
            for result in results:
                if not isinstance(result, dict):
                    continue
                result_path = normalize_graph_path(first_text(result, ("path",)))
                domain = first_text(result, ("domain",))
                slug = slugify(domain)
                result_id = stable_id("subagent_result", result_path or f"{package_rel}:{slug}:result")
                add_node({
                    "id": result_id,
                    "kind": "subagent_result",
                    "path": result_path,
                    "title": domain or slug,
                    "domain": domain or slug,
                    "status": first_text(result, ("status",)),
                    "summary": first_text(result, ("summary",)),
                })
                brief_id = brief_by_slug.get(slug)
                if brief_id:
                    add_edge(brief_id, result_id, "produces", first_text(result, ("status", "summary")))
                accepted_by = first_text(result, ("accepted_by",))
                if accepted_by:
                    actor_id = stable_id("actor", accepted_by)
                    add_node({"id": actor_id, "kind": "actor", "title": accepted_by})
                    add_edge(result_id, actor_id, "accepted_by", accepted_by)

    def add_dormant_node(item: dict[str, object], dormant_path: str, original_path: str = "") -> str:
        target = stable_id("dormant", dormant_path)
        node = {
            "id": target,
            "kind": "dormant",
            "path": dormant_path,
            "title": dormant_title(item, dormant_path),
        }
        if original_path:
            node["original_path"] = original_path
        add_node(node)
        return target

    for doc in docs:
        shard_doc = {key: value for key, value in doc.items() if key != "text"}
        append_shard_record(shard_doc)
        for chunk in chunk_records_by_path.get(str(doc["path"]), []):
            append_shard_record(chunk)

        doc_node = {
            "id": doc["id"],
            "kind": doc["type"],
            "path": doc["path"],
            "title": doc["title"],
            "summary": doc["summary"],
            "text_hash": doc["text_hash"],
        }
        for key in ["memory_schema", "thesis", "atomic", "tags", "properties", "moc", "links", "validation"]:
            if key in doc:
                doc_node[key] = doc[key]
        add_node(doc_node)
        for term in list(doc["terms"])[:8]:
            term_id = f"term:{term}"
            add_node({"id": term_id, "kind": "term", "title": term})
            add_edge(str(doc["id"]), term_id, "mentions", term)
        for source in doc["sources"]:
            add_source_edge(doc, source)
        text = str(doc.get("text", ""))
        for reference in referenced_paths(text):
            add_script_reference(doc, reference)
        for command in command_lines(text):
            add_command_reference(doc, command)
        for snippet in decision_snippets(text):
            add_decision_reference(doc, snippet)
        for kind, label in semantic_items(text):
            add_semantic_reference(doc, kind, label)

    promotion_log = memory / "promotion_log.jsonl"
    if promotion_log.exists():
        for line in promotion_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            trace = normalize_graph_path(str(item.get("trace", "")))
            note = normalize_graph_path(str(item.get("note", "")))
            trace_id = doc_id_by_path.get(trace)
            note_id = doc_id_by_path.get(note)
            if trace_id and note_id:
                add_edge(trace_id, note_id, "promotes", f"{trace} -> {note}")

    dormant_manifest = load_dormant_manifest(local_dir)
    dormant_node_by_path: dict[str, str] = {}
    items = dormant_manifest.get("items", [])
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            original_path = first_text(item, ("original_path", "path"))
            dormant_path = first_text(item, ("dormant_path", "dormant"))
            if not original_path or not dormant_path:
                continue
            original = normalize_graph_path(original_path)
            dormant = normalize_graph_path(dormant_path)
            source_id = doc_id_by_path.get(original)
            if not source_id:
                source_kind = first_text(item, ("kind",)) or "source"
                if "/decision-traces/" in f"/{original}":
                    source_kind = "trace"
                if source_kind == "dormant":
                    source_kind = "source"
                source_id = stable_id(source_kind, original)
                add_node({
                    "id": source_id,
                    "kind": source_kind,
                    "path": original,
                    "title": dormant_title(item, original),
                })
            dormant_id = add_dormant_node(item, dormant, original)
            dormant_node_by_path[dormant] = dormant_id
            evidence = first_text(item, ("source_run", "reason", "action"))
            add_edge(source_id, dormant_id, "archives", evidence)

    reactivations = dormant_manifest.get("reactivations", [])
    if isinstance(reactivations, list):
        for item in reactivations:
            if not isinstance(item, dict):
                continue
            dormant_path = first_text(item, ("dormant_path", "dormant", "from", "source"))
            note_path = first_text(item, ("note_path", "note", "reactivated_path", "to", "target"))
            if not dormant_path or not note_path:
                continue
            dormant = normalize_graph_path(dormant_path)
            note = normalize_graph_path(note_path)
            dormant_id = dormant_node_by_path.get(dormant) or add_dormant_node(item, dormant)
            note_id = doc_id_by_path.get(note)
            if not note_id:
                note_id = stable_id("note", note)
                add_node({"id": note_id, "kind": "note", "path": note, "title": Path(note).name})
            evidence = first_text(item, ("source_run", "reason", "run_id", "action"))
            add_edge(dormant_id, note_id, "reactivates", evidence)

    subagents_dir = local_dir / "subagents"
    if subagents_dir.exists():
        for manifest_path in sorted(subagents_dir.glob("*/manifest.json")):
            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(manifest_data, dict):
                add_subagent_package(manifest_path.parent, manifest_data)

    for node in sorted(nodes.values(), key=lambda item: str(item["id"])):
        append_jsonl(graph_dir / "nodes.jsonl", node)
    for edge in sorted(edges.values(), key=lambda item: str(item["id"])):
        append_jsonl(graph_dir / "edges.jsonl", edge)

    indexes = graph_dir / "indexes"
    indexes.mkdir(parents=True, exist_ok=True)
    by_kind: dict[str, list[str]] = {}
    by_path: dict[str, str] = {}
    by_relation: dict[str, list[str]] = {}
    for node in nodes.values():
        by_kind.setdefault(str(node["kind"]), []).append(str(node["id"]))
        if node.get("path"):
            by_path[str(node["path"])] = str(node["id"])
    for edge in edges.values():
        by_relation.setdefault(str(edge["type"]), []).append(str(edge["id"]))
    (indexes / "by-kind.json").write_text(json.dumps({key: sorted(value) for key, value in sorted(by_kind.items())}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (indexes / "by-path.json").write_text(json.dumps(dict(sorted(by_path.items())), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (indexes / "by-relation.json").write_text(json.dumps({key: sorted(value) for key, value in sorted(by_relation.items())}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    shards = []
    for meta in sorted(shard_meta.values(), key=lambda item: str(item["id"])):
        shards.append({
            "id": meta["id"],
            "path": meta["path"],
            "doc_count": meta["doc_count"],
            "terms": sorted(meta["terms"])[:64],
        })

    chunk_count = sum(len(chunks) for chunks in chunk_records_by_path.values())
    source_hashes = {str(doc["path"]): str(doc["text_hash"]) for doc in docs}
    write_chunk_cache(local_dir, {
        "documents": new_cache_docs,
        "source_hashes": source_hashes,
    })

    manifest = {
        "version": 2,
        "schema": MEMORY_SCHEMA,
        "storage": "sharded-jsonl",
        "embedding": "local-hash-v1",
        "vector_dims": VECTOR_DIMS,
        "chunking": CHUNKING_STRATEGY,
        "document_count": len(docs),
        "chunk_count": chunk_count,
        "record_count": len(docs) + chunk_count,
        "cache": {
            "path": relpath(chunk_cache_path(local_dir), root),
            "hits": cache_hits,
            "misses": cache_misses,
            "documents": len(new_cache_docs),
        },
        "source_hashes": source_hashes,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "shards": shards,
    }
    (memory / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (graph_dir / "manifest.json").write_text(
        json.dumps({
            "version": 1,
            "schema": GRAPH_SCHEMA,
            "node_file": "nodes.jsonl",
            "edge_file": "edges.jsonl",
            "source_manifest": "../manifest.json",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_kinds": sorted(by_kind),
            "edge_types": sorted(by_relation),
            "indexes": [
                "indexes/by-kind.json",
                "indexes/by-path.json",
                "indexes/by-relation.json",
            ],
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_jsonl(path: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def read_json(path: Path, default: object | None = None) -> object:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {} if default is None else default


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
    try:
        tmp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def frontmatter_value(text: str, key: str) -> str | None:
    in_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not in_frontmatter:
            in_frontmatter = True
            continue
        if stripped == "---" and in_frontmatter:
            break
        if in_frontmatter and stripped.startswith(f"{key}:"):
            return stripped.split(":", 1)[1].strip()
    return None


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def touch_index_path(local_dir: Path) -> Path:
    return local_dir / "memory" / "touch_index.json"


def load_touch_index(local_dir: Path) -> dict[str, object]:
    data = read_json(touch_index_path(local_dir), {"version": 1, "items": {}})
    if not isinstance(data, dict):
        return {"version": 1, "items": {}}
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    data.setdefault("version", 1)
    return data


def write_touch_index(local_dir: Path, data: dict[str, object]) -> None:
    data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(touch_index_path(local_dir), data)


def touch_entry(index: dict[str, object], path: str) -> dict[str, object]:
    items = index.get("items")
    if not isinstance(items, dict):
        return {}
    value = items.get(normalize_graph_path(path))
    return value if isinstance(value, dict) else {}


class TouchIndexLock:
    def __init__(self, local_dir: Path, timeout_seconds: float = 10.0) -> None:
        self.path = local_dir / "memory" / "touch_index.lock"
        self.timeout_seconds = timeout_seconds
        self.handle: int | None = None

    def __enter__(self) -> "TouchIndexLock":
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
                    raise TimeoutError(f"timed out waiting for memory touch lock: {self.path}") from exc
                time.sleep(0.025)

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.handle is not None:
            os.close(self.handle)
            self.handle = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def memory_kind_for_path(path: str) -> str:
    normalized = f"/{normalize_graph_path(path)}"
    if "/notes/" in normalized:
        return "note"
    if "/decision-traces/" in normalized:
        return "trace"
    if "/memory/dormant/" in normalized:
        return "dormant"
    return "memory"


def record_memory_touch(root: Path, path: str, reason: str = "", agent: str = "auto") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    ensure_memory_layout(local_dir)
    target = resolve_memory_reference(root, local_dir, path)
    if target is None:
        raise ValueError(f"memory path not found: {path}")
    rel = relpath(target.resolve(), root)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    kind = memory_kind_for_path(rel)
    event = {
        "timestamp": now,
        "path": rel,
        "kind": kind,
        "reason": reason,
    }
    with TouchIndexLock(local_dir):
        append_jsonl(local_dir / "memory" / "touches.jsonl", event)

        index = load_touch_index(local_dir)
        items = index.setdefault("items", {})
        if not isinstance(items, dict):
            items = {}
            index["items"] = items
        existing = items.get(rel)
        entry = existing if isinstance(existing, dict) else {}
        use_count = int(entry.get("use_count", 0)) + 1
        entry.update({
            "path": rel,
            "kind": kind,
            "use_count": use_count,
            "last_used_at": now,
            "last_reason": reason,
        })
        entry.setdefault("first_used_at", now)
        items[rel] = entry
        write_touch_index(local_dir, index)
    return {
        "path": rel,
        "kind": kind,
        "reason": reason,
        "use_count": use_count,
        "last_used_at": now,
        "touch_log": relpath(local_dir / "memory" / "touches.jsonl", root),
        "touch_index": relpath(touch_index_path(local_dir), root),
    }


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dream_run_id(root: Path) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    digest = hashlib.sha256(f"{root.resolve()}:{stamp}".encode("utf-8")).hexdigest()[:8]
    return f"{stamp}-{digest}"


def load_graph(root: Path, agent: str = "auto") -> dict[str, object]:
    local_dir = find_local_dir(root.resolve(), agent)
    graph_dir = local_dir / "memory" / "graph"
    manifest_path = graph_dir / "manifest.json"
    manifest: dict[str, object] = {}
    if manifest_path.exists():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
        except json.JSONDecodeError:
            manifest = {"error": "manifest is not valid JSON"}
    return {
        "graph_dir": graph_dir,
        "manifest": manifest,
        "nodes": read_jsonl(graph_dir / "nodes.jsonl"),
        "edges": read_jsonl(graph_dir / "edges.jsonl"),
    }


def query_graph(
    root: Path,
    agent: str = "auto",
    kind: str | None = None,
    path: str | None = None,
    node: str | None = None,
    relation: str | None = None,
    q: str | None = None,
) -> dict[str, object]:
    graph = load_graph(root, agent)
    nodes = list(graph["nodes"])  # type: ignore[arg-type]
    edges = list(graph["edges"])  # type: ignore[arg-type]
    if kind:
        nodes = [item for item in nodes if item.get("kind") == kind]
    if path:
        wanted = normalize_graph_path(path)
        nodes = [item for item in nodes if item.get("path") == wanted]
        node_ids = {str(item["id"]) for item in nodes if "id" in item}
        edges = [item for item in edges if item.get("from") in node_ids or item.get("to") in node_ids]
    if node:
        nodes = [item for item in nodes if item.get("id") == node]
        edges = [item for item in edges if item.get("from") == node or item.get("to") == node]
    if relation:
        edges = [item for item in edges if item.get("type") == relation]
    if q:
        wanted_terms = tokens(q)
        if wanted_terms:
            def haystack(item: dict[str, object]) -> str:
                return json.dumps(item, ensure_ascii=False, sort_keys=True).lower()

            matched_nodes = [
                item for item in nodes
                if all(term in haystack(item) for term in wanted_terms)
            ]
            matched_ids = {str(item["id"]) for item in matched_nodes if "id" in item}
            matched_edges = [
                item for item in edges
                if all(term in haystack(item) for term in wanted_terms)
                or item.get("from") in matched_ids
                or item.get("to") in matched_ids
            ]
            nodes = matched_nodes
            edges = matched_edges
    return {"nodes": nodes, "edges": edges, "manifest": graph["manifest"]}


def check_graph(root: Path, agent: str = "auto", strict: bool = False) -> dict[str, object]:
    graph = load_graph(root, agent)
    graph_dir = graph["graph_dir"]
    assert isinstance(graph_dir, Path)
    nodes = graph["nodes"]
    edges = graph["edges"]
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    errors: list[str] = []
    node_ids: set[str] = set()
    edge_ids: set[str] = set()
    for item in nodes:
        if not isinstance(item, dict):
            errors.append("malformed node record")
            continue
        node_id = item.get("id")
        if not node_id:
            errors.append("node missing id")
            continue
        if str(node_id) in node_ids:
            errors.append(f"duplicate node id: {node_id}")
        node_ids.add(str(node_id))
        if not item.get("kind"):
            errors.append(f"node missing kind: {node_id}")
    for item in edges:
        if not isinstance(item, dict):
            errors.append("malformed edge record")
            continue
        edge = item.get("id")
        source = item.get("from")
        target = item.get("to")
        edge_type = item.get("type")
        if not edge:
            errors.append("edge missing id")
            continue
        if str(edge) in edge_ids:
            errors.append(f"duplicate edge id: {edge}")
        edge_ids.add(str(edge))
        if not edge_type:
            errors.append(f"edge missing type: {edge}")
        if source not in node_ids:
            errors.append(f"dangling edge source: {edge}")
        if target not in node_ids:
            errors.append(f"dangling edge target: {edge}")
    for index_file in ["indexes/by-kind.json", "indexes/by-path.json", "indexes/by-relation.json"]:
        if not (graph_dir / index_file).is_file():
            errors.append(f"missing graph index: {index_file}")
    manifest = graph["manifest"]
    if isinstance(manifest, dict):
        if strict and manifest.get("schema") != GRAPH_SCHEMA:
            errors.append(f"manifest schema is not {GRAPH_SCHEMA}")
        if strict and manifest.get("node_count") != len(nodes):
            errors.append("manifest node_count does not match nodes.jsonl")
        if strict and manifest.get("edge_count") != len(edges):
            errors.append("manifest edge_count does not match edges.jsonl")
        if strict:
            for expected in ["indexes/by-kind.json", "indexes/by-path.json", "indexes/by-relation.json"]:
                indexes = manifest.get("indexes")
                if not isinstance(indexes, list) or expected not in indexes:
                    errors.append(f"manifest missing graph index entry: {expected}")
    elif strict:
        errors.append("manifest is missing or invalid")
    status = "ok" if not errors else "failed"
    return {
        "status": status,
        "errors": errors,
        "counts": {"nodes": len(nodes), "edges": len(edges)},
        "manifest": graph["manifest"],
    }


def doc_snapshot(doc: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in doc.items()
        if key in {"id", "type", "path", "title", "summary", "terms", "text_hash", "sources"}
    }


def resolve_memory_reference(root: Path, local_dir: Path, value: str) -> Path | None:
    ref = normalize_graph_path(value)
    if not ref:
        return None
    raw = Path(ref)
    candidates = [raw] if raw.is_absolute() else [root / raw, local_dir / raw]
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        if resolved.is_file():
            return resolved
    return None


def local_relative_path(path: Path, local_dir: Path, root: Path) -> str:
    try:
        return path.relative_to(local_dir).as_posix()
    except ValueError:
        return relpath(path, root)


DREAM_SCHEMA = "fable-harness-memory-dream-v2"
DREAM_NOTE_COMPACT_BYTES = 2400
DREAM_NOTE_STALE_DAYS = 180
DREAM_CONTEXT_RELEVANCE_THRESHOLD = 0.35


def dream_action(
    action: str,
    path: str,
    reason: str,
    mode: str,
    risk: str,
    safe_to_apply: bool,
    requires_review: bool,
    source: str,
    signals: dict[str, object] | None = None,
    **extra: object,
) -> dict[str, object]:
    item: dict[str, object] = {
        "action": action,
        "path": normalize_graph_path(path),
        "reason": reason,
        "mode": mode,
        "risk": risk,
        "safe_to_apply": safe_to_apply,
        "requires_review": requires_review,
        "source": source,
        "signals": signals or {},
    }
    item.update(extra)
    return item


def note_dream_signals(root: Path, doc: dict[str, object], touch_index: dict[str, object]) -> dict[str, object]:
    path_value = normalize_graph_path(str(doc.get("path", "")))
    path = (root / path_value).resolve()
    text = str(doc.get("text", ""))
    size = path.stat().st_size if path.is_file() else len(text.encode("utf-8"))
    verified = frontmatter_value(text, "last_verified") or ""
    verified_date = parse_date(verified) if verified else None
    stale_days = None
    if verified_date:
        stale_days = (dt.date.today() - verified_date).days
    touch = touch_entry(touch_index, path_value)
    return {
        "size_bytes": size,
        "size_limit_bytes": DREAM_NOTE_COMPACT_BYTES,
        "last_verified": verified,
        "stale_days": stale_days,
        "use_count": int(touch.get("use_count", 0)) if touch else 0,
        "last_used_at": str(touch.get("last_used_at", "")) if touch else "",
        "last_reason": str(touch.get("last_reason", "")) if touch else "",
    }


def compact_note_reason(signals: dict[str, object]) -> str:
    reasons: list[str] = []
    if int(signals.get("size_bytes", 0)) > DREAM_NOTE_COMPACT_BYTES:
        reasons.append(f"note exceeds {DREAM_NOTE_COMPACT_BYTES} bytes")
    stale_days = signals.get("stale_days")
    if isinstance(stale_days, int) and stale_days > DREAM_NOTE_STALE_DAYS:
        reasons.append(f"last_verified is older than {DREAM_NOTE_STALE_DAYS} days")
    return "; ".join(reasons)


def review_only_dream_actions(root: Path, docs: list[dict[str, object]], touch_index: dict[str, object]) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    for doc in docs:
        if doc.get("type") != "note":
            continue
        path = normalize_graph_path(str(doc.get("path", "")))
        signals = note_dream_signals(root, doc, touch_index)
        reason = compact_note_reason(signals)
        if not reason:
            continue
        actions.append(dream_action(
            "compact-note",
            path,
            reason + "; create or update a compact canonical note only after orchestrator review",
            "semantic-review",
            "medium",
            False,
            True,
            "active-index",
            signals,
        ))
    return actions


def dream_action_context_text(action: dict[str, object]) -> str:
    signals = action.get("signals")
    signal_text = ""
    if isinstance(signals, dict):
        signal_text = " ".join(str(value) for value in signals.values() if isinstance(value, (str, int)))
    return " ".join([
        str(action.get("action", "")),
        str(action.get("path", "")),
        str(action.get("reason", "")),
        str(action.get("source", "")),
        str(action.get("dormant_copy", "")),
        signal_text,
    ])


def dream_context_relevance(action: dict[str, object], context: str) -> dict[str, object]:
    context = context.strip()
    if not context:
        return {
            "context": "",
            "score": 0.0,
            "threshold": DREAM_CONTEXT_RELEVANCE_THRESHOLD,
            "decision": "no-context",
        }
    action_text = dream_action_context_text(action)
    context_terms = set(top_terms(context, limit=32))
    action_terms = set(top_terms(action_text, limit=64))
    lexical = 0.0
    if context_terms:
        lexical = len(context_terms & action_terms) / len(context_terms)
    semantic = max(0.0, cosine(vector(context), vector(action_text)))
    score = round(max(lexical, semantic * 0.5), 4)
    decision = "context-cold" if score < DREAM_CONTEXT_RELEVANCE_THRESHOLD else "agent-review"
    return {
        "context": context,
        "score": score,
        "threshold": DREAM_CONTEXT_RELEVANCE_THRESHOLD,
        "decision": decision,
        "overlap_terms": sorted(context_terms & action_terms),
    }


def annotate_dream_actions_for_context(actions: list[dict[str, object]], context: str) -> None:
    for action in actions:
        relevance = dream_context_relevance(action, context)
        signals = action.setdefault("signals", {})
        if isinstance(signals, dict):
            signals["context_relevance"] = relevance
        if not context:
            continue
        if (
            action.get("mode") == "mechanical"
            and action.get("risk") == "low"
            and action.get("safe_to_apply") is True
            and action.get("requires_review") is False
            and relevance["decision"] == "agent-review"
        ):
            action["safe_to_apply"] = False
            action["requires_review"] = True
            action["mode"] = "agent-review"
            action["risk"] = "medium"
            action["reason"] = str(action.get("reason", "")) + "; held for agent review because it is relevant to the current context"


def write_agent_review_packet(run_dir: Path, diff: dict[str, object], context: str) -> Path:
    actions = diff.get("actions", [])
    review_actions = [
        action
        for action in actions
        if isinstance(action, dict) and action.get("requires_review") is True
    ] if isinstance(actions, list) else []
    lines = [
        "# Agent Memory Review",
        "",
        f"- Run ID: `{diff.get('run_id', run_dir.name)}`",
        f"- Context: {context or '(none supplied)'}",
        f"- Review actions: {len(review_actions)}",
        "",
        "## Orchestrator Instructions",
        "",
        "- Decide whether each item is still needed for the current task, plan, or project stage.",
        "- Keep active memory when it is relevant to current work.",
        "- Compact or archive only after preserving durable facts in canonical notes.",
        "- Escalate to the user only for product decisions, conflicting canonical decisions, or possible loss of primary evidence.",
        "",
        "## Review Queue",
        "",
    ]
    if not review_actions:
        lines.append("- none")
    for action in review_actions:
        signals = action.get("signals", {})
        relevance = signals.get("context_relevance", {}) if isinstance(signals, dict) else {}
        score = relevance.get("score", "") if isinstance(relevance, dict) else ""
        lines.extend([
            f"- `{action.get('action', '')}`: `{action.get('path', '')}`",
            f"  - mode: {action.get('mode', '')}",
            f"  - risk: {action.get('risk', '')}",
            f"  - reason: {action.get('reason', '')}",
            f"  - context_score: {score}",
        ])
    review_path = run_dir / "agent-review.md"
    review_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return review_path


def write_auto_applied_packet(run_dir: Path, diff: dict[str, object]) -> Path:
    actions = diff.get("actions", [])
    auto_path = run_dir / "auto-applied.jsonl"
    auto_path.write_text("", encoding="utf-8")
    if isinstance(actions, list):
        for action in actions:
            if not isinstance(action, dict):
                continue
            if action.get("safe_to_apply") is True and action.get("requires_review") is False:
                append_jsonl(auto_path, {
                    "action": action.get("action", ""),
                    "path": action.get("path", ""),
                    "mode": action.get("mode", ""),
                    "risk": action.get("risk", ""),
                    "reason": action.get("reason", ""),
                    "source": action.get("source", ""),
                    "signals": action.get("signals", {}),
                })
    return auto_path


def initialize_agent_decisions_packet(run_dir: Path) -> Path:
    decisions_path = run_dir / "agent-decisions.jsonl"
    decisions_path.write_text("", encoding="utf-8")
    return decisions_path


def create_dream_plan(root: Path, agent: str = "auto", context: str = "") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    memory_dir = local_dir / "memory"
    dreams_dir = memory_dir / "dreams"
    runs_dir = dreams_dir / "runs"
    run_id = dream_run_id(root)
    run_dir = runs_dir / run_id
    while run_dir.exists():
        run_id = dream_run_id(root)
        run_dir = runs_dir / run_id

    input_dir = run_dir / "input"
    output_dir = run_dir / "output"
    dormant_dir = output_dir / "dormant-items"
    dormant_dir.mkdir(parents=True, exist_ok=True)
    created_at = dt.datetime.now(dt.timezone.utc).isoformat()

    docs = iter_markdown_docs(local_dir, dormant_excluded_paths(local_dir))
    active_index = {
        "generated_at": created_at,
        "local_dir": relpath(local_dir, root),
        "documents": [doc_snapshot(doc) for doc in docs],
    }
    write_json(input_dir / "active-index.json", active_index)

    existing_dormant = read_json(dreams_dir / "dormant-index.json", {"items": []})
    write_json(input_dir / "dormant-index.json", existing_dormant)

    touch_index = load_touch_index(local_dir)
    write_json(input_dir / "touch-index.json", touch_index)

    graph = load_graph(root, agent)
    graph_snapshot = {
        "manifest": graph["manifest"],
        "nodes": graph["nodes"],
        "edges": graph["edges"],
    }
    write_json(input_dir / "graph-snapshot.json", graph_snapshot)

    actions: list[dict[str, object]] = []
    dormant_items: list[dict[str, object]] = []
    seen_traces: set[str] = set()
    promotion_log = read_jsonl(memory_dir / "promotion_log.jsonl")
    for entry in promotion_log:
        trace_ref = str(entry.get("trace", ""))
        trace_path = resolve_memory_reference(root, local_dir, trace_ref)
        if trace_path is None:
            continue
        trace_rel = relpath(trace_path, root)
        if trace_rel in seen_traces:
            continue
        seen_traces.add(trace_rel)
        text = trace_path.read_text(encoding="utf-8")
        dormant_rel = local_relative_path(trace_path, local_dir, root)
        dormant_path = dormant_dir / dormant_rel
        dormant_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(trace_path, dormant_path)
        trace_hash = file_hash(trace_path)
        dormant_copy = relpath(dormant_path, run_dir)
        item = {
            "path": trace_rel,
            "title": file_title(text, trace_path.stem),
            "summary": compact_summary(text),
            "terms": top_terms(text),
            "sha256": trace_hash,
            "copy": dormant_copy,
        }
        dormant_items.append(item)
        actions.append(dream_action(
            "archive-promoted-trace",
            trace_rel,
            "trace has promotion-log evidence; dry-run copied it into dormant review output",
            "mechanical",
            "low",
            True,
            False,
            "promotion-log",
            {
                "promotion_log": True,
                "sha256": trace_hash,
                "title": item["title"],
            },
            dormant_copy=dormant_copy,
            sha256=trace_hash,
        ))

    actions.extend(review_only_dream_actions(root, docs, touch_index))
    annotate_dream_actions_for_context(actions, context)

    maintenance_report = {
        "generated_at": created_at,
        "mode": "dream-plan-dry-run",
        "context": context,
        "candidates": actions,
        "counts": {
            "active_documents": len(docs),
            "dormant_items": len(dormant_items),
        },
    }
    write_json(input_dir / "maintenance-report.json", maintenance_report)

    write_json(output_dir / "dormant-index.json", {
        "generated_at": created_at,
        "items": dormant_items,
    })
    diff = {
        "schema": DREAM_SCHEMA,
        "version": 2,
        "run_id": run_id,
        "generated_at": created_at,
        "dry_run": True,
        "context": context,
        "actions": actions,
    }
    write_json(run_dir / "diff.json", diff)

    manifest = {
        "version": 1,
        "kind": "memory-dream-plan",
        "schema": DREAM_SCHEMA,
        "run_id": run_id,
        "created_at": created_at,
        "root": str(root),
        "local_dir": relpath(local_dir, root),
        "dry_run": True,
        "context": context,
        "action_count": len(actions),
        "safe_action_count": len([action for action in actions if action.get("safe_to_apply") is True]),
        "review_action_count": len([action for action in actions if action.get("requires_review") is True]),
        "inputs": [
            "input/active-index.json",
            "input/dormant-index.json",
            "input/touch-index.json",
            "input/graph-snapshot.json",
            "input/maintenance-report.json",
        ],
        "outputs": [
            "output/dormant-index.json",
            "output/dormant-items",
            "diff.json",
            "report.md",
        ],
    }
    write_json(run_dir / "manifest.json", manifest)

    lines = [
        "# Memory Dream Plan",
        "",
        f"- Run ID: `{run_id}`",
        f"- Created: {created_at}",
        f"- Mode: dry-run",
        f"- Context: {context or '(none supplied)'}",
        f"- Actions: {len(actions)}",
        "",
        "## Actions",
        "",
    ]
    if actions:
        for action in actions:
            if action.get("dormant_copy"):
                lines.append(f"- {action['action']} ({action['mode']}, {action['risk']}): `{action['path']}` -> `{action['dormant_copy']}`")
            else:
                lines.append(f"- {action['action']} ({action['mode']}, {action['risk']}): `{action['path']}`")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Review Files",
        "",
        "- `manifest.json`",
        "- `diff.json`",
        "- `input/active-index.json`",
        "- `output/dormant-items/`",
    ])
    (run_dir / "report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    append_jsonl(dreams_dir / "log.jsonl", {
        "run_id": run_id,
        "run_dir": relpath(run_dir, root),
        "created_at": created_at,
        "action_count": len(actions),
        "status": "planned",
    })
    return {"run_id": run_id, "run_dir": str(run_dir), "action_count": len(actions)}


def resolve_dream_run(root: Path, local_dir: Path, run: str) -> Path:
    raw = Path(run)
    candidates = [raw] if raw.is_absolute() else [
        root / raw,
        local_dir / "memory" / "dreams" / "runs" / run,
    ]
    runs_dir = (local_dir / "memory" / "dreams" / "runs").resolve()
    for candidate in candidates:
        resolved = candidate.resolve()
        if not resolved.exists():
            continue
        if not is_relative_to(resolved, runs_dir):
            raise ValueError(f"dream run is outside memory dreams runs directory: {run}")
        if not resolved.is_dir():
            raise ValueError(f"dream run is not a directory: {run}")
        return resolved
    raise ValueError(f"dream run not found: {run}")


def dormant_item_tail(dormant_copy: str, original_path: str) -> str:
    value = normalize_graph_path(dormant_copy)
    prefix = "output/dormant-items/"
    if value.startswith(prefix):
        tail = value[len(prefix):]
    else:
        tail = normalize_graph_path(original_path)
    return tail.lstrip("/")


def upsert_dormant_item(
    manifest: dict[str, object],
    original_path: str,
    dormant_path: str,
    sha256: str,
    run_id: str,
    action: dict[str, object],
) -> bool:
    items = manifest.setdefault("items", [])
    if not isinstance(items, list):
        items = []
        manifest["items"] = items
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("original_path") == original_path and item.get("sha256") == sha256:
            item.update({
                "dormant_path": dormant_path,
                "state": "dormant",
                "last_applied_run": run_id,
            })
            return False
    items.append({
        "id": hashlib.sha256(f"{original_path}:{sha256}".encode("utf-8")).hexdigest()[:20],
        "original_path": original_path,
        "dormant_path": dormant_path,
        "sha256": sha256,
        "state": "dormant",
        "archived_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_run": run_id,
        "action": action.get("action", "archive-promoted-trace"),
        "reason": action.get("reason", ""),
    })
    return True


def apply_dream_run(root: Path, run: str, agent: str = "auto") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    run_dir = resolve_dream_run(root, local_dir, run)
    diff = read_json(run_dir / "diff.json")
    if not isinstance(diff, dict):
        raise ValueError("dream run diff.json must contain an object")
    if diff.get("schema") != DREAM_SCHEMA or diff.get("version") != 2:
        raise ValueError(f"dream run diff.json schema must be {DREAM_SCHEMA} version 2")
    actions = diff.get("actions")
    if not isinstance(actions, list):
        raise ValueError("dream run diff.json is missing actions")
    run_id = str(diff.get("run_id") or run_dir.name)

    manifest = load_dormant_manifest(local_dir)
    copied = 0
    new_items = 0
    skipped_review_actions = 0
    skipped_unsafe_actions = 0
    skipped_unsupported_actions = 0
    unsupported_actions: list[dict[str, object]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        safe_to_apply = action.get("safe_to_apply")
        requires_review = action.get("requires_review")
        if requires_review is True:
            skipped_review_actions += 1
            continue
        if safe_to_apply is not True or requires_review is not False:
            skipped_unsafe_actions += 1
            continue
        if action.get("action") != "archive-promoted-trace":
            skipped_unsupported_actions += 1
            unsupported_actions.append({
                "action": action.get("action", ""),
                "path": action.get("path", ""),
                "reason": "safe action type is not supported by this apply implementation",
            })
            continue
        original_value = action.get("path")
        dormant_copy_value = action.get("dormant_copy")
        sha256_value = action.get("sha256")
        if not isinstance(original_value, str) or not isinstance(dormant_copy_value, str) or not isinstance(sha256_value, str):
            raise ValueError("archive-promoted-trace action requires path, dormant_copy, and sha256")
        original_ref = Path(normalize_graph_path(original_value))
        source_path = (original_ref if original_ref.is_absolute() else root / original_ref).resolve()
        if not is_relative_to(source_path, root):
            raise ValueError(f"dream action path is outside workspace: {original_value}")
        original_path = relpath(source_path, root)
        if not source_path.is_file():
            raise ValueError(f"dream action source is missing: {original_path}")
        if file_hash(source_path) != sha256_value:
            raise ValueError(f"dream action source hash changed: {original_path}")

        dormant_copy = (run_dir / normalize_graph_path(dormant_copy_value)).resolve()
        if not is_relative_to(dormant_copy, run_dir):
            raise ValueError(f"dream dormant copy is outside the run: {dormant_copy_value}")
        if not dormant_copy.is_file():
            raise ValueError(f"dream dormant copy is missing: {dormant_copy_value}")
        if file_hash(dormant_copy) != sha256_value:
            raise ValueError(f"dream dormant copy hash does not match source: {dormant_copy_value}")

        items_dir = (local_dir / "memory" / "dormant" / "items").resolve()
        destination = (items_dir / dormant_item_tail(dormant_copy_value, original_path)).resolve()
        if not is_relative_to(destination, items_dir):
            raise ValueError(f"dream dormant destination is outside dormant items: {dormant_copy_value}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dormant_copy, destination)
        copied += 1
        if upsert_dormant_item(
            manifest,
            original_path,
            relpath(destination, root),
            sha256_value,
            run_id,
            action,
        ):
            new_items += 1

    write_dormant_manifest(local_dir, manifest)
    append_jsonl(local_dir / "memory" / "dreams" / "log.jsonl", {
        "run_id": run_id,
        "run_dir": relpath(run_dir, root),
        "applied_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "copied": copied,
        "new_items": new_items,
        "skipped_review_actions": skipped_review_actions,
        "skipped_unsafe_actions": skipped_unsafe_actions,
        "skipped_unsupported_actions": skipped_unsupported_actions,
        "unsupported_actions": unsupported_actions,
        "status": "applied",
    })
    memory_manifest = build_memory(root, agent)
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "copied": copied,
        "new_items": new_items,
        "skipped_review_actions": skipped_review_actions,
        "skipped_unsafe_actions": skipped_unsafe_actions,
        "skipped_unsupported_actions": skipped_unsupported_actions,
        "unsupported_actions": unsupported_actions,
        "dormant_manifest": str(dormant_manifest_path(local_dir)),
        "memory_document_count": memory_manifest["document_count"],
    }


def maintain_memory_dream(
    root: Path,
    agent: str = "auto",
    context: str = "",
    auto_safe: bool = False,
    agent_review: bool = True,
) -> dict[str, object]:
    plan = create_dream_plan(root, agent, context)
    run_dir = Path(str(plan["run_dir"]))
    diff = read_json(run_dir / "diff.json")
    if not isinstance(diff, dict):
        raise ValueError("dream run diff.json must contain an object")

    review_path: Path | None = None
    decisions_path: Path | None = None
    if agent_review:
        review_path = write_agent_review_packet(run_dir, diff, context)
        decisions_path = initialize_agent_decisions_packet(run_dir)

    applied = {
        "copied": 0,
        "new_items": 0,
        "skipped_review_actions": 0,
        "skipped_unsafe_actions": 0,
        "skipped_unsupported_actions": 0,
        "unsupported_actions": [],
        "memory_document_count": None,
    }
    auto_applied_path: Path | None = None
    if auto_safe:
        applied = apply_dream_run(root, str(run_dir), agent)
        auto_applied_path = write_auto_applied_packet(run_dir, diff)

    actions = diff.get("actions", [])
    review_action_count = len([
        action
        for action in actions
        if isinstance(action, dict) and action.get("requires_review") is True
    ]) if isinstance(actions, list) else 0
    safe_action_count = len([
        action
        for action in actions
        if isinstance(action, dict) and action.get("safe_to_apply") is True
    ]) if isinstance(actions, list) else 0

    manifest_path = run_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if isinstance(manifest, dict):
        manifest["kind"] = "memory-dream-maintenance"
        manifest["auto_safe"] = auto_safe
        manifest["agent_review"] = relpath(review_path, run_dir) if review_path else ""
        manifest["agent_decisions"] = relpath(decisions_path, run_dir) if decisions_path else ""
        manifest["auto_applied_log"] = relpath(auto_applied_path, run_dir) if auto_applied_path else ""
        manifest["review_action_count"] = review_action_count
        manifest["safe_action_count"] = safe_action_count
        manifest["auto_applied"] = {
            "copied": applied.get("copied", 0),
            "new_items": applied.get("new_items", 0),
            "skipped_review_actions": applied.get("skipped_review_actions", 0),
            "skipped_unsafe_actions": applied.get("skipped_unsafe_actions", 0),
            "skipped_unsupported_actions": applied.get("skipped_unsupported_actions", 0),
        }
        outputs = manifest.setdefault("outputs", [])
        if isinstance(outputs, list) and review_path:
            outputs.append("agent-review.md")
        if isinstance(outputs, list) and decisions_path:
            outputs.append("agent-decisions.jsonl")
        if isinstance(outputs, list) and auto_applied_path:
            outputs.append("auto-applied.jsonl")
        write_json(manifest_path, manifest)

    local_dir = find_local_dir(root.resolve(), agent)
    append_jsonl(local_dir / "memory" / "dreams" / "log.jsonl", {
        "run_id": plan["run_id"],
        "run_dir": relpath(run_dir, root.resolve()),
        "maintained_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "context": context,
        "auto_safe": auto_safe,
        "agent_review": relpath(review_path, root.resolve()) if review_path else "",
        "safe_action_count": safe_action_count,
        "review_action_count": review_action_count,
        "copied": applied.get("copied", 0),
        "status": "maintained",
    })

    return {
        "run_id": plan["run_id"],
        "run_dir": str(run_dir),
        "context": context,
        "auto_safe": auto_safe,
        "safe_action_count": safe_action_count,
        "review_action_count": review_action_count,
        "agent_review": str(review_path) if review_path else "",
        "agent_decisions": str(decisions_path) if decisions_path else "",
        "auto_applied_log": str(auto_applied_path) if auto_applied_path else "",
        "auto_applied": applied,
    }


def dormant_item_kind(item: dict[str, object], original_path: str) -> str:
    kind = str(item.get("kind", "")).strip()
    if kind:
        return kind
    normalized = f"/{normalize_graph_path(original_path)}"
    if "/decision-traces/" in normalized:
        return "trace"
    if "/notes/" in normalized:
        return "note"
    return "dormant"


def search_dormant_memory(root: Path, query: str, agent: str = "auto", limit: int = 5) -> list[dict[str, object]]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    manifest = load_dormant_manifest(local_dir)
    query_terms = set(top_terms(query, limit=32))
    query_vector = vector(query)
    results: list[dict[str, object]] = []
    items = manifest.get("items", [])
    if not isinstance(items, list):
        return results
    for item in items:
        if not isinstance(item, dict) or item.get("state") != "dormant":
            continue
        dormant_value = item.get("dormant_path")
        original_value = item.get("original_path") or item.get("path")
        if not isinstance(dormant_value, str) or not isinstance(original_value, str):
            continue
        dormant_path = normalize_graph_path(dormant_value)
        original_path = normalize_graph_path(original_value)
        raw_path = Path(dormant_path)
        path = (raw_path if raw_path.is_absolute() else root / raw_path).resolve()
        if not is_relative_to(path, root) or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        terms = set(top_terms(text, limit=64))
        score = cosine(query_vector, vector(text))
        if query_terms:
            score += len(query_terms.intersection(terms)) * 0.05
        if score <= 0:
            continue
        results.append({
            "score": round(score, 6),
            "title": str(item.get("title") or file_title(text, Path(original_path).stem)),
            "original_path": original_path,
            "dormant_path": dormant_path,
            "kind": dormant_item_kind(item, original_path),
            "summary": compact_summary(text),
        })
    results.sort(key=lambda item: (-float(item["score"]), str(item["original_path"])))
    return results[:limit]


def note_path(local_dir: Path, category: str, area: str | None, topic: str) -> Path:
    pieces = [slugify(category)]
    if area:
        pieces.append(slugify(area))
    pieces.append(slugify(topic) + ".md")
    return local_dir / "notes" / Path(*pieces)


def create_note(
    root: Path,
    category: str,
    area: str | None,
    topic: str,
    title: str | None = None,
    source_trace: Path | None = None,
    body: str | None = None,
    agent: str = "auto",
) -> Path:
    local_dir = find_local_dir(root.resolve(), agent)
    path = note_path(local_dir, category, area, topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    title = title or topic.replace("-", " ").title()
    scope = "/".join(slugify(piece) for piece in [category, area, topic] if piece)
    category_slug = slugify(category)
    area_slug = slugify(area) if area else ""
    topic_slug = slugify(topic)
    moc_rel = relpath(note_moc_path(local_dir, category_slug), path.parent)
    tags = [f"category/{category_slug}"]
    if area_slug:
        tags.append(f"area/{area_slug}")
    tags.append(f"topic/{topic_slug}")
    properties = [f"category={category_slug}", f"topic={topic_slug}", f"scope={scope}"]
    if area_slug:
        properties.insert(1, f"area={area_slug}")
    tag_lines = "".join(f"  - {tag}\n" for tag in tags)
    property_lines = "".join(f"  - {prop}\n" for prop in properties)
    source_block = ""
    if source_trace:
        source_block = f"  - {relpath(source_trace.resolve(), path.parent)}\n"
    sources_section = source_block
    default_body = """## Durable Fact Or Decision

-

## Connections

- MOC: `{moc_rel}`
- Related:

## Validation

- Atomic: one idea only.
- Thesis title: the title states the claim.
- Connects: this note links to its MOC.
- Unique: scope is unique among active canonical notes.
- Metadata: tags and properties are queryable.

## Evidence

-

## Operational Use

-

## Revalidation

-""".format(moc_rel=moc_rel)
    body_text = body or default_body
    content = f"""# {title}

---
memory_schema: atomic-v1
type: canonical-decision
status: active
scope: {scope}
canonical: true
thesis: {title}
atomic: true
tags:
{tag_lines}properties:
{property_lines}moc: {moc_rel}
links:
  - {moc_rel}
sources:
{sources_section}last_verified: {dt.date.today().isoformat()}
supersedes:
validation:
  - atomic
  - thesis-title
  - connects
  - unique
  - metadata
---

{body_text}
"""
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    update_notes_index(local_dir)
    build_memory(root, agent)
    return path


def bounded_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def lexical_relevance(query_terms: set[str], record_terms: set[str]) -> float:
    if not query_terms:
        return 0.0
    return bounded_score(len(query_terms.intersection(record_terms)) / max(1, len(query_terms)))


def graph_relevance(query_terms: set[str], record: dict[str, object]) -> float:
    graph_terms = {str(term) for term in record.get("graph_terms", [])}
    if not query_terms or not graph_terms:
        return 0.0
    return bounded_score(len(query_terms.intersection(graph_terms)) / max(1, len(query_terms)))


def rerank_relevance(query: str, query_terms: set[str], record: dict[str, object]) -> float:
    haystack_parts = [
        str(record.get("title", "")),
        str(record.get("thesis", "")),
        str(record.get("heading", "")),
        str(record.get("summary", "")),
        str(record.get("snippet", "")),
        " ".join(str(tag) for tag in record.get("tags", [])),
        " ".join(str(prop) for prop in record.get("properties", [])),
        str(record.get("moc", "")),
        " ".join(str(link) for link in record.get("links", [])),
        str(record.get("path", "")),
    ]
    haystack = " ".join(haystack_parts).lower()
    score = 0.0
    normalized_query = " ".join(tokens(query)).lower()
    if normalized_query and normalized_query in haystack:
        score += 0.45
    if query_terms:
        title_heading = " ".join(haystack_parts[:2]).lower()
        heading_hits = sum(1 for term in query_terms if term in title_heading)
        snippet_hits = sum(1 for term in query_terms if term in haystack)
        score += min(0.35, heading_hits * 0.07)
        score += min(0.20, snippet_hits * 0.03)
    if record.get("kind") == "chunk":
        score += 0.08
    return bounded_score(score)


def score_memory_record(query: str, query_terms: set[str], query_vector: list[list[float]], record: dict[str, object]) -> tuple[float, dict[str, float]]:
    record_terms = {str(term) for term in record.get("terms", [])}
    vector_score = bounded_score(cosine(query_vector, record.get("vector", [])))
    lexical_score = lexical_relevance(query_terms, record_terms)
    graph_score = graph_relevance(query_terms, record)
    rerank_score = rerank_relevance(query, query_terms, record)
    type_boost = 0.05 if record.get("type") == "note" else 0.0
    score = (
        vector_score * HYBRID_SCORE_WEIGHTS["vector"]
        + lexical_score * HYBRID_SCORE_WEIGHTS["lexical"]
        + graph_score * HYBRID_SCORE_WEIGHTS["graph"]
        + rerank_score * HYBRID_SCORE_WEIGHTS["rerank"]
        + type_boost
    )
    return score, {
        "vector": round(vector_score, 6),
        "lexical": round(lexical_score, 6),
        "graph": round(graph_score, 6),
        "rerank": round(rerank_score, 6),
        "type_boost": round(type_boost, 6),
    }


def search_result(record: dict[str, object], shard_id: str, score: float, breakdown: dict[str, float]) -> dict[str, object]:
    path = str(record.get("parent_path") or record.get("path", ""))
    start_line = record.get("start_line")
    end_line = record.get("end_line")
    if isinstance(start_line, int):
        citation = str(record.get("citation") or citation_for(path, start_line, int(end_line or start_line)))
    else:
        citation = str(record.get("citation") or citation_for(path))
    result = {
        "score": round(score, 6),
        "path": path,
        "title": record.get("title", ""),
        "type": record.get("type", ""),
        "kind": record.get("kind", "document"),
        "summary": record.get("summary", ""),
        "snippet": record.get("snippet") or record.get("summary", ""),
        "heading": record.get("heading", record.get("title", "")),
        "citation": citation,
        "score_breakdown": breakdown,
        "shard": shard_id,
    }
    if isinstance(start_line, int):
        result["start_line"] = start_line
    if isinstance(end_line, int):
        result["end_line"] = end_line
    if record.get("parent_id"):
        result["parent_id"] = record["parent_id"]
    for key in ["memory_schema", "thesis", "atomic", "tags", "properties", "moc", "links", "validation"]:
        if key in record:
            result[key] = record[key]
    return result


def diversify_results(results: list[dict[str, object]]) -> list[dict[str, object]]:
    parent_counts: dict[str, int] = {}
    adjusted: list[dict[str, object]] = []
    for item in sorted(results, key=lambda value: -float(value["score"])):
        parent = str(item.get("parent_id") or item.get("path"))
        count = parent_counts.get(parent, 0)
        if count:
            item = dict(item)
            penalty = min(0.12, count * 0.04)
            item["score"] = round(max(0.0, float(item["score"]) - penalty), 6)
            breakdown = dict(item.get("score_breakdown", {}))
            breakdown["diversity_penalty"] = round(penalty, 6)
            item["score_breakdown"] = breakdown
        parent_counts[parent] = count + 1
        adjusted.append(item)
    adjusted.sort(key=lambda item: (0 if item.get("type") == "note" else 1, -float(item["score"]), str(item.get("path", "")), int(item.get("start_line", 0) or 0)))
    return adjusted


def reactivation_body(query: str, candidate: dict[str, object], dormant_text: str) -> str:
    summary = compact_summary(dormant_text, limit=700) or "No compact excerpt was available."
    original_path = normalize_graph_path(str(candidate["original_path"]))
    dormant_path = normalize_graph_path(str(candidate["dormant_path"]))
    return "\n".join([
        "## Durable Fact Or Decision",
        "",
        f"Dormant evidence matched `{query}` and was reactivated as a compact active note.",
        "",
        "## Dormant Evidence",
        "",
        f"- Original path: `{original_path}`",
        f"- Dormant path: `{dormant_path}`",
        f"- Matched excerpt: {summary}",
        "",
        "## Operational Use",
        "",
        "Use this note as the active retrieval surface and keep the dormant file as source evidence.",
        "",
        "## Revalidation",
        "",
        "- Re-run memory graph checks after changing dormant reactivation records.",
    ])


def upsert_reactivation(
    manifest: dict[str, object],
    entry: dict[str, object],
) -> None:
    reactivations = manifest.setdefault("reactivations", [])
    if not isinstance(reactivations, list):
        reactivations = []
        manifest["reactivations"] = reactivations
    for existing in reactivations:
        if not isinstance(existing, dict):
            continue
        if (
            existing.get("query") == entry.get("query")
            and existing.get("dormant_path") == entry.get("dormant_path")
            and existing.get("note_path") == entry.get("note_path")
        ):
            existing.update(entry)
            return
    reactivations.append(entry)


def reactivate_dormant_memory(
    root: Path,
    query: str,
    category: str,
    area: str | None,
    topic: str,
    agent: str = "auto",
    apply: bool = False,
) -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    target_note = note_path(local_dir, category, area, topic)
    note_rel = relpath(target_note, root)
    matches = search_dormant_memory(root, query, agent=agent, limit=1)
    if not matches:
        return {
            "status": "not-found",
            "query": query,
            "note_path": note_rel,
            "candidate": None,
        }

    candidate = matches[0]
    result: dict[str, object] = {
        "status": "planned",
        "query": query,
        "note_path": note_rel,
        "candidate": candidate,
    }
    if not apply:
        return result

    dormant_value = normalize_graph_path(str(candidate["dormant_path"]))
    dormant_path = (root / dormant_value).resolve()
    if not is_relative_to(dormant_path, root) or not dormant_path.is_file():
        raise ValueError(f"dormant evidence is missing: {dormant_value}")
    dormant_text = dormant_path.read_text(encoding="utf-8")
    note = create_note(
        root,
        category,
        area,
        topic,
        title=str(candidate.get("title") or topic.replace("-", " ").title()),
        source_trace=dormant_path,
        body=reactivation_body(query, candidate, dormant_text),
        agent=agent,
    )

    manifest = load_dormant_manifest(local_dir)
    entry = {
        "reactivated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "query": query,
        "dormant_path": dormant_value,
        "original_path": normalize_graph_path(str(candidate["original_path"])),
        "note_path": relpath(note, root),
        "action": "reactivate-dormant-memory",
        "reason": "dormant evidence matched reactivation query",
    }
    upsert_reactivation(manifest, entry)
    write_dormant_manifest(local_dir, manifest)
    memory_manifest = build_memory(root, agent)
    result.update({
        "status": "applied",
        "note_path": relpath(note, root),
        "reactivation": entry,
        "memory_document_count": memory_manifest["document_count"],
    })
    return result


def append_source_to_existing_note(path: Path, source: str) -> None:
    text = path.read_text(encoding="utf-8")
    if source in text:
        return
    lines = text.splitlines()
    output: list[str] = []
    inserted = False
    in_sources = False
    for line in lines:
        stripped = line.strip()
        if stripped == "sources:":
            in_sources = True
            output.append(line)
            continue
        if in_sources and stripped and not line.startswith(" ") and not line.startswith("-"):
            output.append(f"  - {source}")
            inserted = True
            in_sources = False
        output.append(line)
    if in_sources and not inserted:
        output.append(f"  - {source}")
        inserted = True
    if not inserted:
        insert_at = len(output)
        for idx, line in enumerate(output):
            if idx > 0 and line.strip() == "---":
                insert_at = idx
                break
        output[insert_at:insert_at] = ["sources:", f"  - {source}"]
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def refresh_note_last_verified(path: Path) -> None:
    today = dt.date.today().isoformat()
    lines = []
    replaced = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("last_verified:"):
            lines.append(f"last_verified: {today}")
            replaced = True
        else:
            lines.append(line)
    if not replaced:
        for idx, line in enumerate(lines):
            if idx > 0 and line.strip() == "---":
                lines.insert(idx, f"last_verified: {today}")
                break
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def append_trace_evidence(path: Path, trace: Path, root: Path, fact: str, verification: str) -> None:
    source = relpath(trace, root)
    text = path.read_text(encoding="utf-8").rstrip()
    if "## Additional Trace Evidence" not in text:
        text += "\n\n## Additional Trace Evidence\n"
    entry = f"\n- Source trace: `{source}`"
    if fact:
        entry += f" - {fact.replace(chr(10), ' ')}"
    if verification:
        entry += f" Verification: {verification.replace(chr(10), ' ')}"
    path.write_text(text.rstrip() + entry + "\n", encoding="utf-8")


def promote_trace(
    root: Path,
    trace: Path,
    category: str,
    area: str | None,
    topic: str,
    agent: str = "auto",
) -> Path:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    trace = trace.resolve()
    text = trace.read_text(encoding="utf-8")
    title = file_title(text, topic.replace("-", " ").title())
    objective = section(text, ("Objective",)) or compact_summary(text)
    decision = section(text, ("Decide", "Decision", "Durable Decision"))
    verification = section(text, ("Verify", "Verification"))
    fact = decision or objective
    verification_line = "- Verification: not recorded in trace"
    if verification:
        verification_line = "- Verification: " + verification.replace("\n", " ")
    path = note_path(local_dir, category, area, topic)
    if path.exists():
        append_source_to_existing_note(path, relpath(trace, path.parent))
        append_trace_evidence(path, trace, root, fact, verification)
        refresh_note_last_verified(path)
        update_notes_index(local_dir)
        memory = local_dir / "memory"
        append_jsonl(memory / "promotion_log.jsonl", {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "trace": relpath(trace, root),
            "note": relpath(path, root),
            "category": category,
            "area": area,
            "topic": topic,
        })
        build_memory(root, agent)
        return path
    body = f"""## Durable Fact Or Decision

{fact}

## Evidence

- Source trace: `{relpath(trace, root)}`
{verification_line}

## Operational Use

- Load this note before opening the full trace when the task touches `{area or category}`.

## Revalidation

- Reopen the source trace if this decision becomes contested or stale.
"""
    path = create_note(root, category, area, topic, title=title, source_trace=trace, body=body, agent=agent)
    memory = local_dir / "memory"
    append_jsonl(memory / "promotion_log.jsonl", {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "trace": relpath(trace, root),
        "note": relpath(path, root),
        "category": category,
        "area": area,
        "topic": topic,
    })
    build_memory(root, agent)
    return path


def search_memory(root: Path, query: str, agent: str = "auto", limit: int = 5, max_shards: int = 32) -> list[dict[str, object]]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    manifest_path = local_dir / "memory" / "manifest.json"
    if not manifest_path.exists():
        build_memory(root, agent)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    query_terms = set(top_terms(query, limit=32))
    query_vector = vector(query)
    shards = manifest.get("shards", [])
    candidates = [
        shard for shard in shards
        if query_terms.intersection(set(shard.get("terms", [])))
    ]
    if not candidates:
        candidates = shards[:max_shards]
    else:
        candidates = candidates[:max_shards]

    results: list[dict[str, object]] = []
    for shard in candidates:
        shard_path = root / str(shard["path"])
        if not shard_path.exists():
            continue
        for line in shard_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            score, breakdown = score_memory_record(query, query_terms, query_vector, doc)
            if score <= 0:
                continue
            results.append(search_result(doc, str(shard["id"]), score, breakdown))
    return diversify_results(results)[:limit]
