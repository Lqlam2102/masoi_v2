from __future__ import annotations

from app.game.roles import get_role
from app.game.state import Faction, GameState

WINNER_LABEL: dict[str, str] = {
    "village": "Phe Dân thắng",
    "wolf": "Phe Sói thắng",
    "white_wolf": "Sói Trắng thắng một mình",
    "lovers": "Cặp đôi thắng",
    "fool": "Thằng Ngố thắng",
}


def check_winner(state: GameState) -> str | None:
    """Kiểm tra theo đúng thứ tự ưu tiên trong spec mục 8."""
    if state.fool_lynched:
        return "fool"

    alive = state.alive_players()

    if len(alive) == 2:
        a, b = alive
        cross_faction = get_role(a.role_id).faction is not get_role(b.role_id).faction
        if a.lover_id == b.id and b.lover_id == a.id and cross_faction:
            return "lovers"

    if len(alive) == 1 and alive[0].role_id == "white_wolf":
        return "white_wolf"

    wolves = [p for p in alive if get_role(p.role_id).faction is Faction.WOLF]
    if not wolves:
        return "village"
    if len(wolves) >= len(alive) - len(wolves):
        return "wolf"
    return None
