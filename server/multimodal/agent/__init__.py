"""Deprecated: use server.multimodal.session."""

from server.multimodal.session import SessionService

AgentService = SessionService

__all__ = ["AgentService", "SessionService"]
