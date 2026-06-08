"""
Local HTTP API for:
- Browsing and editing YAML under yard/prompts.
- Exporting read-only memory.yaml from Mem0 (yard/prompts/memory/).

Public URL prefix (recommended for nginx same-origin): /api/prompt-editor/
  - /api/prompt-editor/prompts-yaml/tree|content
  - /api/prompt-editor/memory-yaml/refresh

Legacy paths (still supported for direct :8010 clients): /api/prompts-yaml/*

Run from repo root: python src/prompt-editor-server.py
Default: http://0.0.0.0:8010
"""
from __future__ import annotations

import asyncio
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_ROOT = REPO_ROOT / "yard" / "prompts"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8010

PROMPT_EDITOR_API_PREFIX = "/api/prompt-editor"
READONLY_YAML_PATHS = frozenset({"memory/memory.yaml"})


def _route_paths(subpath: str) -> frozenset[str]:
    sub = subpath.lstrip("/")
    return frozenset({f"/api/{sub}", f"{PROMPT_EDITOR_API_PREFIX}/{sub}"})


def _json_body(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(data)


def _error(handler: BaseHTTPRequestHandler, message: str, status: int = 400) -> None:
    _json_body(handler, {"error": message}, status=status)


def _normalize_rel_path(rel: str) -> str:
    return rel.strip().replace("\\", "/")


def _is_readonly_yaml(rel: str) -> bool:
    return _normalize_rel_path(rel) in READONLY_YAML_PATHS


def _safe_prompts_yaml_path(rel: str, prompts_root: Path) -> Path:
    if rel is None or rel.strip() == "":
        raise ValueError("missing path")
    rel = _normalize_rel_path(rel)
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


def _list_prompts_yaml_tree_children(dir_path: Path, root: Path) -> list:
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
                "children": _list_prompts_yaml_tree_children(e, root),
            }
        )
    for e in yaml_files:
        rel = e.relative_to(root).as_posix()
        node = {"name": e.name, "path": rel, "type": "file"}
        if _is_readonly_yaml(rel):
            node["readonly"] = True
        items.append(node)
    return items


def _refresh_memory_yaml(prompts_root: Path) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    from yard.configs.config import load_config
    from yard.memory.mem0.service import Mem0Service
    from yard.memory.mem0.export import MEMORY_YAML_REL, export_memory_yaml

    cfg = load_config()
    if not cfg.memory_enabled:
        raise ValueError("memory_enabled 未开启，请在 .config.yaml 中启用 Mem0 记忆")
    service = Mem0Service.create(cfg)
    out_path = asyncio.run(
        export_memory_yaml(service, prompts_root, user_id=cfg.mem0_user_id)
    )
    rel = out_path.relative_to(prompts_root.resolve()).as_posix()
    return {"path": rel or MEMORY_YAML_REL, "readonly": True}


def make_handler(prompts: Path):
    class PromptEditorHandler(BaseHTTPRequestHandler):
        prompts_root = prompts

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write(
                "%s - - [%s] %s\n"
                % (self.address_string(), self.log_date_time_string(), fmt % args)
            )

        def _send_cors(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self._send_cors()
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in _route_paths("prompts-yaml/tree"):
                root = self.prompts_root
                if not root.exists():
                    _json_body(self, {"children": []})
                    return
                try:
                    children = _list_prompts_yaml_tree_children(root, root)
                except OSError as e:
                    _error(self, str(e), 500)
                    return
                _json_body(self, {"children": children})
                return
            if parsed.path in _route_paths("prompts-yaml/content"):
                qs = parse_qs(parsed.query)
                raw = (qs.get("path") or [None])[0]
                if raw is None:
                    _error(self, "missing path query parameter")
                    return
                try:
                    target = _safe_prompts_yaml_path(raw, self.prompts_root)
                except ValueError as e:
                    _error(self, str(e))
                    return
                if not target.is_file():
                    _error(self, "file not found", 404)
                    return
                try:
                    text = target.read_text(encoding="utf-8")
                except OSError as e:
                    _error(self, str(e), 500)
                    return
                rel = _normalize_rel_path(raw)
                _json_body(
                    self,
                    {
                        "path": rel,
                        "content": text,
                        "readonly": _is_readonly_yaml(rel),
                    },
                )
                return
            _error(self, "not found", 404)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in _route_paths("user-data/clear"):
                sys.path.insert(0, str(REPO_ROOT))
                from yard.memory.admin.user_data import clear_user_data
                from yard.memory.core.user_id import normalize_user_id

                length = self.headers.get("Content-Length")
                try:
                    n = int(length) if length else 0
                except ValueError:
                    _error(self, "bad Content-Length")
                    return
                body = self.rfile.read(n) if n > 0 else b"{}"
                try:
                    payload = json.loads(body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    _error(self, "invalid json")
                    return
                try:
                    uid = normalize_user_id(payload.get("user_id"))
                    result = asyncio.run(clear_user_data(uid))
                except ValueError as e:
                    _error(self, str(e), 400)
                    return
                except Exception as e:
                    _error(self, str(e), 500)
                    return
                _json_body(self, {"ok": True, "result": result})
                return
            if parsed.path in _route_paths("memory-yaml/refresh"):
                try:
                    payload = _refresh_memory_yaml(self.prompts_root)
                except Exception as e:
                    _error(self, str(e), 500)
                    return
                _json_body(self, payload)
                return
            _error(self, "not found", 404)

        def do_PUT(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path not in _route_paths("prompts-yaml/content"):
                _error(self, "not found", 404)
                return
            qs = parse_qs(parsed.query)
            raw = (qs.get("path") or [None])[0]
            if raw is None:
                _error(self, "missing path query parameter")
                return
            if _is_readonly_yaml(raw):
                _error(self, "memory.yaml is read-only", 403)
                return
            try:
                target = _safe_prompts_yaml_path(raw, self.prompts_root)
            except ValueError as e:
                _error(self, str(e))
                return
            length = self.headers.get("Content-Length")
            try:
                n = int(length) if length else 0
            except ValueError:
                _error(self, "bad Content-Length")
                return
            body = self.rfile.read(n) if n > 0 else b""
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                _error(self, "body must be utf-8")
                return
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            except OSError as e:
                _error(self, str(e), 500)
                return
            self.send_response(204)
            self._send_cors()
            self.end_headers()

    return PromptEditorHandler


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Local editor API for yard/prompts YAML")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--prompts",
        type=Path,
        default=PROMPTS_ROOT,
        help="Prompts YAML root directory (default: yard/prompts under repo)",
    )
    args = parser.parse_args()
    prompts = args.prompts.resolve()
    handler_cls = make_handler(prompts)
    server = ThreadingHTTPServer((args.host, args.port), handler_cls)
    print(f"Prompt editor API: http://{args.host}:{args.port}")
    print(f"Prompts YAML root: {prompts}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
