from __future__ import annotations

from dataclasses import dataclass, field


class InvalidIntent(Exception):
    """Hành động không hợp lệ — server trả lỗi, không đổi state."""


@dataclass(frozen=True)
class Intent:
    actor_id: str
    role_id: str
    targets: tuple[str, ...] = ()
    extra: dict = field(default_factory=dict)
