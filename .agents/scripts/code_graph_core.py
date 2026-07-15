#!/usr/bin/env python3
"""Generated local code graph support for Fable Harness."""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path


SCHEMA = "fable-harness-code-graph-v1"
EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "temp_files",
    ".worktrees",
    "worktrees",
}


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def find_local_dir(root: Path, agent: str = "auto") -> Path:
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(kind: str, *parts: object) -> str:
    value = ":".join(str(part) for part in parts)
    digest = hashlib.sha256(f"{kind}:{value}".encode("utf-8")).hexdigest()[:20]
    return f"code-{kind}:{digest}"


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def graph_dir(root: Path, agent: str = "auto") -> Path:
    return find_local_dir(root, agent) / "memory" / "code-graph"


def normalize_path(value: str) -> str:
    return value.strip().strip("`").replace("\\", "/")


def module_name_for_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if "src" in parts:
        parts = parts[parts.index("src") + 1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) or path.stem


def resolve_import_module(module_name: str, rel: str, level: int, module: str | None) -> str:
    if level <= 0:
        return module or ""
    module_parts = module_name.split(".") if module_name else []
    if not rel.endswith("__init__.py"):
        module_parts = module_parts[:-1]
    up = max(level - 1, 0)
    if up:
        module_parts = module_parts[:-up]
    suffix = [part for part in (module or "").split(".") if part]
    return ".".join([*module_parts, *suffix])


def should_skip_source_path(path: Path, root: Path, local_dir: Path) -> bool:
    try:
        resolved = path.resolve()
        if is_relative_to(resolved, local_dir.resolve()):
            return True
        rel_parts = path.relative_to(root.resolve()).parts
    except ValueError:
        return True
    if any(part in EXCLUDED_DIR_NAMES for part in rel_parts):
        return True
    return "memory" in rel_parts and "code-graph" in rel_parts


def iter_source_files(root: Path, local_dir: Path, extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    root = root.resolve()
    local_dir = local_dir.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        if should_skip_source_path(path, root, local_dir):
            continue
        files.append(path)
    return sorted(files, key=lambda item: relpath(item, root))


def iter_python_files(root: Path, local_dir: Path) -> list[Path]:
    return iter_source_files(root, local_dir, {".py"})


def span(node: ast.AST, fallback_end: int = 1) -> dict[str, int]:
    return {
        "line_start": int(getattr(node, "lineno", 1) or 1),
        "line_end": int(getattr(node, "end_lineno", getattr(node, "lineno", fallback_end)) or fallback_end),
        "col_start": int(getattr(node, "col_offset", 0) or 0),
        "col_end": int(getattr(node, "end_col_offset", getattr(node, "col_offset", 0)) or 0),
    }


def call_name(expr: ast.AST) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        base = call_name(expr.value)
        return f"{base}.{expr.attr}" if base else expr.attr
    if isinstance(expr, ast.Call):
        return call_name(expr.func)
    return None


class GraphBuilder:
    def __init__(self, root: Path, agent: str = "auto") -> None:
        self.root = root.resolve()
        self.agent = agent
        self.local_dir = find_local_dir(self.root, agent)
        self.nodes: dict[str, dict[str, object]] = {}
        self.edges: dict[str, dict[str, object]] = {}
        self.symbol_by_full: dict[str, str] = {}
        self.symbols_by_name: dict[str, list[str]] = {}
        self.records: list[dict[str, object]] = []

    def add_node(self, node: dict[str, object]) -> str:
        node_id = str(node["id"])
        self.nodes[node_id] = node
        return node_id

    def add_edge(self, relation: str, source: str, target: str, **attributes: object) -> str:
        edge_id = stable_id("edge", relation, source, target, json.dumps(attributes, sort_keys=True))
        edge = {
            "id": edge_id,
            "relation": relation,
            "from": source,
            "to": target,
        }
        if attributes:
            edge["attributes"] = attributes
        self.edges[edge_id] = edge
        return edge_id

    def add_symbol(self, rel: str, language: str, name: str, full_name: str, symbol_kind: str, node: ast.AST, file_id: str, parent_id: str) -> str:
        node_id = stable_id("symbol", language, rel, full_name)
        item: dict[str, object] = {
            "id": node_id,
            "kind": "symbol",
            "language": language,
            "path": rel,
            "name": name,
            "full_name": full_name,
            "symbol_kind": symbol_kind,
            **span(node),
            "attributes": {},
        }
        self.add_node(item)
        self.symbol_by_full[full_name] = node_id
        self.symbols_by_name.setdefault(name, []).append(node_id)
        self.add_edge("contains", parent_id, node_id)
        self.add_edge("defines", file_id, node_id)
        return node_id

    def collect_imports(self, tree: ast.AST, rel: str, file_id: str, module_name: str) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    aliases[local] = alias.name
                    import_id = stable_id("import", rel, getattr(node, "lineno", 1), local, alias.name)
                    self.add_node({
                        "id": import_id,
                        "kind": "import",
                        "language": "python",
                        "path": rel,
                        "name": local,
                        "module": alias.name,
                        **span(node),
                    })
                    self.add_edge("imports", file_id, import_id, imported=alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = resolve_import_module(module_name, rel, int(node.level or 0), node.module)
                for alias in node.names:
                    local = alias.asname or alias.name
                    imported = f"{module}.{alias.name}" if module else alias.name
                    aliases[local] = imported
                    import_id = stable_id("import", rel, getattr(node, "lineno", 1), local, imported)
                    self.add_node({
                        "id": import_id,
                        "kind": "import",
                        "language": "python",
                        "path": rel,
                        "name": local,
                        "module": module,
                        "imported": imported,
                        **span(node),
                    })
                    self.add_edge("imports", file_id, import_id, imported=imported)
        return aliases

    def collect_definitions(self, tree: ast.Module, rel: str, module_name: str, file_id: str) -> dict[ast.AST, str]:
        defs_by_node: dict[ast.AST, str] = {}
        module_id = stable_id("symbol", "python", rel, module_name)
        module_node = {
            "id": module_id,
            "kind": "symbol",
            "language": "python",
            "path": rel,
            "name": module_name.split(".")[-1],
            "full_name": module_name,
            "symbol_kind": "module",
            "line_start": 1,
            "line_end": max(1, len(getattr(tree, "body", []))),
            "col_start": 0,
            "col_end": 0,
            "attributes": {},
        }
        self.add_node(module_node)
        self.symbol_by_full[module_name] = module_id
        self.symbols_by_name.setdefault(module_node["name"], []).append(module_id)  # type: ignore[index]
        self.add_edge("contains", file_id, module_id)
        self.add_edge("defines", file_id, module_id)
        defs_by_node[tree] = module_id

        def visit_body(body: list[ast.stmt], parent_id: str, prefix: list[str], in_class: bool = False) -> None:
            for child in body:
                if isinstance(child, ast.ClassDef):
                    full = ".".join([module_name, *prefix, child.name])
                    class_id = self.add_symbol(rel, "python", child.name, full, "class", child, file_id, parent_id)
                    defs_by_node[child] = class_id
                    visit_body(child.body, class_id, [*prefix, child.name], True)
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    full = ".".join([module_name, *prefix, child.name])
                    if child.name.startswith("test_") or rel.startswith("tests/") or Path(rel).name.startswith("test_"):
                        symbol_kind = "test"
                    elif isinstance(child, ast.AsyncFunctionDef):
                        symbol_kind = "async_function"
                    elif in_class:
                        symbol_kind = "method"
                    else:
                        symbol_kind = "function"
                    function_id = self.add_symbol(rel, "python", child.name, full, symbol_kind, child, file_id, parent_id)
                    defs_by_node[child] = function_id
                    visit_body([stmt for stmt in child.body if isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))], function_id, [*prefix, child.name], False)

        visit_body(tree.body, module_id, [])
        return defs_by_node

    def parse_file(self, path: Path) -> None:
        rel = relpath(path, self.root)
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=rel)
        module_name = module_name_for_path(path, self.root)
        file_id = stable_id("file", rel)
        self.add_node({
            "id": file_id,
            "kind": "file",
            "language": "python",
            "path": rel,
            "name": Path(rel).name,
            "sha256": sha256_text(text),
            "size": len(text.encode("utf-8")),
        })
        aliases = self.collect_imports(tree, rel, file_id, module_name)
        defs_by_node = self.collect_definitions(tree, rel, module_name, file_id)
        self.records.append({
            "path": path,
            "rel": rel,
            "tree": tree,
            "file_id": file_id,
            "module_name": module_name,
            "module_id": defs_by_node[tree],
            "aliases": aliases,
            "defs_by_node": defs_by_node,
        })

    def resolve_symbol(self, name: str, aliases: dict[str, str], rel: str) -> tuple[str | None, str]:
        parts = name.split(".")
        resolved_name = name
        if parts and parts[0] in aliases:
            resolved_name = ".".join([aliases[parts[0]], *parts[1:]])
        if resolved_name in self.symbol_by_full:
            return self.symbol_by_full[resolved_name], resolved_name
        if "." in resolved_name:
            suffix = f".{resolved_name}"
            matches = [
                node_id
                for full, node_id in self.symbol_by_full.items()
                if full.endswith(suffix) and self.nodes.get(node_id, {}).get("path") == rel
            ]
            if len(matches) == 1:
                return matches[0], resolved_name
        matches = self.symbols_by_name.get(resolved_name, [])
        matches = [node_id for node_id in matches if self.nodes.get(node_id, {}).get("path") == rel]
        if len(matches) == 1:
            return matches[0], resolved_name
        return None, resolved_name

    def add_reference(self, rel: str, name: str, node: ast.AST) -> str:
        ref_id = stable_id("reference", rel, getattr(node, "lineno", 1), name)
        self.add_node({
            "id": ref_id,
            "kind": "reference",
            "language": "python",
            "path": rel,
            "name": name,
            **span(node),
            "attributes": {"resolved": False},
        })
        return ref_id

    def collect_calls(self, record: dict[str, object]) -> None:
        rel = str(record["rel"])
        tree = record["tree"]
        aliases = record["aliases"]
        defs_by_node = record["defs_by_node"]
        assert isinstance(tree, ast.AST)
        assert isinstance(aliases, dict)
        assert isinstance(defs_by_node, dict)

        def visit(node: ast.AST, current_symbol: str) -> None:
            if node in defs_by_node:
                current_symbol = str(defs_by_node[node])
            if isinstance(node, ast.Call):
                name = call_name(node.func)
                if name:
                    target_id, resolved_name = self.resolve_symbol(name, aliases, rel)  # type: ignore[arg-type]
                    if not target_id:
                        target_id = self.add_reference(rel, resolved_name, node)
                    self.add_edge("calls", current_symbol, target_id, name=name, resolved_name=resolved_name, **span(node))
                    source_node = self.nodes.get(current_symbol, {})
                    target_node = self.nodes.get(target_id, {})
                    if source_node.get("symbol_kind") == "test" and target_node.get("kind") == "symbol":
                        self.add_edge("tests", current_symbol, target_id, heuristic=True, **span(node))
            for child in ast.iter_child_nodes(node):
                visit(child, current_symbol)

        visit(tree, str(record["module_id"]))

    def build(self) -> dict[str, object]:
        for path in iter_python_files(self.root, self.local_dir):
            try:
                self.parse_file(path)
            except (SyntaxError, UnicodeDecodeError) as exc:
                rel = relpath(path, self.root)
                node_id = stable_id("diagnostic", rel, type(exc).__name__, str(exc))
                self.add_node({
                    "id": node_id,
                    "kind": "diagnostic",
                    "language": "python",
                    "path": rel,
                    "name": type(exc).__name__,
                    "message": str(exc),
                })
        for record in self.records:
            self.collect_calls(record)
        return write_code_graph(self.root, self.agent, list(self.nodes.values()), list(self.edges.values()))


def build_indexes(nodes: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, dict[str, list[str]]]:
    by_kind: dict[str, list[str]] = {}
    by_path: dict[str, list[str]] = {}
    by_symbol: dict[str, list[str]] = {}
    by_relation: dict[str, list[str]] = {}
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            continue
        for key in [node.get("kind"), node.get("symbol_kind")]:
            if key:
                by_kind.setdefault(str(key), []).append(node_id)
        if node.get("path"):
            by_path.setdefault(str(node["path"]), []).append(node_id)
        for key in [node.get("name"), node.get("full_name")]:
            if key:
                by_symbol.setdefault(str(key), []).append(node_id)
        full_name = str(node.get("full_name", ""))
        if full_name:
            for suffix in full_name.split("."):
                by_symbol.setdefault(suffix, []).append(node_id)
    for edge in edges:
        edge_id = str(edge.get("id", ""))
        relation = str(edge.get("relation", ""))
        if edge_id and relation:
            by_relation.setdefault(relation, []).append(edge_id)
    return {
        "by-kind": {key: sorted(set(value)) for key, value in sorted(by_kind.items())},
        "by-path": {key: sorted(set(value)) for key, value in sorted(by_path.items())},
        "by-symbol": {key: sorted(set(value)) for key, value in sorted(by_symbol.items())},
        "by-relation": {key: sorted(set(value)) for key, value in sorted(by_relation.items())},
    }


def clear_generated_graph_dir(root: Path, local_dir: Path, target: Path) -> None:
    resolved_root = root.resolve()
    if local_dir.exists() and not is_relative_to(local_dir.resolve(), resolved_root):
        raise ValueError(f"refusing to clear code graph through local dir outside workspace: {local_dir}")
    memory_dir = local_dir / "memory"
    if memory_dir.exists() and not is_relative_to(memory_dir.resolve(), resolved_root):
        raise ValueError(f"refusing to clear code graph through memory directory outside workspace: {memory_dir}")
    if memory_dir.exists() and memory_dir.is_symlink():
        raise ValueError(f"refusing to clear code graph through symlinked memory directory: {memory_dir}")
    if target.exists():
        if target.is_symlink():
            raise ValueError(f"refusing to clear symlinked code graph directory: {target}")
        resolved_memory = memory_dir.resolve()
        resolved_target = target.resolve()
        if not is_relative_to(resolved_target, resolved_root):
            raise ValueError(f"refusing to clear code graph outside workspace: {target}")
        if not is_relative_to(resolved_target, resolved_memory):
            raise ValueError(f"refusing to clear code graph outside generated memory directory: {target}")
        shutil.rmtree(target)


def write_code_graph(root: Path, agent: str, nodes: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, object]:
    local_dir = find_local_dir(root, agent)
    target = local_dir / "memory" / "code-graph"
    clear_generated_graph_dir(root, local_dir, target)
    (target / "indexes").mkdir(parents=True, exist_ok=True)
    nodes = sorted(nodes, key=lambda item: str(item.get("id", "")))
    edges = sorted(edges, key=lambda item: str(item.get("id", "")))
    write_jsonl(target / "nodes.jsonl", nodes)
    write_jsonl(target / "edges.jsonl", edges)
    indexes = build_indexes(nodes, edges)
    for name, data in indexes.items():
        write_json(target / "indexes" / f"{name}.json", data)
    manifest = {
        "schema": SCHEMA,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_kinds": sorted({str(node.get("kind", "")) for node in nodes if node.get("kind")}),
        "symbol_kinds": sorted({str(node.get("symbol_kind", "")) for node in nodes if node.get("symbol_kind")}),
        "relations": sorted({str(edge.get("relation", "")) for edge in edges if edge.get("relation")}),
        "indexes": [
            "indexes/by-kind.json",
            "indexes/by-path.json",
            "indexes/by-symbol.json",
            "indexes/by-relation.json",
        ],
        "files": [
            {"path": str(node["path"]), "sha256": str(node["sha256"])}
            for node in nodes
            if node.get("kind") == "file" and node.get("sha256") and node.get("path")
        ],
    }
    write_json(target / "manifest.json", manifest)
    return manifest


def build_code_graph(root: Path, agent: str = "auto") -> dict[str, object]:
    builder = GraphBuilder(root, agent)
    return builder.build()


def load_code_graph(root: Path, agent: str = "auto") -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    target = graph_dir(root, agent)
    manifest = read_json(target / "manifest.json", {})
    if not isinstance(manifest, dict):
        manifest = {}
    return manifest, read_jsonl(target / "nodes.jsonl"), read_jsonl(target / "edges.jsonl")


def match_symbol(node: dict[str, object], value: str) -> bool:
    value = value.strip()
    name = str(node.get("name", ""))
    full = str(node.get("full_name", ""))
    return value in {name, full} or full.endswith(f".{value}") or name.endswith(value)


def query_code_graph(
    root: Path,
    agent: str = "auto",
    path: str | None = None,
    symbol: str | None = None,
    kind: str | None = None,
    relation: str | None = None,
    from_value: str | None = None,
    to_value: str | None = None,
    impact: str | None = None,
) -> dict[str, object]:
    manifest, nodes, edges = load_code_graph(root, agent)
    node_by_id = {str(node.get("id")): node for node in nodes}
    selected_nodes: dict[str, dict[str, object]] = {}
    selected_edges: dict[str, dict[str, object]] = {}

    def add_node_id(node_id: str) -> None:
        if node_id in node_by_id:
            selected_nodes[node_id] = node_by_id[node_id]

    def node_matches_ref(node: dict[str, object], value: str) -> bool:
        return str(node.get("id")) == value or str(node.get("path", "")) == normalize_path(value) or match_symbol(node, value)

    if path:
        wanted = normalize_path(path)
        for node in nodes:
            if str(node.get("path", "")) == wanted:
                add_node_id(str(node.get("id")))
    if symbol:
        for node in nodes:
            if match_symbol(node, symbol):
                add_node_id(str(node.get("id")))
    if kind:
        for node in nodes:
            if node.get("kind") == kind or node.get("symbol_kind") == kind:
                add_node_id(str(node.get("id")))
    if relation:
        for edge in edges:
            if edge.get("relation") == relation:
                selected_edges[str(edge.get("id"))] = edge
                add_node_id(str(edge.get("from")))
                add_node_id(str(edge.get("to")))
    if from_value or to_value:
        from_ids = {
            str(node.get("id"))
            for node in nodes
            if from_value and node_matches_ref(node, from_value)
        } if from_value else set()
        to_ids = {
            str(node.get("id"))
            for node in nodes
            if to_value and node_matches_ref(node, to_value)
        } if to_value else set()
        if (from_value and not from_ids) or (to_value and not to_ids):
            return {"schema": manifest.get("schema", SCHEMA), "nodes": [], "edges": []}
        for edge in edges:
            if from_ids and edge.get("from") not in from_ids:
                continue
            if to_ids and edge.get("to") not in to_ids:
                continue
            selected_edges[str(edge.get("id"))] = edge
            add_node_id(str(edge.get("from")))
            add_node_id(str(edge.get("to")))
    if impact:
        seeds = {
            str(node.get("id"))
            for node in nodes
            if node_matches_ref(node, impact)
        }
        frontier = set(seeds)
        seen = set(seeds)
        impact_relations = {"calls", "imports", "tests"}
        while frontier:
            current = frontier
            frontier = set()
            for edge in edges:
                if edge.get("relation") not in impact_relations:
                    continue
                source = str(edge.get("from"))
                target = str(edge.get("to"))
                if target in current:
                    selected_edges[str(edge.get("id"))] = edge
                    for node_id in [source, target]:
                        add_node_id(node_id)
                        if node_id not in seen:
                            seen.add(node_id)
                            frontier.add(node_id)
    if not any([path, symbol, kind, relation, from_value, to_value, impact]):
        selected_nodes = {str(node.get("id")): node for node in nodes}
        selected_edges = {str(edge.get("id")): edge for edge in edges}

    result = {
        "schema": manifest.get("schema", SCHEMA),
        "nodes": sorted(selected_nodes.values(), key=lambda item: str(item.get("id", ""))),
        "edges": sorted(selected_edges.values(), key=lambda item: str(item.get("id", ""))),
    }
    if impact:
        result["query_mode"] = "static-impact"
        result["impact_query"] = impact
    return result


def check_code_graph(root: Path, agent: str = "auto", strict: bool = False) -> dict[str, object]:
    manifest, nodes, edges = load_code_graph(root, agent)
    target = graph_dir(root, agent)
    errors: list[str] = []
    if manifest.get("schema") != SCHEMA:
        errors.append("manifest schema is missing or invalid")
    node_ids: set[str] = set()
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            errors.append("node missing id")
            continue
        if node_id in node_ids:
            errors.append(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
    edge_ids: set[str] = set()
    for edge in edges:
        edge_id = str(edge.get("id", ""))
        if not edge_id:
            errors.append("edge missing id")
            continue
        if edge_id in edge_ids:
            errors.append(f"duplicate edge id: {edge_id}")
        edge_ids.add(edge_id)
        source = str(edge.get("from", ""))
        target_id = str(edge.get("to", ""))
        if source not in node_ids or target_id not in node_ids:
            errors.append(f"dangling edge {edge_id}: {source} -> {target_id}")
    if manifest.get("node_count") != len(nodes):
        errors.append("manifest node_count does not match nodes.jsonl")
    if manifest.get("edge_count") != len(edges):
        errors.append("manifest edge_count does not match edges.jsonl")
    indexes = build_indexes(nodes, edges)
    for name, expected in indexes.items():
        path = target / "indexes" / f"{name}.json"
        actual = read_json(path, None)
        if actual != expected:
            errors.append(f"index mismatch: indexes/{name}.json")
    if strict:
        for item in manifest.get("files", []):
            if not isinstance(item, dict):
                continue
            path_value = item.get("path")
            expected_hash = item.get("sha256")
            if not isinstance(path_value, str) or not isinstance(expected_hash, str):
                continue
            file_path = root / path_value
            if not file_path.is_file():
                errors.append(f"source file missing: {path_value}")
                continue
            current_hash = sha256_text(file_path.read_text(encoding="utf-8"))
            if current_hash != expected_hash:
                errors.append(f"source hash changed: {path_value}")
    return {
        "status": "ok" if not errors else "failed",
        "schema": manifest.get("schema", SCHEMA),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "errors": errors,
    }
