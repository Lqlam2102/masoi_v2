from __future__ import annotations

from app.game.effects import Effect
from app.game.intents import Intent, InvalidIntent
from app.game.state import Faction, GameState, Player


class Role:
    """Khai báo một vai. Mỗi vai là một subclass, đăng ký vào REGISTRY."""

    id: str = ""
    name: str = ""
    faction: Faction = Faction.VILLAGE
    night_phase: str | None = None
    phase_order: int = 0
    resolve_priority: int = 0
    acts_on_night: str = "none"  # none | first | every | even
    target_count: int = 1

    def acts_tonight(self, state: GameState) -> bool:
        if self.acts_on_night == "none":
            return False
        if self.acts_on_night == "first":
            return state.night == 1
        if self.acts_on_night == "even":
            return state.night % 2 == 0
        return True

    def candidates(self, state: GameState, actor: Player) -> list[str]:
        """Mặc định: mọi người còn sống trừ chính mình."""
        return [p.id for p in state.alive_players() if p.id != actor.id]

    def validate(self, state: GameState, intent: Intent) -> None:
        if len(intent.targets) != self.target_count:
            raise InvalidIntent(f"{self.name} phải chọn {self.target_count} mục tiêu")
        actor = state.players.get(intent.actor_id)
        if actor is None:
            raise InvalidIntent("Người chơi không tồn tại")
        allowed = set(self.candidates(state, actor))
        for target in intent.targets:
            if target not in allowed:
                raise InvalidIntent("Mục tiêu không hợp lệ")

    def resolve(self, state: GameState, intent: Intent) -> list[Effect]:
        return []
