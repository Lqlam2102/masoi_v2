import asyncio
import random

import pytest

import main as app_main
from app.game.effects import Reveal
from app.game.intents import InvalidIntent
from app.game.pipeline import NightResult
from app.room import DEFAULT_TIMERS, Room, RoomManager


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


def filled_room(n: int = 6) -> tuple[Room, list[str]]:
    room = Room(code="TEST", rng=random.Random(3))
    ids = [room.join(f"Người {i}", token=None)[0] for i in range(n)]
    return room, ids


def test_nguoi_dau_tien_lam_host():
    room, ids = filled_room()

    assert room.host_id == ids[0]


def test_reconnect_bang_token_giu_nguyen_ghe():
    room = Room(code="TEST", rng=random.Random(3))
    pid, token = room.join("Lâm", token=None)

    again_id, again_token = room.join("Lâm", token=token)

    assert again_id == pid
    assert again_token == token
    assert len(room.players) == 1


def test_start_chia_vai_va_mo_pha_dem():
    room, _ = filled_room()
    room.start()

    assert room.machine is not None
    assert room.machine.phase.startswith("night_")
    assert all(p.role_id for p in room.machine.state.players.values())


def test_khong_du_nguoi_thi_khong_start_duoc():
    room, _ = filled_room(n=3)

    with pytest.raises(ValueError):
        room.start()


def test_views_moi_nguoi_mot_ban():
    room, ids = filled_room()
    room.start()

    views = room.views()

    assert set(views) == set(ids)
    assert views[ids[0]]["you"]["id"] == ids[0]


def test_hanh_dong_sai_pha_bao_loi():
    room, ids = filled_room()
    room.start()
    outsider = next(
        pid for pid in ids if pid not in room.machine.current_actors()
    )

    with pytest.raises(InvalidIntent):
        room.handle(outsider, {"type": "action", "targets": [ids[0]]})


def test_room_manager_sinh_ma_khac_nhau():
    manager = RoomManager()
    a, b = manager.create(), manager.create()

    assert a.code != b.code
    assert manager.get(a.code) is a
    assert manager.get("KHONGCO") is None


def test_default_timers_co_du_cac_pha():
    for key in ("night", "day_discuss", "day_vote", "hunter_shot"):
        assert key in DEFAULT_TIMERS


def test_reveal_chi_gui_dung_mot_lan():
    """Ruling R5: private reveal là thông báo một lần — broadcast lần sau
    không được gửi lại cùng một reveal."""
    room, ids = filled_room()
    room.start()
    seer, target = ids[0], ids[1]
    room.machine.last_result = NightResult(
        reveals=[Reveal(actor=seer, target=target, text="Bạn thấy phe Sói")]
    )

    sockets = {pid: FakeSocket() for pid in ids}
    app_main.connections[room.code] = sockets
    try:
        asyncio.run(app_main.broadcast(room))
        asyncio.run(app_main.broadcast(room))
    finally:
        app_main.connections.pop(room.code, None)

    private_msgs = [m for m in sockets[seer].sent if m.get("type") == "private"]
    assert len(private_msgs) == 1
    assert room.machine.last_result.reveals == []
