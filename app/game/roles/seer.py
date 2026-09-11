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

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        from app.game.roles import get_role

        target = state.get(intent.targets[0])
        is_wolf = get_role(target.role_id).faction is Faction.WOLF
        verdict = "thuộc phe Sói" if is_wolf else "KHÔNG thuộc phe Sói"
        return [Reveal(intent.actor_id, target.id, f"{target.name} {verdict}")]
