from __future__ import annotations

from app.game.phases import PhaseMachine
from app.game.roles import get_role
from app.game.state import Faction, GameState


def can_see_role(state: GameState, viewer_id: str, target_id: str,
                 reveal_role_on_death: bool = True) -> bool:
    """Xem spec mục 9 — nguyên tắc bảo mật thông tin."""
    viewer = state.players.get(viewer_id)
    target = state.players.get(target_id)
    if viewer is None or target is None:
        return False
    if viewer_id == target_id:
        return True
    if not target.alive and reveal_role_on_death:
        return True
    if viewer.lover_id == target_id:
        return True
    viewer_is_wolf = get_role(viewer.role_id).faction is Faction.WOLF
    target_is_wolf = get_role(target.role_id).faction is Faction.WOLF
    return viewer_is_wolf and target_is_wolf


def prompt_for(machine: PhaseMachine, viewer_id: str) -> dict | None:
    """Nội dung ô hành động cho người xem, hoặc None nếu không tới lượt."""
    if viewer_id not in machine.current_actors():
        return None
    state = machine.state
    actor = state.get(viewer_id)

    if machine.phase == "day_vote":
        return {
            "action": "vote",
            "count": 1,
            "candidates": [p.id for p in state.alive_players()],
        }
    if machine.phase == "hunter_shot":
        return {
            "action": "shoot",
            "count": 1,
            "candidates": [p.id for p in state.alive_players()],
        }

    role = get_role("wolf" if machine.phase == "night_wolf" else actor.role_id)
    if role.id == "witch":
        bitten = machine.bite_target_for_witch()
        return {
            "action": "witch",
            "count": 0,
            "bitten": bitten,
            "heal_used": state.witch_heal_used,
            "poison_used": state.witch_poison_used,
            # Bình cứu chỉ dùng được khi còn bình VÀ đêm nay có người bị cắn.
            "can_heal": not state.witch_heal_used and bitten is not None,
            "can_poison": not state.witch_poison_used,
            "candidates": [p.id for p in state.alive_players()],
        }
    return {
        "action": "pick",
        "role": role.id,
        "count": role.target_count,
        "candidates": role.candidates(state, actor),
    }


def _is_wolf(state: GameState, player_id: str) -> bool:
    player = state.players.get(player_id)
    return player is not None and get_role(player.role_id).faction is Faction.WOLF


def chat_channel_for(machine: PhaseMachine, viewer_id: str) -> str | None:
    """Kênh người này được NÓI vào lúc này, hoặc None nếu phải im lặng.

    Ban đêm cả làng ngủ nên chỉ bầy Sói bàn với nhau; ban ngày ai còn sống
    cũng nói được. Người chết chỉ đọc, không nói.
    """
    state = machine.state
    if not state.is_alive(viewer_id):
        return None
    if machine.phase.startswith("night_") and machine.phase != "night_result":
        return "wolf" if _is_wolf(state, viewer_id) else None
    if machine.phase in ("day_discuss", "day_vote", "day_result", "night_result"):
        return "village"
    return None


def can_read_chat(machine: PhaseMachine, viewer_id: str, channel: str) -> bool:
    """Kênh sói là bí mật — chỉ phe Sói đọc được, kể cả khi đã chết."""
    if channel == "wolf":
        return _is_wolf(machine.state, viewer_id)
    return viewer_id in machine.state.players


def live_votes(machine: PhaseMachine, viewer_id: str) -> dict | None:
    """Phiếu đang bỏ, cập nhật realtime để mọi người thấy nhau chọn ai.

    Pha đêm của Sói chỉ bầy Sói thấy; pha treo cổ ban ngày thì công khai.
    """
    if machine.phase == "night_wolf":
        if not _is_wolf(machine.state, viewer_id):
            return None
        raw, scope = machine.wolf_votes, "wolf"
    elif machine.phase == "day_vote":
        raw, scope = machine.votes, "all"
    else:
        return None

    counts: dict[str, int] = {}
    for target in raw.values():
        counts[target] = counts.get(target, 0) + 1
    leaders = sorted(counts.values(), reverse=True)
    return {
        "scope": scope,
        "by_voter": dict(raw),
        "counts": counts,
        # Hoà phiếu ở đỉnh nghĩa là chưa chốt được ai.
        "decided": bool(leaders) and (len(leaders) == 1 or leaders[0] > leaders[1]),
        "pending": [
            p.id for p in machine.state.alive_players()
            if p.id in machine.current_actors() and p.id not in raw
        ],
    }


def state_view(
    machine: PhaseMachine,
    viewer_id: str,
    deadline: float | None,
    duration: int | None = None,
    reveal_role_on_death: bool = True,
) -> dict:
    state = machine.state
    return {
        "type": "state",
        "phase": machine.phase,
        "night": state.night,
        "deadline": deadline,
        "duration": duration,
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "alive": p.alive,
                "role": p.role_id if can_see_role(state, viewer_id, p.id, reveal_role_on_death) else None,
                "role_name": get_role(p.role_id).name
                if can_see_role(state, viewer_id, p.id, reveal_role_on_death)
                else None,
            }
            for p in state.players.values()
        ],
        "you": {
            "id": viewer_id,
            "role": state.get(viewer_id).role_id,
            "role_name": get_role(state.get(viewer_id).role_id).name,
            "alive": state.is_alive(viewer_id),
            "lover": state.get(viewer_id).lover_id,
        },
        "prompt": prompt_for(machine, viewer_id),
        "votes": live_votes(machine, viewer_id),
        "chat_channel": chat_channel_for(machine, viewer_id),
    }
