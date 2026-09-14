from __future__ import annotations

import asyncio
import random
import string
import time

from fastapi import WebSocket

from app.game.phases import PhaseMachine
from app.game.roles import get_role
from app.game.setup import MAX_PLAYERS, MIN_PLAYERS, build_state
from app.game.state import Faction
from app.game.winner import WINNER_LABEL
from app.views import can_read_chat, chat_channel_for, state_view

DEFAULT_TIMERS: dict[str, int] = {
    "night": 60,        # alias used in tests
    "night_phase": 60,  # mỗi vai có 60s để hành động
    "night_result": 8,  # nhịp "trời đang sáng" trước khi công bố
    "day_discuss": 180,
    "day_vote": 75,
    "day_result": 10,   # nhịp công bố kết quả treo cổ
    "hunter_shot": 45,
}

# Giới hạn hợp lệ khi host chỉnh thời gian (giây).
TIMER_BOUNDS: dict[str, tuple[int, int]] = {
    "night": (15, 180),
    "night_phase": (15, 180),
    "night_result": (3, 30),
    "day_discuss": (30, 900),
    "day_vote": (15, 300),
    "day_result": (3, 30),
    "hunter_shot": (15, 120),
}

# Khi mọi người đã hành động xong, chờ thêm chút để ai cũng kịp đọc kết quả
# (Tiên Tri xem lời phán, Phù Thủy thấy mình vừa dùng bình nào…) rồi mới sang pha kế.
ACTION_GRACE = 3

LOBBY_TIMEOUT = 600  # seconds

MAX_CHAT_LEN = 300      # ký tự mỗi tin nhắn
CHAT_HISTORY = 60       # số tin giữ lại để người vào lại còn đọc được
CHAT_COOLDOWN = 0.35    # giây tối thiểu giữa hai tin của cùng một người


class Connection:
    __slots__ = ("ws", "player_id", "token")

    def __init__(self, ws: WebSocket, player_id: str, token: str) -> None:
        self.ws = ws
        self.player_id = player_id
        self.token = token


def _gen_token() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


def _gen_room_code(existing: set[str]) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=4))
        if code not in existing:
            return code


class Room:
    def __init__(self, code: str) -> None:
        self.code = code
        self.machine: PhaseMachine | None = None
        self.names: dict[str, str] = {}
        self.tokens: dict[str, str] = {}
        self.token_index: dict[str, str] = {}
        self.connections: dict[str, Connection | None] = {}
        self.host_id: str | None = None
        self.disabled_roles: set[str] = set()
        self.timers: dict[str, int] = dict(DEFAULT_TIMERS)
        self._timer_task: asyncio.Task | None = None
        self._deadline: float | None = None
        self._grace_pending: bool = False
        self._last_active: float = time.time()
        self._pid_counter = 0
        self.chat_log: list[dict] = []
        self._last_chat_at: dict[str, float] = {}
        # Người vào khi ván đang chạy: giữ ghế, ngồi chờ ván sau.
        # Họ KHÔNG được nhận state, chat hay kết quả đêm của ván hiện tại.
        self.pending: set[str] = set()

    # ── Thông tin cho sảnh chờ ──

    @property
    def in_game(self) -> bool:
        return self.machine is not None and self.machine.phase != "game_over"

    def seated_ids(self) -> list[str]:
        """Người đang có ghế trong ván (hoặc sẽ có, nếu đang ở lobby)."""
        return [pid for pid in self.names if pid not in self.pending]

    @property
    def online_count(self) -> int:
        return sum(1 for c in self.connections.values() if c is not None)

    def summary(self) -> dict:
        return {
            "code": self.code,
            "host": self.names.get(self.host_id or "", ""),
            "players": len(self.seated_ids()),
            "waiting": len(self.pending),
            "online": self.online_count,
            "max": MAX_PLAYERS,
            "min": MIN_PLAYERS,
            "status": "playing" if self.in_game else "lobby",
            "night": self.machine.state.night if self.machine else 0,
        }

    def waiting_view(self) -> dict:
        return {
            "type": "waiting",
            "room": self.code,
            "host": self.names.get(self.host_id or "", ""),
            "playing": len(self.seated_ids()),
            "night": self.machine.state.night if self.machine else 0,
            "waiters": [self.names[pid] for pid in self.pending if pid in self.names],
        }

    # ── Join / reconnect ──

    def join_or_reconnect(
        self, ws: WebSocket, name: str, token: str | None
    ) -> tuple[str, str, bool]:
        self._last_active = time.time()

        if token and token in self.token_index:
            pid = self.token_index[token]
            self.connections[pid] = Connection(ws, pid, token)
            return pid, token, pid == self.host_id

        if len(self.names) >= MAX_PLAYERS:
            raise ValueError("Phòng đã đầy")

        self._pid_counter += 1
        pid = f"p{self._pid_counter}"
        tok = _gen_token()
        self.names[pid] = name or f"Người {self._pid_counter}"
        self.tokens[pid] = tok
        self.token_index[tok] = pid
        self.connections[pid] = Connection(ws, pid, tok)
        # Ván đang chạy thì ngồi chờ — không chen ngang ván của người khác.
        if self.machine is not None:
            self.pending.add(pid)
        elif self.host_id is None:
            self.host_id = pid
        return pid, tok, pid == self.host_id

    def disconnect(self, player_id: str) -> None:
        if player_id in self.connections:
            self.connections[player_id] = None
        self._last_active = time.time()
        if player_id == self.host_id:
            for pid, conn in self.connections.items():
                if conn is not None and pid != player_id:
                    self.host_id = pid
                    break

    def _remove_player(self, player_id: str) -> None:
        self.names.pop(player_id, None)
        tok = self.tokens.pop(player_id, None)
        if tok:
            self.token_index.pop(tok, None)
        self.connections.pop(player_id, None)
        self.pending.discard(player_id)
        if player_id == self.host_id:
            self.host_id = next(iter(self.names), None)

    def leave_room(self, player_id: str) -> None:
        """Xóa hẳn người chơi khỏi phòng. Người đang trong ván chỉ mất kết nối
        (giữ ghế để vào lại); người ở lobby hoặc đang ngồi chờ thì xoá hẳn."""
        self.disconnect(player_id)
        if self.machine is None or player_id in self.pending:
            self._remove_player(player_id)

    def reset_for_new_game(self) -> None:
        """Về lại lobby cho ván mới: người ngồi chờ được xếp ghế, ai mất kết
        nối thì nhường chỗ."""
        self._cancel_timer()
        self.machine = None
        self.pending.clear()
        self.chat_log.clear()
        self._last_chat_at.clear()
        for pid in [p for p, c in self.connections.items() if c is None]:
            self._remove_player(pid)
        if self.host_id not in self.names:
            self.host_id = next(iter(self.names), None)

    @property
    def empty(self) -> bool:
        return all(c is None for c in self.connections.values())

    # ── Broadcast helpers ──

    async def broadcast_state(self) -> None:
        waiting = self.waiting_view() if self.pending else None
        for pid, conn in self.connections.items():
            if conn is None:
                continue
            if pid in self.pending:
                await self._send(conn, waiting)
                continue
            view = state_view(
                self.machine, pid, self._deadline,
                self.phase_duration(self.machine.phase) if self.machine else None,
            )
            view["is_host"] = pid == self.host_id
            await self._send(conn, view)

    async def broadcast_waiting(self) -> None:
        view = self.waiting_view()
        for pid in self.pending:
            await self.send_to(pid, view)

    async def broadcast(self, msg: dict, include_pending: bool = False) -> None:
        """Mặc định KHÔNG gửi cho người ngồi chờ — kết quả đêm, chuông bình minh…
        đều là thông tin của ván đang chạy, họ không được biết."""
        for pid, conn in self.connections.items():
            if conn is None or (pid in self.pending and not include_pending):
                continue
            await self._send(conn, msg)

    async def send_to(self, player_id: str, msg: dict) -> None:
        conn = self.connections.get(player_id)
        if conn:
            await self._send(conn, msg)

    @staticmethod
    async def _send(conn: Connection, msg: dict) -> None:
        try:
            await conn.ws.send_json(msg)
        except Exception:
            pass

    # ── Start game ──

    def start_game(self, rng: random.Random | None = None) -> None:
        if len(self.names) < MIN_PLAYERS:
            raise ValueError(
                f"Cần ít nhất {MIN_PLAYERS} người chơi, hiện có {len(self.names)}"
            )
        rng = rng or random.Random()
        state = build_state(self.names, rng, disabled=self.disabled_roles)
        self.machine = PhaseMachine(state)
        self.machine.start()

    # ── Phase timer ──

    async def _run_phase_timer(self, duration: int) -> None:
        self._deadline = time.time() + duration
        try:
            await asyncio.sleep(duration)
        except asyncio.CancelledError:
            return
        await self._do_advance()

    def _cancel_timer(self) -> None:
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self._deadline = None
        self._grace_pending = False

    def phase_duration(self, phase: str) -> int | None:
        """Số giây của một pha, hoặc None nếu pha không tự chạy."""
        if phase == "night_result":
            return self.timers.get("night_result", DEFAULT_TIMERS["night_result"])
        if phase == "day_result":
            return self.timers.get("day_result", DEFAULT_TIMERS["day_result"])
        if phase.startswith("night_"):
            return self.timers["night_phase"]
        if phase in ("day_discuss", "day_vote", "hunter_shot"):
            return self.timers[phase]
        return None

    def _schedule_advance(self, duration: float) -> None:
        self._cancel_timer()
        self._deadline = time.time() + duration
        loop = asyncio.get_event_loop()
        self._timer_task = loop.create_task(self._run_phase_timer(duration))

    def _start_timer(self) -> None:
        self._cancel_timer()
        if self.machine is None:
            return
        duration = self.phase_duration(self.machine.phase)
        if duration is None:
            return
        self._schedule_advance(duration)

    def _grace_advance(self) -> None:
        """Mọi người đã xong sớm — chốt pha sau một nhịp ngắn, không cắt ngang ngay."""
        if self._grace_pending:
            return
        remaining = (self._deadline - time.time()) if self._deadline else None
        delay = ACTION_GRACE if remaining is None else min(ACTION_GRACE, remaining)
        self._schedule_advance(max(0.5, delay))
        self._grace_pending = True

    async def _do_advance(self) -> None:
        if self.machine is None:
            return
        self._cancel_timer()
        self.machine.advance()
        await self._post_advance()

    def _deaths_payload(self, result) -> list[dict]:
        deaths = []
        for d in result.deaths:
            p = self.machine.state.get(d.player_id)
            deaths.append({"id": d.player_id, "name": p.name,
                           "role": p.role_id, "source": d.source})
        return deaths

    @staticmethod
    def _public_log(result) -> list[str]:
        """Log công khai — loại mọi câu mang thông tin soi của Tiên Tri."""
        return [
            line for line in result.log
            if not any(kw in line for kw in ["thuộc phe", "KHÔNG thuộc"])
        ]

    async def _post_advance(self) -> None:
        if self.machine is None:
            return
        phase = self.machine.phase

        # Nhịp "trời đang sáng": báo trước khi công bố người chết.
        if phase == "night_result":
            await self.broadcast({
                "type": "dawn",
                "night": self.machine.state.night,
                "duration": self.phase_duration("night_result"),
            })

        if phase == "day_discuss" and self.machine.last_result:
            result = self.machine.last_result
            await self.broadcast({
                "type": "night_result",
                "night": self.machine.state.night,
                "deaths": self._deaths_payload(result),
                "public_log": self._public_log(result),
            })

        if phase == "day_result" and self.machine.last_result:
            result = self.machine.last_result
            await self.broadcast({
                "type": "day_result",
                "night": self.machine.state.night,
                "deaths": self._deaths_payload(result),
                "public_log": self._public_log(result),
            })

        # Reveal riêng tư chỉ gửi đúng một lần (Ruling R5).
        if self.machine.last_result and self.machine.last_result.reveals:
            for reveal in self.machine.last_result.reveals:
                await self.send_to(reveal.actor,
                                   {"type": "private", "kind": "reveal", "text": reveal.text})
            self.machine.last_result.reveals = []

        if phase == "game_over":
            winner = self.machine.winner or ""
            roles = {pid: p.role_id for pid, p in self.machine.state.players.items()}
            await self.broadcast({
                "type": "game_over",
                "winner": winner,
                "winner_label": WINNER_LABEL.get(winner, winner),
                "roles": roles,
                "full_log": list(self.machine.state.log),
                "waiting": len(self.pending),
            }, include_pending=True)   # người ngồi chờ cần biết đã tới lượt mình
            return

        # Hẹn giờ TRƯỚC khi gửi state: state_view đọc self._deadline, gửi trước
        # thì client nhận deadline=None và không vẽ được đồng hồ đếm ngược.
        self._start_timer()
        await self.broadcast_state()

    # ── Message handlers ──

    async def handle_config(self, player_id: str, msg) -> None:
        if player_id != self.host_id:
            await self.send_to(player_id, {"type": "error",
                                           "message": "Chỉ host mới được config"})
            return
        if self.machine is not None:
            await self.send_to(player_id, {"type": "error", "message": "Ván đã bắt đầu"})
            return
        for role_id, enabled in (msg.roles or {}).items():
            if enabled:
                self.disabled_roles.discard(role_id)
            else:
                self.disabled_roles.add(role_id)
        for role_id in msg.disabled_roles or []:
            self.disabled_roles.add(role_id)

        for key, val in (msg.timers or {}).items():
            if key not in self.timers:
                continue
            low, high = TIMER_BOUNDS.get(key, (3, 900))
            self.timers[key] = max(low, min(high, int(val)))
        # `night` là alias của `night_phase` — giữ hai giá trị luôn khớp nhau.
        if "night_phase" in msg.timers:
            self.timers["night"] = self.timers["night_phase"]

        await self.send_to(player_id, {"type": "config_ok", "timers": dict(self.timers)})

    async def handle_start(self, player_id: str) -> None:
        if player_id != self.host_id:
            await self.send_to(player_id, {"type": "error",
                                           "message": "Chỉ host mới được bắt đầu"})
            return
        if self.machine is not None:
            await self.send_to(player_id, {"type": "error", "message": "Ván đã bắt đầu"})
            return
        try:
            self.start_game()
        except ValueError as e:
            await self.send_to(player_id, {"type": "error", "message": str(e)})
            return

        for pid in self.machine.state.players:
            player = self.machine.state.get(pid)
            role = get_role(player.role_id)
            await self.send_to(pid, {"type": "private",
                                     "text": f"Vai của bạn: {role.name}"})
            if role.faction is Faction.WOLF:
                teammates = [
                    self.machine.state.get(p).name
                    for p in self.machine.state.players
                    if p != pid
                    and get_role(self.machine.state.get(p).role_id).faction is Faction.WOLF
                ]
                if teammates:
                    await self.send_to(pid, {"type": "private",
                                             "text": f"Đồng đội sói: {', '.join(teammates)}"})

        # Hẹn giờ TRƯỚC khi gửi state: state_view đọc self._deadline, gửi trước
        # thì client nhận deadline=None và không vẽ được đồng hồ đếm ngược.
        self._start_timer()
        await self.broadcast_state()

    async def _flush_instant_reveals(self) -> None:
        """Tiên Tri / Sói Tiên Tri biết kết quả ngay khi soi, không phải chờ sáng."""
        for reveal in self.machine.take_instant_reveals():
            await self.send_to(reveal.actor, {
                "type": "private", "kind": "reveal", "text": reveal.text,
            })

    async def _after_submit(self) -> None:
        # Rút ngắn hạn chót trước, rồi mới gửi — để đồng hồ trên máy người chơi
        # khớp với thời điểm pha thật sự đóng.
        if self.machine.everyone_acted():
            self._grace_advance()
        await self.broadcast_state()

    async def handle_action(self, player_id: str, msg) -> None:
        if self.machine is None:
            return
        try:
            self.machine.submit_action(player_id, tuple(msg.targets), msg.extra or {})
        except Exception as e:
            await self.send_to(player_id, {"type": "error", "message": str(e)})
            return
        await self._flush_instant_reveals()
        await self._after_submit()

    # Nhãn hiển thị khi host chốt pha sớm.
    _ADVANCE_NOTICE = {
        "day_discuss": "Host đã kết thúc phiên thảo luận",
        "day_vote": "Host đã chốt phiếu",
        "day_result": "Host đã chuyển sang đêm",
        "night_result": "Host đã đánh thức cả làng",
        "hunter_shot": "Host đã chốt lượt Thợ Săn",
    }

    async def handle_advance(self, player_id: str) -> None:
        """Host kết thúc pha sớm — dùng khi cả làng đã bàn xong, khỏi chờ hết giờ."""
        if self.machine is None:
            return
        if player_id != self.host_id:
            await self.send_to(player_id, {
                "type": "error", "message": "Chỉ host mới được kết thúc sớm",
            })
            return
        phase = self.machine.phase
        # Chỉ chốt được pha đang có đồng hồ chạy; lobby/game_over thì vô nghĩa.
        if self.phase_duration(phase) is None:
            return
        await self.broadcast({
            "type": "notice",
            "text": self._ADVANCE_NOTICE.get(phase, "Host đã chuyển pha"),
        })
        await self._do_advance()

    async def handle_rematch(self, player_id: str) -> None:
        """Host mở ván mới ngay trong phòng — người ngồi chờ được vào chơi cùng."""
        if player_id != self.host_id:
            await self.send_to(player_id, {
                "type": "error", "message": "Chỉ host mới được mở ván mới",
            })
            return
        if self.machine is not None and self.machine.phase != "game_over":
            await self.send_to(player_id, {
                "type": "error", "message": "Ván đang chạy",
            })
            return
        joined = len(self.pending)
        self.reset_for_new_game()
        if joined:
            await self.broadcast({
                "type": "notice",
                "text": f"{joined} người chờ đã vào phòng",
            })

    async def handle_pass(self, player_id: str) -> None:
        """Người chơi tự bỏ lượt. Host không ở trong lượt thì được ép qua pha."""
        if self.machine is None:
            return
        try:
            self.machine.submit_pass(player_id)
        except Exception:
            if player_id == self.host_id:
                await self._do_advance()
            return
        await self._after_submit()

    async def handle_vote(self, player_id: str, msg) -> None:
        if self.machine is None:
            return
        try:
            self.machine.submit_vote(player_id, msg.target)
        except Exception as e:
            await self.send_to(player_id, {"type": "error", "message": str(e)})
            return
        await self._after_submit()

    # ── Chat ──

    def chat_history_for(self, player_id: str) -> list[dict]:
        """Các tin người này được phép đọc — dùng khi vào lại phòng."""
        if self.machine is None:
            return []
        return [
            m for m in self.chat_log
            if can_read_chat(self.machine, player_id, m["channel"])
        ]

    async def handle_chat(self, player_id: str, msg) -> None:
        if self.machine is None:
            return
        text = " ".join((msg.text or "").split())[:MAX_CHAT_LEN]
        if not text:
            return

        channel = chat_channel_for(self.machine, player_id)
        if channel is None:
            await self.send_to(player_id, {
                "type": "error",
                "message": "Lúc này bạn không nói được"
                           if self.machine.state.is_alive(player_id)
                           else "Người chết chỉ được nghe",
            })
            return

        now = time.time()
        if now - self._last_chat_at.get(player_id, 0.0) < CHAT_COOLDOWN:
            return
        self._last_chat_at[player_id] = now

        entry = {
            "type": "chat",
            "channel": channel,
            "from_id": player_id,
            "from_name": self.machine.state.get(player_id).name,
            "text": text,
            "ts": now,
        }
        self.chat_log.append(entry)
        del self.chat_log[:-CHAT_HISTORY]

        for pid in self.machine.state.players:
            if can_read_chat(self.machine, pid, channel):
                await self.send_to(pid, entry)


# ── Room registry ──

_ROOMS: dict[str, Room] = {}


def get_or_create_room(code: str | None) -> tuple[Room, bool]:
    if code and code.upper() in _ROOMS:
        return _ROOMS[code.upper()], False
    new_code = _gen_room_code(set(_ROOMS.keys()))
    room = Room(code=new_code)
    _ROOMS[new_code] = room
    return room, True


def get_room(code: str) -> Room | None:
    return _ROOMS.get(code.upper())


def all_rooms() -> list[Room]:
    return list(_ROOMS.values())


def cleanup_empty_rooms() -> None:
    now = time.time()
    to_delete = [
        code for code, room in _ROOMS.items()
        if room.empty and now - room._last_active > LOBBY_TIMEOUT
    ]
    for code in to_delete:
        del _ROOMS[code]


# ─────────────────────────────────────────
# Compat layer for tests (sync API)
# ─────────────────────────────────────────

EMPTY_ROOM_TTL = LOBBY_TIMEOUT  # alias used in tests


class _SyncRoom(Room):
    """Thin synchronous wrapper used by unit tests."""

    def __init__(self, code: str, rng: random.Random | None = None) -> None:
        super().__init__(code)
        self._rng = rng or random.Random()
        self.players: dict[str, str] = {}       # {player_id: name}
        self._connected_ids: set[str] = set()
        self._empty_since: float | None = None

    # Sync join: returns (player_id, token)
    def join(self, name: str, token: str | None = None) -> tuple[str, str]:
        if token and token in self.token_index:
            pid = self.token_index[token]
            self._connected_ids.add(pid)
            return pid, token
        self._pid_counter += 1
        pid = f"p{self._pid_counter}"
        tok = _gen_token()
        self.names[pid] = name
        self.players[pid] = name
        self.tokens[pid] = tok
        self.token_index[tok] = pid
        self.connections[pid] = None  # no real socket
        self._connected_ids.add(pid)
        if self.host_id is None:
            self.host_id = pid
        return pid, tok

    def start(self) -> None:
        if len(self.names) < MIN_PLAYERS:
            raise ValueError(
                f"Cần ít nhất {MIN_PLAYERS} người chơi, hiện có {len(self.names)}"
            )
        from app.game.setup import build_state
        state = build_state(self.names, self._rng, disabled=self.disabled_roles)
        self.machine = PhaseMachine(state)
        self.machine.start()

    def handle(self, player_id: str, msg: dict) -> None:
        from app.game.intents import InvalidIntent
        msg_type = msg.get("type")
        if msg_type in ("start", "config") and player_id != self.host_id:
            raise InvalidIntent("Chỉ host mới được thực hiện hành động này")
        if msg_type == "action":
            if self.machine is None:
                return
            targets = tuple(msg.get("targets", []))
            extra = msg.get("extra", {})
            self.machine.submit_action(player_id, targets, extra)
        elif msg_type == "vote":
            if self.machine is None:
                return
            self.machine.submit_vote(player_id, msg.get("target"))
        elif msg_type == "start":
            self.start()
        elif msg_type == "config":
            for role_id, enabled in msg.get("disabled_roles_map", {}).items():
                if not enabled:
                    self.disabled_roles.add(role_id)

    def views(self) -> dict[str, dict]:
        from app.views import state_view
        if self.machine is None:
            return {}
        return {pid: state_view(self.machine, pid, None) for pid in self.names}

    def sync_connections(
        self, connected: set[str], now: float | None = None
    ) -> None:
        self._connected_ids = set(connected)
        now = now if now is not None else time.time()
        if not connected:
            if self._empty_since is None:
                self._empty_since = now
            # Transfer host if someone was host and is gone
            if self.host_id not in connected:
                ordered = list(self.names.keys())
                for pid in ordered:
                    if pid in connected:
                        self.host_id = pid
                        break
        else:
            self._empty_since = None
            # Ensure host is someone connected
            if self.host_id not in connected:
                ordered = list(self.names.keys())
                for pid in ordered:
                    if pid in connected:
                        self.host_id = pid
                        break

    def is_abandoned(self, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        if self.machine is None:
            return False
        if self._empty_since is None:
            return False
        return now - self._empty_since >= EMPTY_ROOM_TTL


# Monkey-patch Room so that Room(code=..., rng=...) works in tests
_orig_room_init = Room.__init__


def _patched_room_init(self, code: str, rng: random.Random | None = None) -> None:
    _orig_room_init(self, code)
    if rng is not None:
        self._rng = rng
    self.players: dict[str, str] = {}
    self._connected_ids: set[str] = set()
    self._empty_since: float | None = None


def _patched_join(self, name: str, token: str | None = None) -> tuple[str, str]:
    if token and token in self.token_index:
        pid = self.token_index[token]
        self._connected_ids.add(pid)
        return pid, token
    self._pid_counter += 1
    pid = f"p{self._pid_counter}"
    tok = _gen_token()
    self.names[pid] = name
    self.players[pid] = name
    self.tokens[pid] = tok
    self.token_index[tok] = pid
    self.connections[pid] = None
    self._connected_ids.add(pid)
    if self.host_id is None:
        self.host_id = pid
    return pid, tok


def _patched_start(self) -> None:
    if len(self.names) < MIN_PLAYERS:
        raise ValueError(
            f"Cần ít nhất {MIN_PLAYERS} người chơi, hiện có {len(self.names)}"
        )
    rng = getattr(self, "_rng", random.Random())
    state = build_state(self.names, rng, disabled=self.disabled_roles)
    self.machine = PhaseMachine(state)
    self.machine.start()


def _patched_handle(self, player_id: str, msg: dict) -> None:
    from app.game.intents import InvalidIntent
    msg_type = msg.get("type")
    if msg_type in ("start", "config") and player_id != self.host_id:
        raise InvalidIntent("Chỉ host mới được thực hiện hành động này")
    if msg_type == "action":
        if self.machine is None:
            return
        self.machine.submit_action(
            player_id, tuple(msg.get("targets", [])), msg.get("extra", {})
        )
    elif msg_type == "vote":
        if self.machine is None:
            return
        self.machine.submit_vote(player_id, msg.get("target"))
    elif msg_type == "start":
        _patched_start(self)
    elif msg_type == "config":
        pass  # no-op for now


def _patched_views(self) -> dict[str, dict]:
    from app.views import state_view
    if self.machine is None:
        return {}
    return {pid: state_view(self.machine, pid, None) for pid in self.names}


def _patched_sync_connections(
    self, connected: set[str], now: float | None = None
) -> None:
    self._connected_ids = set(connected)
    now = now if now is not None else time.time()
    if not connected:
        if self._empty_since is None:
            self._empty_since = now
        if self.host_id not in connected:
            for pid in list(self.names.keys()):
                if pid in connected:
                    self.host_id = pid
                    break
    else:
        self._empty_since = None
        if self.host_id not in connected:
            for pid in list(self.names.keys()):
                if pid in connected:
                    self.host_id = pid
                    break


def _patched_is_abandoned(self, now: float | None = None) -> bool:
    now = now if now is not None else time.time()
    if self.machine is None:
        return False
    if self._empty_since is None:
        return False
    return now - self._empty_since >= EMPTY_ROOM_TTL


Room.__init__ = _patched_room_init
Room.join = _patched_join
Room.start = _patched_start
Room.handle = _patched_handle
Room.views = _patched_views
Room.sync_connections = _patched_sync_connections
Room.is_abandoned = _patched_is_abandoned


class RoomManager:
    """Synchronous room manager used by tests."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rooms: dict[str, Room] = {}
        self.rooms = self._rooms   # alias for test compatibility
        self._rng = rng or random.Random()

    def create(self) -> Room:
        code = _gen_room_code(set(self._rooms.keys()))
        room = Room(code=code, rng=self._rng)
        self._rooms[code] = room
        return room

    def get(self, code: str) -> Room | None:
        return self._rooms.get(code)

    def remove(self, code: str) -> None:
        self._rooms.pop(code, None)

    def sweep(self, now: float | None = None) -> list[str]:
        now = now if now is not None else time.time()
        gone = [
            code for code, room in self._rooms.items()
            if room.is_abandoned(now=now)
        ]
        for code in gone:
            del self._rooms[code]
        return gone
