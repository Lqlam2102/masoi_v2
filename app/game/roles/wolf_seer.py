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

    def _verdict(self, state: GameState, target_id: str) -> str:
        from app.game.roles import get_role

        target = state.get(target_id)
        return f"{target.name} là {get_role(target.role_id).name}"

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        return [
            Reveal(intent.actor_id, intent.targets[0],
                   self._verdict(state, intent.targets[0]))
        ]

    def instant_reveal(self, state: GameState, intent: Intent) -> str | None:
        return self._verdict(state, intent.targets[0])
