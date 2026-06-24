"""Core path utilities for the prompt editor HTTP API."""
from __future__ import annotations

from pathlib import Path

PROMPT_EDITOR_API_PREFIX = "/api/prompt-editor"
READONLY_YAML_PATHS = frozenset({"memory/memory.yaml"})


def route_paths(subpath: str) -> frozenset[str]:
    """Return legacy and prefixed API paths for a prompt-editor subpath."""
    sub = subpath.lstrip("/")
    return frozenset({f"/api/{sub}", f"{PROMPT_EDITOR_API_PREFIX}/{sub}"})


def normalize_rel_path(rel: str) -> str:
    """Normalize a relative path to forward-slash POSIX form."""
    return rel.strip().replace("\\", "/")


def is_readonly_yaml(rel: str) -> bool:
    """Return whether the relative YAML path is read-only in the editor."""
    return normalize_rel_path(rel) in READONLY_YAML_PATHS


def safe_prompts_yaml_path(rel: str, prompts_root: Path) -> Path:
    """Resolve a relative path under prompts_root, rejecting traversal and non-YAML."""
    if rel is None or rel.strip() == "":
        raise ValueError("missing path")
    rel = normalize_rel_path(rel)
    parts = Path(rel).parts
    if ".." in parts or (len(parts) > 0 and parts[0] == "/"):
        raise ValueError("invalid path")
    candidate = (prompts_root / rel).resolve()
    root = prompts_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise ValueError("path outside prompts root") from e
    if candidate.suffix.lower() not in (".yaml", ".yml"):
        raise ValueError("not a yaml file")
    return candidate


def list_prompts_yaml_tree_children(dir_path: Path, root: Path) -> list:
    """Build a nested tree of directories and YAML files under root."""
    items: list = []
    try:
        entries = list(dir_path.iterdir())
    except FileNotFoundError:
        return items
    dirs = sorted([e for e in entries if e.is_dir()], key=lambda x: x.name.lower())
    yaml_files = sorted(
        [e for e in entries if e.is_file() and e.suffix.lower() in (".yaml", ".yml")],
        key=lambda x: x.name.lower(),
    )
    for e in dirs:
        rel = e.relative_to(root).as_posix()
        items.append(
            {
                "name": e.name,
                "path": rel,
                "type": "dir",
                "children": list_prompts_yaml_tree_children(e, root),
            }
        )
    for e in yaml_files:
        rel = e.relative_to(root).as_posix()
        node = {"name": e.name, "path": rel, "type": "file"}
        if is_readonly_yaml(rel):
            node["readonly"] = True
        items.append(node)
    return items
