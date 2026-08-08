"""Starlette HTTP routes for the prompt editor API."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from prompt_editor.api.core import (
    is_readonly_yaml,
    list_prompts_yaml_tree_children,
    normalize_rel_path,
    route_paths,
    safe_prompts_yaml_path,
)


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, PUT, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _json(payload: dict[str, Any], status: int = 200) -> JSONResponse:
    return JSONResponse(payload, status_code=status, headers=_cors_headers())


def _error(message: str, status: int = 400) -> JSONResponse:
    return _json({"error": message}, status=status)


async def _options(_: Request) -> Response:
    return Response(status_code=204, headers=_cors_headers())


def create_prompt_editor_routes(prompts_root: Path) -> list[Route]:
    """Build Starlette routes for prompt YAML editing and memory admin APIs."""
    root = prompts_root.resolve()

    async def get_tree(request: Request) -> JSONResponse:
        if not root.exists():
            return _json({"children": []})
        try:
            children = list_prompts_yaml_tree_children(root, root)
        except OSError as e:
            return _error(str(e), 500)
        return _json({"children": children})

    async def get_content(request: Request) -> JSONResponse:
        raw = request.query_params.get("path")
        if raw is None:
            return _error("missing path query parameter")
        try:
            target = safe_prompts_yaml_path(raw, root)
        except ValueError as e:
            return _error(str(e))
        rel = normalize_rel_path(raw)
        if not target.is_file():
            from agent.memory.mem0.export import MEMORY_YAML_REL, load_memory_yaml_text

            if rel == MEMORY_YAML_REL:
                try:
                    text = await load_memory_yaml_text(root)
                except Exception as e:
                    return _error(str(e), 500)
                return _json({"path": rel, "content": text, "readonly": True})
            return _error("file not found", 404)
        try:
            text = target.read_text(encoding="utf-8")
        except OSError as e:
            return _error(str(e), 500)
        return _json({"path": rel, "content": text, "readonly": is_readonly_yaml(rel)})

    async def put_content(request: Request) -> Response:
        raw = request.query_params.get("path")
        if raw is None:
            return _error("missing path query parameter")
        if is_readonly_yaml(raw):
            return _error("memory.yaml is read-only", 403)
        try:
            target = safe_prompts_yaml_path(raw, root)
        except ValueError as e:
            return _error(str(e))
        body = await request.body()
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return _error("body must be utf-8")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        except OSError as e:
            return _error(str(e), 500)
        return Response(status_code=204, headers=_cors_headers())

    async def post_user_data_clear(request: Request) -> JSONResponse:
        from agent.memory.admin.user_data import clear_user_data
        from agent.memory.core.user_id import normalize_user_id

        try:
            payload = await request.json()
        except json.JSONDecodeError:
            return _error("invalid json")
        try:
            uid = normalize_user_id(payload.get("user_id"))
            result = await clear_user_data(uid)
        except ValueError as e:
            return _error(str(e), 400)
        except Exception as e:
            return _error(str(e), 500)
        return _json({"ok": True, "result": result})

    async def post_memory_yaml_refresh(_: Request) -> JSONResponse:
        from agent.memory.mem0.export import MEMORY_YAML_REL, ensure_memory_yaml_exported

        try:
            out_path = await ensure_memory_yaml_exported(root, force=True)
            rel = out_path.relative_to(root).as_posix()
            return _json({"path": rel or MEMORY_YAML_REL, "readonly": True})
        except Exception as e:
            return _error(str(e), 500)

    handlers = {
        "tree": get_tree,
        "content_get": get_content,
        "content_put": put_content,
        "user_data_clear": post_user_data_clear,
        "memory_refresh": post_memory_yaml_refresh,
    }

    routes: list[Route] = []
    for path_key, method, endpoint in [
        ("prompts-yaml/tree", "GET", handlers["tree"]),
        ("prompts-yaml/content", "GET", handlers["content_get"]),
        ("prompts-yaml/content", "PUT", handlers["content_put"]),
        ("user-data/clear", "POST", handlers["user_data_clear"]),
        ("memory-yaml/refresh", "POST", handlers["memory_refresh"]),
    ]:
        for route_path in route_paths(path_key):
            routes.append(Route(route_path, endpoint=endpoint, methods=[method]))
            routes.append(Route(route_path, endpoint=_options, methods=["OPTIONS"]))
    return routes
