from __future__ import annotations

from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction


@register
class Fool(Role):
    """Thắng một mình nếu bị dân làng treo cổ."""

    id = "fool"
    name = "Thằng Ngố"
    faction = Faction.VILLAGE
    night_phase = None
    acts_on_night = "none"
