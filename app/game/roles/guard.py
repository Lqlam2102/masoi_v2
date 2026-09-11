from __future__ import annotations

from app.game.effects import Effect, Protect
from app.game.intents import Intent, InvalidIntent
from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction, GameState, Player


@register
class Guard(Role):
    id = "guard"
    name = "Bảo Vệ"
    faction = Faction.VILLAGE
    night_phase = "night_guard"
    phase_order = 30
    resolve_priority = 30
    acts_on_night = "every"

    def candidates(self, state: GameState, actor: Player) -> list[str]:
        """Được tự bảo vệ, nhưng không lặp lại mục tiêu đêm trước."""
        return [
            p.id for p in state.alive_players() if p.id != state.guard_last_target
        ]

    def validate(self, state: GameState, intent: Intent) -> None:
        if intent.targets and intent.targets[0] == state.guard_last_target:
            raise InvalidIntent("Không được bảo vệ cùng một người hai đêm liên tiếp")
        super().validate(state, intent)

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        return [Protect(intent.targets[0])]
