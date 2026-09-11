from __future__ import annotations

from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction


@register
class Hunter(Role):
    """Không hành động ban đêm — bắn khi chết, do pipeline mở pha riêng."""

    id = "hunter"
    name = "Thợ Săn"
    faction = Faction.VILLAGE
    night_phase = None
    acts_on_night = "none"
