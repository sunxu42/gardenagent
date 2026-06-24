"""Deprecated: use server.multimodal.session.backends.factory."""

from server.multimodal.session.backends.factory import BACKEND_REGISTRY as agent_to_class
from server.multimodal.session.backends.factory import SessionBackendFactory as AgentFactory
from server.multimodal.session.backends.factory import load_class

__all__ = ["AgentFactory", "agent_to_class", "load_class"]
