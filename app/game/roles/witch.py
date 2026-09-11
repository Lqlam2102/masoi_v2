from __future__ import annotations

from app.game.effects import Effect, Heal, Kill, KillSource
from app.game.intents import Intent, InvalidIntent
from app.game.roles import register
from app.game.roles.base import Role
from app.game.state import Faction, GameState


@register
class Witch(Role):
    id = "witch"
    name = "Phù Thủy"
    faction = Faction.VILLAGE
    night_phase = "night_witch"
    phase_order = 50
    resolve_priority = 50
    acts_on_night = "every"
    target_count = 0

    def validate(self, state: GameState, intent: Intent) -> None:
        heal = intent.extra.get("heal")
        poison = intent.extra.get("poison")
        if heal and state.witch_heal_used:
            raise InvalidIntent("Bình cứu đã dùng hết")
        if poison and state.witch_poison_used:
            raise InvalidIntent("Bình độc đã dùng hết")
        for pid in (heal, poison):
            if pid is not None and not state.is_alive(pid):
                raise InvalidIntent("Mục tiêu không hợp lệ")

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        effects: list[Effect] = []
        heal = intent.extra.get("heal")
        poison = intent.extra.get("poison")
        if heal:
            effects.append(Heal(heal))
            state.witch_heal_used = True
        if poison:
            effects.append(Kill(poison, KillSource.WITCH))
            state.witch_poison_used = True
        return effects
