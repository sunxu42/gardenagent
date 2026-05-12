"""Compose persona system prompts from `prompts/*.yaml` on each model call.

YAML 合并与渲染逻辑原先在 `yard/persona/prompt_builder.py`，现并入本模块，
由 `PersonaPromptMiddleware` 在每次 `modify_request` 时从磁盘重新读取，
以便网页或编辑器修改 prompt 后立即生效（含 `manifests/personas.yaml`）。
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml
from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest
from langchain_core.messages import SystemMessage
from deepagents.middleware._utils import append_to_system_message


DEFAULT_PROMPTS_DIR = "yard/prompts"
MANIFEST_RELPATH = Path("manifests") / "personas.yaml"


def _read_yaml(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {}
    return data


def _resolve_ref(prompts_dir: Path, ref: str) -> Path:
    if not ref:
        raise ValueError("Empty reference")

    p = Path(ref)
    if p.is_absolute() and p.exists():
        return p

    repo_root = prompts_dir.parent
    candidates: list[Path] = []
    candidates.append(repo_root / p)
    candidates.append(prompts_dir / p)
    parts = p.parts
    if parts and parts[0] == prompts_dir.name:
        candidates.append(prompts_dir / Path(*parts[1:]))
    candidates.append(Path.cwd() / p)

    for cand in candidates:
        if cand.exists():
            return cand

    raise FileNotFoundError(
        f"Cannot resolve prompt ref {ref!r}. Tried: " + ", ".join(str(c) for c in candidates)
    )


def _deep_merge(base: Any, override: Any) -> Any:
    if override is None:
        return base
    if base is None:
        return override
    if isinstance(base, dict) and isinstance(override, dict):
        out: dict = dict(base)
        for key, value in override.items():
            out[key] = _deep_merge(out.get(key), value)
        return out
    return override


def _is_blank_scalar(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return len(list(value)) == 0
    return False


def _merge_persona_supplement(base: dict, role: dict) -> dict:
    """Merge role onto base: shared baseline + role additions (not wholesale replacement).

    - ``system.identity`` / ``personality`` / ``style``: concatenate when both present.
    - ``system.rules``, ``instructions.{must,should}``, ``constraints.{hard,soft}``: append lists.
    - Other keys (``meta``, ``output``, ``tools``, ``capabilities``, ``skills``, …): keep
      recursive deep-merge semantics (role refines or replaces non-list leaves as before).
    """
    temp = _deep_merge(copy.deepcopy(base), copy.deepcopy(role))

    base_sys = base.get("system") or {}
    role_sys = role.get("system") or {}
    out_sys = dict(temp.get("system") or {})

    sep = "\n\n---\n\n"
    for field in ("identity", "personality", "style"):
        b = base_sys.get(field)
        r = role_sys.get(field)
        if field in role_sys and _is_blank_scalar(r):
            if not _is_blank_scalar(b):
                out_sys[field] = b
            continue
        if _is_blank_scalar(r):
            continue
        if _is_blank_scalar(b):
            out_sys[field] = r
            continue
        out_sys[field] = f"{str(b).rstrip()}{sep}{str(r).rstrip()}"

    if role_sys.get("rules") is not None:
        combined = _as_lines(base_sys.get("rules")) + _as_lines(role_sys.get("rules"))
        if combined:
            out_sys["rules"] = combined

    temp["system"] = out_sys

    base_i = base.get("instructions") or {}
    role_i = role.get("instructions") or {}
    ti = dict(temp.get("instructions") or {})
    for key in ("must", "should"):
        if role_i.get(key) is not None:
            merged_lines = _as_lines(base_i.get(key)) + _as_lines(role_i.get(key))
            if merged_lines:
                ti[key] = merged_lines
    temp["instructions"] = ti

    base_c = base.get("constraints") or {}
    role_c = role.get("constraints") or {}
    tc = dict(temp.get("constraints") or {})
    for key in ("hard", "soft"):
        if role_c.get(key) is not None:
            merged_lines = _as_lines(base_c.get(key)) + _as_lines(role_c.get(key))
            if merged_lines:
                tc[key] = merged_lines
    temp["constraints"] = tc

    return temp


def _as_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Iterable):
        lines: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                lines.append(text)
        return lines
    return [str(value)]


def _render_section(title: str, value: Any, *, bullet: bool = False) -> str:
    lines = _as_lines(value)
    if not lines:
        return ""
    if bullet or len(lines) > 1:
        body = "\n".join(f"- {line}" for line in lines)
    else:
        body = lines[0]
    return f"## {title}\n{body}"


def render_system_prompt(data: dict) -> str:
    """Render a merged persona dict (base + role) into a single string."""
    blocks: list[str] = []

    capabilities = data.get("capabilities") or {}
    preamble = capabilities.get("index_preamble")
    if preamble:
        blocks.append(_render_section("Capability index", preamble))

    system = data.get("system") or {}
    blocks.append(_render_section("Identity", system.get("identity")))
    blocks.append(_render_section("Personality", system.get("personality")))
    blocks.append(_render_section("Style", system.get("style")))
    blocks.append(_render_section("Rules", system.get("rules"), bullet=True))

    instructions = data.get("instructions") or {}
    blocks.append(_render_section("You must", instructions.get("must"), bullet=True))
    blocks.append(_render_section("You should", instructions.get("should"), bullet=True))

    constraints = data.get("constraints") or {}
    blocks.append(_render_section("Hard constraints", constraints.get("hard"), bullet=True))
    blocks.append(_render_section("Soft constraints", constraints.get("soft"), bullet=True))

    tools = data.get("tools") or {}
    tool_lines: list[str] = []
    policy = tools.get("policy") or {}
    if policy:
        policy_items = ", ".join(f"{k}={v}" for k, v in policy.items())
        tool_lines.append(f"Policy: {policy_items}")
    for key, label in (
        ("call_conditions", "Call conditions"),
        ("deny_conditions", "Deny conditions"),
        ("failure_fallback", "Failure fallback"),
    ):
        for line in _as_lines(tools.get(key)):
            tool_lines.append(f"- [{label}] {line}")
    if tool_lines:
        blocks.append("## Tool usage\n" + "\n".join(tool_lines))

    output = data.get("output") or {}
    if output:
        out_lines: list[str] = []
        fmt = output.get("format")
        if fmt:
            out_lines.append(f"Format: {fmt}")
        schema = output.get("schema") or {}
        sections = schema.get("sections")
        if sections:
            out_lines.append("Sections: " + ", ".join(_as_lines(sections)))
        for line in _as_lines(output.get("constraints")):
            out_lines.append(f"- {line}")
        if out_lines:
            blocks.append("## Output\n" + "\n".join(out_lines))

    skills = data.get("skills")
    skill_lines = _as_lines(skills)
    if skill_lines:
        blocks.append(_render_section("Skill sources", skill_lines, bullet=True))

    return "\n\n".join(block for block in blocks if block).strip()


class _PersonaYamlComposer:
    """Resolve `prompts_dir` once; reload manifest and role YAML on each `build`."""

    def __init__(self, prompts_dir: str | Path = DEFAULT_PROMPTS_DIR) -> None:
        self.prompts_dir = Path(prompts_dir).resolve() if Path(prompts_dir).is_absolute() else Path(prompts_dir)
        manifest_path = self.prompts_dir / MANIFEST_RELPATH
        if not manifest_path.exists():
            alt = Path.cwd() / self.prompts_dir / MANIFEST_RELPATH
            if alt.exists():
                self.prompts_dir = (Path.cwd() / self.prompts_dir).resolve()
                manifest_path = self.prompts_dir / MANIFEST_RELPATH
            else:
                raise FileNotFoundError(f"Personas manifest not found: {manifest_path}")
        self._manifest_path = manifest_path

    def build(self, persona_id: Optional[str] = None) -> str:
        manifest = _read_yaml(self._manifest_path)
        default_persona_id: Optional[str] = manifest.get("default_persona_id")
        personas: dict[str, dict] = {
            p["id"]: p for p in manifest.get("personas", []) if "id" in p
        }

        pid = persona_id or default_persona_id
        if not pid:
            raise ValueError("No persona id supplied and personas.yaml has no default_persona_id")
        if pid not in personas:
            raise ValueError(f"Unknown persona id: {pid!r}. Available: {list(personas)}")
        persona = personas[pid]
        if persona.get("enabled") is False:
            raise ValueError(f"Persona {pid!r} is disabled in personas.yaml")

        merged: dict = {}
        base_ref = persona.get("base_ref")
        role_ref = persona.get("role_ref")
        if base_ref:
            merged = _read_yaml(_resolve_ref(self.prompts_dir, base_ref))
        if role_ref:
            role_data = _read_yaml(_resolve_ref(self.prompts_dir, role_ref))
            merged = _merge_persona_supplement(merged, role_data) if merged else role_data
        meta = dict(merged.get("meta") or {})
        meta.setdefault("persona_id", persona.get("id"))
        merged["meta"] = meta
        return render_system_prompt(merged)


def _flatten_system_text(system_message: SystemMessage | None) -> str:
    if system_message is None:
        return ""
    content = system_message.content
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in system_message.content_blocks:
        if isinstance(block, dict) and block.get("type") == "text":
            t = block.get("text")
            if t:
                parts.append(str(t))
    return "\n\n".join(parts)


class PersonaPromptState(AgentState):
    """State schema for PersonaPromptMiddleware (no extra fields)."""


class PersonaPromptMiddleware(AgentMiddleware[PersonaPromptState, Any]):
    """Prepend freshly built persona YAML prompt before the graph system message (e.g. BASE_AGENT_PROMPT)."""

    state_schema = PersonaPromptState

    def __init__(
        self,
        prompts_dir: str | Path = DEFAULT_PROMPTS_DIR,
        *,
        persona_id: Optional[str] = None,
    ) -> None:
        self._composer = _PersonaYamlComposer(prompts_dir)
        self._persona_id = persona_id

    def modify_request(self, request: ModelRequest) -> ModelRequest:
        persona_text = self._composer.build(self._persona_id).strip()
        base_flat = _flatten_system_text(request.system_message)
        if not persona_text:
            return request
        new_system_message = append_to_system_message(
            SystemMessage(content=persona_text),
            base_flat,
        )
        return request.override(system_message=new_system_message)

    def wrap_model_call(self, request: ModelRequest, handler):
        return handler(self.modify_request(request))

    async def awrap_model_call(self, request: ModelRequest, handler):
        return await handler(self.modify_request(request))
