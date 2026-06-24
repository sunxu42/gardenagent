"""Deprecated: use shared.config.agent."""

from shared.config.agent import AgentConfig, Config, load_agent_settings

load_settings = load_agent_settings

__all__ = ["AgentConfig", "Config", "load_agent_settings", "load_settings"]
