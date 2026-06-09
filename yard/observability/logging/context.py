from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_session_id: ContextVar[str | None] = ContextVar("garden_session_id", default=None)
_turn_id: ContextVar[str | None] = ContextVar("garden_turn_id", default=None)


def get_session_id() -> str | None:
    return _session_id.get()


def get_turn_id() -> str | None:
    return _turn_id.get()


def set_turn_id(turn_id: str | None) -> Token:
    return _turn_id.set(turn_id)


@contextmanager
def bind_session(session_id: str, turn_id: str | None = None) -> Iterator[None]:
    t_sess = _session_id.set(session_id)
    t_turn = _turn_id.set(turn_id)
    try:
        yield
    finally:
        _session_id.reset(t_sess)
        _turn_id.reset(t_turn)
