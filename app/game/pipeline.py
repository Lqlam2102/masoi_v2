from __future__ import annotations

from dataclasses import dataclass, field

from app.game.effects import Effect, Kill, Reveal, resolve_damage
from app.game.intents import Intent
from app.game.roles import get_role
from app.game.state import GameState

PACK_ACTOR = "__pack__"


@dataclass(frozen=True)
class Death:
    player_id: str
    source: str


@dataclass
class NightResult:
    deaths: list[Death] = field(default_factory=list)
    reveals: list[Reveal] = field(default_factory=list)
    pending_hunters: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)


def collect_effects(state: GameState, intents: list[Intent]) -> list[Effect]:
    """Chạy resolve() của từng vai theo đúng resolve_priority."""
    ordered = sorted(intents, key=lambda i: get_role(i.role_id).resolve_priority)
    effects: list[Effect] = []
    for intent in ordered:
        effects.extend(get_role(intent.role_id).resolve(state, intent))
    return effects


def resolve_night(state: GameState, intents: list[Intent]) -> NightResult:
    effects = collect_effects(state, intents)
    reveals = [e for e in effects if isinstance(e, Reveal)]

    landed, damage_log = resolve_damage(state, effects)
    result = NightResult(reveals=reveals, log=list(damage_log))

    for kill in landed:
        _kill_player(state, kill, result)

    for line in result.log:
        state.add_log(f"Đêm {state.night}: {line}")
    guard_intent = next((i for i in intents if i.role_id == "guard"), None)
    state.guard_last_target = guard_intent.targets[0] if guard_intent else None
    return result


def _kill_player(state: GameState, kill: Kill, result: NightResult) -> None:
    player = state.get(kill.target)
    player.alive = False
    player.death_reason = kill.source.value
    player.death_night = state.night
    result.deaths.append(Death(player_id=player.id, source=kill.source.value))
