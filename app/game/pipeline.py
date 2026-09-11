from __future__ import annotations

from dataclasses import dataclass, field

from app.game.effects import Effect, Kill, KillSource, Pair, Reveal, resolve_damage
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


def pending_bite(intents: list[Intent]) -> str | None:
    """Nạn nhân bầy sói nhắm tới — Phù Thủy được biết trước khi quyết định."""
    for intent in intents:
        if intent.role_id == "wolf" and intent.targets:
            return intent.targets[0]
    return None


def collect_effects(state: GameState, intents: list[Intent]) -> list[Effect]:
    """Chạy resolve() của từng vai theo đúng resolve_priority."""
    ordered = sorted(intents, key=lambda i: get_role(i.role_id).resolve_priority)
    effects: list[Effect] = []
    for intent in ordered:
        effects.extend(get_role(intent.role_id).resolve(state, intent))
    return effects


def apply_deaths(state: GameState, kills: list[Kill]) -> NightResult:
    """Giết người và lan chuỗi chết (người yêu). Dùng cho cả đêm lẫn ngày."""
    result = NightResult()
    queue = list(kills)
    while queue:
        kill = queue.pop(0)
        player = state.players.get(kill.target)
        if player is None or not player.alive:
            continue

        player.alive = False
        player.death_reason = kill.source.value
        player.death_night = state.night
        result.deaths.append(Death(player_id=player.id, source=kill.source.value))

        if player.role_id == "hunter":
            result.pending_hunters.append(player.id)

        if player.lover_id and state.is_alive(player.lover_id):
            lover = state.get(player.lover_id)
            result.log.append(f"{lover.name}: chết theo người yêu")
            queue.append(Kill(lover.id, KillSource.LOVER))
    return result


def apply_hunter_shot(
    state: GameState, hunter_id: str, target_id: str | None
) -> NightResult:
    """Thợ Săn đã chết bắn một phát không thể chặn."""
    if target_id is None or not state.is_alive(target_id):
        state.add_log(f"{state.get(hunter_id).name}: Thợ Săn không bắn ai")
        return NightResult()

    result = apply_deaths(state, [Kill(target_id, KillSource.HUNTER)])
    state.add_log(
        f"{state.get(hunter_id).name} (Thợ Săn) bắn {state.get(target_id).name}"
    )
    return result


def resolve_night(state: GameState, intents: list[Intent]) -> NightResult:
    effects = collect_effects(state, intents)

    for pair in [e for e in effects if isinstance(e, Pair)]:
        state.get(pair.a).lover_id = pair.b
        state.get(pair.b).lover_id = pair.a

    landed, damage_log = resolve_damage(state, effects)

    result = apply_deaths(state, landed)
    result.reveals = [e for e in effects if isinstance(e, Reveal)]
    result.log = damage_log + result.log

    guard_intent = next((i for i in intents if i.role_id == "guard"), None)
    state.guard_last_target = guard_intent.targets[0] if guard_intent else None

    for line in result.log:
        state.add_log(f"Đêm {state.night}: {line}")
    return result
