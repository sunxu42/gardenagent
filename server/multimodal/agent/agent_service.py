"""Deprecated: use server.multimodal.session."""

from server.multimodal.session.backends.factory import SessionBackendFactory as AgentFactory
from server.multimodal.session.session_service import SessionService as AgentService

__all__ = ["AgentFactory", "AgentService"]
