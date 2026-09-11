from __future__ import annotations

from app.game.effects import Effect, Pair
from app.game.intents import Intent, InvalidIntent
from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction, GameState, Player


@register
class Cupid(Role):
    id = "cupid"
    name = "Cupid"
    faction = Faction.VILLAGE
    night_phase = "night_cupid"
    phase_order = 10
    resolve_priority = 10
    acts_on_night = "first"
    target_count = 2

    def candidates(self, state: GameState, actor: Player) -> list[str]:
        """Cupid được ghép cả chính mình."""
        return [p.id for p in state.alive_players()]

    def validate(self, state: GameState, intent: Intent) -> None:
        if len(set(intent.targets)) != 2:
            raise InvalidIntent("Cupid phải chọn hai người khác nhau")
        super().validate(state, intent)

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        return [Pair(intent.targets[0], intent.targets[1])]
