"""Load soul.yaml into a persona profile (voice, baseline, display name)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

import yaml
from shared.config.paths import DEFAULT_PROMPTS_DIR
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.AGENT)

SOUL_RELPATH = Path("soul.yaml")
SKIP_RENDER_KEYS = frozenset({"meta", "voice", "baseline", "relationship_baseline"})
DEFAULT_VOICE_TYPE = "longanlingxin"
DEFAULT_BASELINE = {"v": 0.3, "a": 0.55, "d": 0.1}


def _read_yaml(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {}
    return data


def _is_blank_scalar(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return len(list(value)) == 0
    return False


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


def _render_generic_value(title: str, value: Any, blocks: list[str]) -> None:
    if _is_blank_scalar(value):
        return
    if isinstance(value, dict):
        for key, child in value.items():
            child_title = f"{title}.{key}" if title else str(key)
            _render_generic_value(child_title, child, blocks)
        return
    if isinstance(value, list):
        if value and isinstance(value[0], dict):
            section_lines = [f"## {title}"]
            for item in value:
                if not isinstance(item, dict):
                    continue
                ex_id = str(item.get("id") or "").strip()
                user = str(item.get("user") or "").strip()
                assistant = str(item.get("assistant") or "").strip()
                if not ex_id:
                    continue
                section_lines.append(f"### {ex_id}")
                if user:
                    section_lines.append(f"User: {user}")
                if assistant:
                    section_lines.append(f"Assistant: {assistant}")
                section_lines.append("")
            body = "\n".join(section_lines).strip()
            if body:
                blocks.append(body)
            return
        lines = _as_lines(value)
        if lines:
            blocks.append(f"## {title}\n" + "\n".join(f"- {line}" for line in lines))
        return
    text = str(value).strip()
    if text:
        blocks.append(f"## {title}\n{text}")


def render_system_prompt_generic(data: dict) -> str:
    """Render a soul.yaml dict into markdown system-prompt blocks."""
    blocks: list[str] = []
    for key, value in data.items():
        if key in SKIP_RENDER_KEYS:
            continue
        _render_generic_value(str(key), value, blocks)
    return "\n\n".join(blocks).strip()


class SoulProfileLoader:
    """Reload ``soul.yaml`` from disk on each ``build`` / ``resolve_profile``."""

    def __init__(self, prompts_dir: str | Path = DEFAULT_PROMPTS_DIR) -> None:
        self.prompts_dir = Path(prompts_dir)
        self._soul_path = self._resolve_soul_path()

    def _resolve_soul_path(self) -> Path:
        candidates = [
            self.prompts_dir / SOUL_RELPATH,
            Path.cwd() / self.prompts_dir / SOUL_RELPATH,
        ]
        for path in candidates:
            if path.exists():
                return path.resolve()
        tried = ", ".join(str(p) for p in candidates)
        raise FileNotFoundError(f"soul.yaml not found. Tried: {tried}")

    def load_soul(self) -> dict:
        return _read_yaml(self._soul_path)

    def build(self, persona_id: Optional[str] = None) -> str:
        if persona_id:
            _log.debug(f"persona_id={persona_id!r} ignored; using soul.yaml")
        return render_system_prompt_generic(self.load_soul())

    def resolve_profile(self, persona_id: Optional[str] = None) -> dict[str, Any]:
        if persona_id:
            _log.debug(f"persona_id={persona_id!r} ignored; using soul.yaml")
        data = self.load_soul()
        meta = data.get("meta") or {}
        role_name = str(meta.get("role_name") or "").strip()
        display_name = str(meta.get("display_name") or "").strip()
        assistant_label = display_name or role_name or "助手"

        voice_block = data.get("voice") if isinstance(data.get("voice"), dict) else {}
        baseline_block = data.get("baseline") if isinstance(data.get("baseline"), dict) else {}
        voice_type = str(voice_block.get("type") or DEFAULT_VOICE_TYPE).strip()
        bl = {**DEFAULT_BASELINE, **{k: baseline_block[k] for k in ("v", "a", "d") if k in baseline_block}}
        rel_block = (
            data.get("relationship_baseline")
            if isinstance(data.get("relationship_baseline"), dict)
            else {}
        )
        rel_trust = float(rel_block.get("trust", 0.5))
        rel_warmth = float(rel_block.get("warmth", 0.4))

        return {
            "persona_id": "soul",
            "display_name": display_name or assistant_label,
            "role_name": role_name or None,
            "assistant_label": assistant_label,
            "voice_type": voice_type,
            "baseline": {
                "v": float(bl["v"]),
                "a": float(bl["a"]),
                "d": float(bl["d"]),
            },
            "relationship_baseline": {
                "trust": rel_trust,
                "warmth": rel_warmth,
            },
        }


def resolve_soul_profile(
    prompts_dir: str | Path = DEFAULT_PROMPTS_DIR,
    persona_id: Optional[str] = None,
) -> dict[str, Any]:
    """Return voice/baseline/display fields from soul.yaml."""
    return SoulProfileLoader(prompts_dir).resolve_profile(persona_id)


# Backward-compatible aliases
SoulYamlLoader = SoulProfileLoader
_SoulYamlComposer = SoulProfileLoader
