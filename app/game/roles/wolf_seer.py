from __future__ import annotations

from app.game.effects import Effect, Reveal
from app.game.intents import Intent
from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction, GameState


@register
class WolfSeer(Role):
    """Vẫn cắn cùng bầy; thêm quyền soi ra vai chính xác."""

    id = "wolf_seer"
    name = "Sói Tiên Tri"
    faction = Faction.WOLF
    night_phase = "night_wolf_seer"
    phase_order = 25
    resolve_priority = 25
    acts_on_night = "every"

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        from app.game.roles import get_role

        target = state.get(intent.targets[0])
        role_name = get_role(target.role_id).name
        return [Reveal(intent.actor_id, target.id, f"{target.name} là {role_name}")]
