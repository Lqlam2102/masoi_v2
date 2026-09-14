from __future__ import annotations

from app.game.effects import Effect, Reveal
from app.game.intents import Intent
from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction, GameState


@register
class Seer(Role):
    id = "seer"
    name = "Tiên Tri"
    faction = Faction.VILLAGE
    night_phase = "night_seer"
    phase_order = 20
    resolve_priority = 20
    acts_on_night = "every"

    def _verdict(self, state: GameState, target_id: str) -> str:
        from app.game.roles import get_role

        target = state.get(target_id)
        is_wolf = get_role(target.role_id).faction is Faction.WOLF
        verdict = "thuộc phe Sói" if is_wolf else "KHÔNG thuộc phe Sói"
        return f"{target.name} {verdict}"

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        return [
            Reveal(intent.actor_id, intent.targets[0],
                   self._verdict(state, intent.targets[0]))
        ]

    def instant_reveal(self, state: GameState, intent: Intent) -> str | None:
        return self._verdict(state, intent.targets[0])
