from __future__ import annotations

import random
import secrets
import string
import time

from app.game.intents import InvalidIntent
from app.game.phases import PhaseMachine
from app.game.setup import build_state
from app.protocol import parse_client_msg
from app.views import state_view

DEFAULT_TIMERS: dict[str, int] = {
    "night": 30,
    "day_discuss": 180,
    "day_vote": 60,
    "hunter_shot": 30,
}

CODE_ALPHABET = string.ascii_uppercase + string.digits


class Room:
    def __init__(self, code: str, rng: random.Random) -> None:
        self.code = code
        self.rng = rng
        self.players: dict[str, str] = {}
        self.tokens: dict[str, str] = {}
        self.host_id: str | None = None
        self.machine: PhaseMachine | None = None
        self.deadline: float | None = None
        self.timers = dict(DEFAULT_TIMERS)
        self.disabled_roles: set[str] = set()

    # ---------- ghế ngồi ----------

    def join(self, name: str, token: str | None) -> tuple[str, str]:
        if token and token in self.tokens:
            return self.tokens[token], token
        if self.machine is not None:
            raise InvalidIntent("Ván đang diễn ra, không thể vào thêm")

        player_id = f"p{len(self.players) + 1}"
        new_token = secrets.token_urlsafe(12)
        self.players[player_id] = name
        self.tokens[new_token] = player_id
        if self.host_id is None:
            self.host_id = player_id
        return player_id, new_token

    # ---------- vòng chơi ----------

    def start(self) -> None:
        state = build_state(dict(self.players), self.rng, self.disabled_roles)
        self.machine = PhaseMachine(state)
        self.machine.start()
        self._reset_deadline()

    def handle(self, player_id: str, raw: dict) -> None:
        msg = parse_client_msg(raw)
        if msg.type == "config":
            self._require_host(player_id)
            self.disabled_roles = set(msg.disabled_roles)
            self.timers.update(msg.timers)
            return
        if msg.type == "start":
            self._require_host(player_id)
            self.start()
            return

        if self.machine is None:
            raise InvalidIntent("Ván chưa bắt đầu")
        if msg.type == "action":
            self.machine.submit_action(player_id, tuple(msg.targets), msg.extra)
        elif msg.type == "vote":
            self.machine.submit_vote(player_id, msg.target)

        if self.machine.everyone_acted():
            self.advance()

    def advance(self) -> None:
        if self.machine is None:
            return
        self.machine.advance()
        self._reset_deadline()

    def _require_host(self, player_id: str) -> None:
        if player_id != self.host_id:
            raise InvalidIntent("Chỉ chủ phòng làm được việc này")

    def _reset_deadline(self) -> None:
        if self.machine is None or self.is_over():
            self.deadline = None
            return
        phase = self.machine.phase
        key = phase if phase in self.timers else "night"
        if phase in ("night_result", "day_result"):
            self.deadline = time.time() + 5
        else:
            self.deadline = time.time() + self.timers[key]

    def is_over(self) -> bool:
        return self.machine is not None and self.machine.phase == "game_over"

    def views(self) -> dict[str, dict]:
        if self.machine is None:
            return {}
        return {
            pid: state_view(self.machine, pid, self.deadline) for pid in self.players
        }

    def lobby_view(self) -> dict:
        return {
            "type": "lobby",
            "room": self.code,
            "host": self.host_id,
            "players": [
                {"id": pid, "name": name} for pid, name in self.players.items()
            ],
            "disabled_roles": sorted(self.disabled_roles),
        }


class RoomManager:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rooms: dict[str, Room] = {}
        self.rng = rng or random.Random()

    def create(self) -> Room:
        while True:
            code = "".join(self.rng.choices(CODE_ALPHABET, k=4))
            if code not in self.rooms:
                break
        room = Room(code=code, rng=self.rng)
        self.rooms[code] = room
        return room

    def get(self, code: str) -> Room | None:
        return self.rooms.get(code)
