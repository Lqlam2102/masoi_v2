from __future__ import annotations

from app.game.phases import PhaseMachine
from app.game.roles import get_role
from app.game.state import Faction, GameState


def can_see_role(state: GameState, viewer_id: str, target_id: str) -> bool:
    """Xem spec mục 9 — nguyên tắc bảo mật thông tin."""
    viewer = state.players.get(viewer_id)
    target = state.players.get(target_id)
    if viewer is None or target is None:
        return False
    if viewer_id == target_id or not target.alive:
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
            "action": "pick",
            "count": 1,
            "candidates": [p.id for p in state.alive_players()],
        }

    role = get_role("wolf" if machine.phase == "night_wolf" else actor.role_id)
    if role.id == "witch":
        return {
            "action": "witch",
            "count": 0,
            "bitten": machine.bite_target_for_witch(),
            "heal_used": state.witch_heal_used,
            "poison_used": state.witch_poison_used,
            "candidates": [p.id for p in state.alive_players()],
        }
    return {
        "action": "pick",
        "count": role.target_count,
        "candidates": role.candidates(state, actor),
    }


def state_view(machine: PhaseMachine, viewer_id: str, deadline: float | None) -> dict:
    state = machine.state
    return {
        "type": "state",
        "phase": machine.phase,
        "night": state.night,
        "deadline": deadline,
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "alive": p.alive,
                "role": p.role_id if can_see_role(state, viewer_id, p.id) else None,
                "role_name": get_role(p.role_id).name
                if can_see_role(state, viewer_id, p.id)
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
    }
