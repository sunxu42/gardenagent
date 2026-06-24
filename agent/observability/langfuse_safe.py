"""Deprecated: re-exports from shared.observability."""

from shared.observability.langfuse_safe import init_langfuse, safe_flush

__all__ = ["init_langfuse", "safe_flush"]
