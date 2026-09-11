from __future__ import annotations

from app.game.effects import Effect, Kill, KillSource
from app.game.intents import Intent
from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction, GameState, Player


@register
class Wolf(Role):
    """Bầy sói bỏ phiếu chung; pipeline nhận một intent tổng hợp từ PACK_ACTOR."""

    id = "wolf"
    name = "Sói"
    faction = Faction.WOLF
    night_phase = "night_wolf"
    phase_order = 40
    resolve_priority = 40
    acts_on_night = "every"

    def candidates(self, state: GameState, actor: Player) -> list[str]:
        from app.game.roles import get_role

        return [
            p.id
            for p in state.alive_players()
            if get_role(p.role_id).faction is not Faction.WOLF
        ]

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        return [Kill(intent.targets[0], KillSource.WOLF)]
