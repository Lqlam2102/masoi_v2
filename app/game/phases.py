from __future__ import annotations

from app.game.effects import Kill, KillSource, Reveal
from app.game.intents import Intent, InvalidIntent
from app.game.pipeline import (
    PACK_ACTOR,
    NightResult,
    apply_deaths,
    apply_hunter_shot,
    pending_bite,
    resolve_night,
)
from app.game.roles import REGISTRY, get_role
from app.game.state import Faction, GameState
from app.game.votes import tally
from app.game.winner import check_winner


def night_phase_order() -> list[tuple[int, str]]:
    """Các sub-pha đêm, sắp theo phase_order. Bầy sói gộp thành một pha."""
    seen: dict[str, int] = {}
    for role in REGISTRY.values():
        if role.night_phase and role.night_phase not in seen:
            seen[role.night_phase] = role.phase_order
    return sorted(((order, name) for name, order in seen.items()))


class PhaseMachine:
    """Điều phối vòng chơi. Thuần sync — timer và broadcast nằm ở lớp Room."""

    def __init__(self, state: GameState) -> None:
        self.state = state
        self.phase = "lobby"
        self.night_intents: list[Intent] = []
        self.wolf_votes: dict[str, str] = {}
        self.votes: dict[str, str] = {}
        self.winner: str | None = None
        self.last_result: NightResult | None = None
        self.pending_hunters: list[str] = []
        # Ai đã chủ động bỏ lượt trong pha hiện tại.
        self.passed: set[str] = set()
        # Reveal gửi ngay lúc hành động (Tiên Tri), chờ lớp Room lấy đi.
        self.instant_reveals: list[Reveal] = []
        self._delivered_reveals: set[tuple[str, str]] = set()

    # ---------- mở pha ----------

    def start(self) -> None:
        if self.state.night == 0:
            self.state.night = 1
        self.night_intents = []
        self.wolf_votes = {}
        self._open_next_night_phase(after=None)

    def _open_next_night_phase(self, after: str | None) -> None:
        order = night_phase_order()
        start_index = 0
        if after is not None:
            start_index = next(
                i for i, (_, name) in enumerate(order) if name == after
            ) + 1

        for _, phase_name in order[start_index:]:
            if self._actors_for(phase_name):
                self._set_phase(phase_name)
                return
        self._set_phase("night_result")

    def _actors_for(self, phase_name: str) -> list[str]:
        """Ai còn sống và được hành động trong sub-pha này."""
        actors: list[str] = []
        for player in self.state.alive_players():
            role = get_role(player.role_id)
            if role.night_phase == phase_name and role.acts_tonight(self.state):
                actors.append(player.id)
        if phase_name == "night_wolf":
            actors = [
                p.id
                for p in self.state.alive_players()
                if get_role(p.role_id).faction is Faction.WOLF
            ]
        return actors

    def current_actors(self) -> list[str]:
        if self.phase == "hunter_shot":
            return self.pending_hunters[:1]
        if self.phase == "day_vote":
            return [p.id for p in self.state.alive_players()]
        if self.phase.startswith("night_") and self.phase != "night_result":
            return self._actors_for(self.phase)
        return []

    # ---------- nhận hành động ----------

    def submit_action(
        self, actor_id: str, targets: tuple[str, ...], extra: dict | None = None
    ) -> None:
        if actor_id not in self.current_actors():
            raise InvalidIntent("Không phải lượt của bạn")

        if self.phase == "hunter_shot":
            self._hunter_target = targets[0] if targets else None
            return

        role_id = self.state.get(actor_id).role_id
        if self.phase == "night_wolf":
            if not targets:
                raise InvalidIntent("Phải chọn mục tiêu")
            get_role("wolf").validate(
                self.state, Intent(actor_id, "wolf", targets, {})
            )
            self.wolf_votes[actor_id] = targets[0]
            return

        intent = Intent(actor_id, role_id, targets, extra or {})
        role = get_role(role_id)
        role.validate(self.state, intent)
        self.night_intents = [i for i in self.night_intents if i.actor_id != actor_id]
        self.night_intents.append(intent)
        self.passed.discard(actor_id)
        self._queue_instant_reveal(role, intent)

    def _queue_instant_reveal(self, role, intent: Intent) -> None:
        """Vai soi biết kết quả ngay trong lượt của mình, không đợi tới sáng."""
        text = role.instant_reveal(self.state, intent)
        if not text:
            return
        self.instant_reveals.append(Reveal(intent.actor_id, intent.targets[0], text))
        self._delivered_reveals.add((intent.actor_id, text))

    def take_instant_reveals(self) -> list[Reveal]:
        pending, self.instant_reveals = self.instant_reveals, []
        return pending

    def submit_pass(self, actor_id: str) -> None:
        """Người chơi chủ động bỏ lượt — tính là đã hành động."""
        if actor_id not in self.current_actors():
            raise InvalidIntent("Không phải lượt của bạn")
        self.passed.add(actor_id)
        if self.phase == "day_vote":
            self.votes.pop(actor_id, None)

    def submit_vote(self, voter_id: str, target_id: str | None) -> None:
        if voter_id not in [p.id for p in self.state.alive_players()]:
            raise InvalidIntent("Người chết không được bỏ phiếu")
        if target_id is None:
            self.votes.pop(voter_id, None)
            self.passed.add(voter_id)   # phiếu trắng vẫn là đã quyết định
            return
        if not self.state.is_alive(target_id):
            raise InvalidIntent("Mục tiêu không hợp lệ")
        self.votes[voter_id] = target_id
        self.passed.discard(voter_id)

    def everyone_acted(self) -> bool:
        actors = set(self.current_actors())
        if not actors:
            return True
        if self.phase == "night_wolf":
            return actors <= set(self.wolf_votes) | self.passed
        if self.phase == "day_vote":
            return actors <= set(self.votes) | self.passed
        if self.phase == "hunter_shot":
            return hasattr(self, "_hunter_target") or bool(actors & self.passed)
        return actors <= {i.actor_id for i in self.night_intents} | self.passed

    def bite_target_for_witch(self) -> str | None:
        return pending_bite(self._pack_intents())

    def _pack_intents(self) -> list[Intent]:
        victim = tally(self.wolf_votes)
        if victim is None:
            return []
        return [Intent(PACK_ACTOR, "wolf", (victim,), {})]

    # ---------- đóng pha, mở pha kế ----------

    def advance(self) -> str:
        if self.phase == "night_wolf":
            self.night_intents.extend(self._pack_intents())
            if not self.wolf_votes or tally(self.wolf_votes) is None:
                self.state.add_log(f"Đêm {self.state.night}: bầy Sói không thống nhất")
            self._open_next_night_phase(after="night_wolf")
        elif self.phase.startswith("night_") and self.phase != "night_result":
            self._open_next_night_phase(after=self.phase)
        elif self.phase == "night_result":
            self._finish_night()
        elif self.phase == "day_discuss":
            self.votes = {}
            self._set_phase("day_vote")
        elif self.phase == "day_vote":
            self._finish_day_vote()
        elif self.phase == "day_result":
            self._start_new_night()
        elif self.phase == "hunter_shot":
            self._finish_hunter_shot()
        return self.phase

    def _set_phase(self, name: str) -> str:
        self.phase = name
        self.state.phase = name
        self.passed = set()
        return name

    def _finish_night(self) -> None:
        self.last_result = resolve_night(self.state, self.night_intents)
        # Reveal đã báo ngay trong đêm thì không lặp lại lúc bình minh.
        self.last_result.reveals = [
            r for r in self.last_result.reveals
            if (r.actor, r.text) not in self._delivered_reveals
        ]
        self._delivered_reveals.clear()
        self.pending_hunters = list(self.last_result.pending_hunters)
        self._after_deaths(next_phase="day_discuss")

    def _finish_day_vote(self) -> None:
        victim = tally(self.votes)
        if victim is None:
            self.state.add_log("Ngày: dân làng không thống nhất — không ai bị treo cổ")
            self.last_result = NightResult()
            self._set_phase("day_result")
            return

        if self.state.get(victim).role_id == "fool":
            self.state.fool_lynched = True

        self.last_result = apply_deaths(self.state, [Kill(victim, KillSource.LYNCH)])
        self.state.add_log(f"Ngày: {self.state.get(victim).name} bị treo cổ")
        for line in self.last_result.log:
            self.state.add_log(line)
        self.pending_hunters = list(self.last_result.pending_hunters)
        self._after_deaths(next_phase="day_result")

    def _finish_hunter_shot(self) -> None:
        hunter_id = self.pending_hunters.pop(0)
        target = getattr(self, "_hunter_target", None)
        if hasattr(self, "_hunter_target"):
            del self._hunter_target

        result = apply_hunter_shot(self.state, hunter_id, target)
        self.pending_hunters.extend(result.pending_hunters)
        self.last_result = result
        self._after_deaths(next_phase=self._phase_after_hunter)

    def _after_deaths(self, next_phase: str) -> None:
        """Sau mỗi lần có người chết: check thắng → Thợ Săn → pha kế."""
        self.winner = check_winner(self.state)
        if self.winner is not None:
            self._set_phase("game_over")
            return
        if self.pending_hunters:
            self._phase_after_hunter = next_phase
            self._set_phase("hunter_shot")
            return
        self._set_phase(next_phase)

    def _start_new_night(self) -> None:
        self.state.night += 1
        self.night_intents = []
        self.wolf_votes = {}
        self._open_next_night_phase(after=None)
