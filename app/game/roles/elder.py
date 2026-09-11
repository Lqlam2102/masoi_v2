from __future__ import annotations

from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction

ELDER_ARMOR = 1


@register
class Elder(Role):
    """Chịu được một đòn Sói. Độc/treo cổ/đạn Thợ Săn giết ngay."""

    id = "elder"
    name = "Già Làng"
    faction = Faction.VILLAGE
    night_phase = None
    acts_on_night = "none"
