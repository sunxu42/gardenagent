"""Build the LLM system prompt by composing YAML files under `prompts/`.

This module replaces the legacy workspace-bootstrap approach (loading
AGENTS.md / SOUL.md / IDENTITY.md / BOOTSTRAP.md from the workspace).
Instead, we read the structured manifests + base + role YAML files from
`prompts/` and deterministically render a single system prompt string.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml


DEFAULT_PROMPTS_DIR = "yard/prompts"
MANIFEST_RELPATH = Path("manifests") / "personas.yaml"


def _read_yaml(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {}
    return data


def _resolve_ref(prompts_dir: Path, ref: str) -> Path:
    """Resolve a manifest reference like ``base/default.yaml``.

    Refs in personas.yaml are written relative to ``prompts_dir`` itself
    (e.g. ``base/default.yaml`` or ``roles/Lora.yaml``). For backward
    compatibility we also accept absolute paths and paths starting with
    the prompts dir name (e.g. ``prompts/base/default.yaml``).
    """
    if not ref:
        raise ValueError("Empty reference")

    p = Path(ref)
    if p.is_absolute() and p.exists():
        return p

    # Most common: refs are written like "prompts/base/default.yaml"
    repo_root = prompts_dir.parent
    candidates: list[Path] = []
    candidates.append(repo_root / p)
    candidates.append(prompts_dir / p)
    # Strip a leading "prompts/" segment if it duplicates prompts_dir name
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
    """Merge ``override`` on top of ``base``.

    - Dicts are merged recursively.
    - Lists and scalars from ``override`` replace those in ``base``
      (role-level customization should be able to fully replace base
      lists like ``rules`` or ``style`` when desired).
    """
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


class PromptBuilder:
    """Compose persona prompts from `prompts/` manifests."""

    def __init__(self, prompts_dir: str | Path = DEFAULT_PROMPTS_DIR) -> None:
        self.prompts_dir = Path(prompts_dir).resolve() if Path(prompts_dir).is_absolute() else Path(prompts_dir)
        manifest_path = self.prompts_dir / MANIFEST_RELPATH
        if not manifest_path.exists():
            # Try CWD-relative as a fallback
            alt = Path.cwd() / self.prompts_dir / MANIFEST_RELPATH
            if alt.exists():
                self.prompts_dir = (Path.cwd() / self.prompts_dir).resolve()
                manifest_path = alt
            else:
                raise FileNotFoundError(
                    f"Personas manifest not found: {manifest_path}"
                )
        self.manifest_path = manifest_path
        self.manifest = _read_yaml(manifest_path)
        self.default_persona_id: Optional[str] = self.manifest.get("default_persona_id")
        self.personas: dict[str, dict] = {
            p["id"]: p for p in self.manifest.get("personas", []) if "id" in p
        }

    def list_personas(self) -> list[str]:
        return [pid for pid, p in self.personas.items() if p.get("enabled", True)]

    def get_persona(self, persona_id: Optional[str] = None) -> dict:
        pid = persona_id or self.default_persona_id
        if not pid:
            raise ValueError(
                "No persona id supplied and personas.yaml has no default_persona_id"
            )
        if pid not in self.personas:
            raise ValueError(
                f"Unknown persona id: {pid!r}. Available: {list(self.personas)}"
            )
        persona = self.personas[pid]
        if persona.get("enabled") is False:
            raise ValueError(f"Persona {pid!r} is disabled in personas.yaml")
        return persona

    def load_merged(self, persona_id: Optional[str] = None) -> dict:
        """Return the merged dict (base + role) for a persona."""
        persona = self.get_persona(persona_id)
        merged: dict = {}
        base_ref = persona.get("base_ref")
        if base_ref:
            merged = _deep_merge(merged, _read_yaml(_resolve_ref(self.prompts_dir, base_ref)))
        role_ref = persona.get("role_ref")
        if role_ref:
            merged = _deep_merge(merged, _read_yaml(_resolve_ref(self.prompts_dir, role_ref)))
        # Stamp the persona id into meta for downstream debugging.
        meta = dict(merged.get("meta") or {})
        meta.setdefault("persona_id", persona.get("id"))
        merged["meta"] = meta
        return merged

    def build(self, persona_id: Optional[str] = None) -> str:
        """Build the final system prompt string."""
        merged = self.load_merged(persona_id)
        return render_system_prompt(merged)
