"""与前端一致的 user_id 校验。"""

from __future__ import annotations

import re

USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


def normalize_user_id(value: str | None) -> str:
    if value is None:
        raise ValueError("user_id is required")
    uid = value.strip()
    if not USER_ID_PATTERN.match(uid):
        raise ValueError("invalid user_id")
    return uid
