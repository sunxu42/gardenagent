"""Central `.config.yaml` reader — single load path for server and agent models."""

from __future__ import annotations

import os
from typing import Any

import yaml

from shared.config.paths import CONFIG_FILE

_FORBIDDEN_YAML_KEYS = frozenset(
    {
        "llm_api_key",
        "emotion_appraisal_api_key",
        "mem0_llm_api_key",
        "eval_llm_api_key",
        "llm_tool_calling",
    }
)

# Keys owned by shared.config.server.ServerConfig (flat YAML at repo root).
SERVER_CONFIG_KEYS = frozenset(
    {
        "host",
        "port",
        "input_modality",
        "output_modality",
        "handler_type",
        "agent_type",
        "audio_config",
        "tts_config",
    }
)


def read_config_yaml() -> dict[str, Any]:
    """Read `.config.yaml` from CWD; return {} when missing or invalid."""
    if not os.path.isfile(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def reject_forbidden_yaml_keys(raw: dict[str, Any]) -> None:
    """Reject secret fields that must live in `.env` only."""
    found = _FORBIDDEN_YAML_KEYS.intersection(raw.keys())
    if not found:
        return
    names = ", ".join(sorted(found))
    raise ValueError(
        f".config.yaml 含不允许的密钥/废弃字段: {names}。"
        " API Key 请写入 .env；llm_tool_calling 已移除。"
    )
