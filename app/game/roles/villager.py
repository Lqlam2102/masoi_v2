from __future__ import annotations

from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction


@register
class Villager(Role):
    id = "villager"
    name = "Dân Thường"
    faction = Faction.VILLAGE
    night_phase = None
    acts_on_night = "none"
