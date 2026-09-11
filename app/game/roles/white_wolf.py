from __future__ import annotations

from app.game.effects import Effect, Kill, KillSource
from app.game.intents import Intent
from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction, GameState, Player


@register
class WhiteWolf(Role):
    """Các đêm chẵn được giết thêm một Sói khác. Thắng một mình."""

    id = "white_wolf"
    name = "Sói Trắng"
    faction = Faction.WOLF
    night_phase = "night_white_wolf"
    phase_order = 45
    resolve_priority = 45
    acts_on_night = "even"

    def candidates(self, state: GameState, actor: Player) -> list[str]:
        from app.game.roles import get_role

        return [
            p.id
            for p in state.alive_players()
            if p.id != actor.id and get_role(p.role_id).faction is Faction.WOLF
        ]

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        return [Kill(intent.targets[0], KillSource.WHITE_WOLF)]
