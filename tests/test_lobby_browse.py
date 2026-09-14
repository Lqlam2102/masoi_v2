"""Gợi ý phòng ở sảnh, ngồi chờ ván đang chạy, và mở ván mới cùng phòng."""

import asyncio
import random

from app.room import Room
from app.game.setup import MAX_PLAYERS


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


def conn_for(pid: str, sock: FakeSocket):
    return type("C", (), {"ws": sock, "player_id": pid, "token": ""})()


def wired_room(n: int = 6) -> tuple[Room, list[str], dict[str, FakeSocket]]:
    room = Room(code="TEST", rng=random.Random(3))
    ids = [room.join(f"Người {i}", token=None)[0] for i in range(n)]
    socks = {pid: FakeSocket() for pid in ids}
    for pid, sock in socks.items():
        room.connections[pid] = conn_for(pid, sock)
    return room, ids, socks


def seat_late(room: Room, name: str = "Chậm chân") -> tuple[str, FakeSocket]:
    """Người vào khi ván đang chạy — join() của test không tự xếp vào pending."""
    pid = room.join(name, token=None)[0]
    sock = FakeSocket()
    room.connections[pid] = conn_for(pid, sock)
    if room.machine is not None:
        room.pending.add(pid)
    return pid, sock


def types(sock: FakeSocket) -> list[str]:
    return [m["type"] for m in sock.sent]


# ── Tóm tắt phòng cho sảnh ──

def test_phong_o_lobby_bao_dang_cho():
    room, ids, _ = wired_room(3)

    s = room.summary()

    assert s["code"] == "TEST"
    assert s["status"] == "lobby"
    assert s["players"] == 3
    assert s["waiting"] == 0
    assert s["online"] == 3
    assert s["host"] == room.names[ids[0]]
    assert s["max"] == MAX_PLAYERS


def test_phong_dang_choi_bao_dang_choi_va_so_nguoi_cho():
    room, _, _ = wired_room()
    room.start()
    seat_late(room)

    s = room.summary()

    assert s["status"] == "playing"
    assert s["players"] == 6      # người chờ không tính là đang chơi
    assert s["waiting"] == 1
    assert s["night"] == 1


def test_van_da_ket_thuc_thi_khong_con_tinh_la_dang_choi():
    room, _, _ = wired_room()
    room.start()
    room.machine._set_phase("game_over")

    assert room.in_game is False
    assert room.summary()["status"] == "lobby"


# ── Vào giữa ván thì ngồi chờ ──

def test_vao_giua_van_thi_vao_hang_cho_chu_khong_bi_tu_choi():
    room, _, _ = wired_room()
    room.start()

    late, _ = seat_late(room)

    assert late in room.pending
    assert late not in room.machine.state.players
    assert late in room.names


def test_nguoi_cho_nhan_man_hinh_cho_thay_vi_state():
    room, ids, socks = wired_room()
    room.start()
    late, late_sock = seat_late(room)

    asyncio.run(room.broadcast_state())
    room._cancel_timer()

    assert types(late_sock) == ["waiting"]
    assert late_sock.sent[0]["playing"] == 6
    assert "Chậm chân" in late_sock.sent[0]["waiters"]
    assert types(socks[ids[0]]) == ["state"]


def test_ket_qua_dem_khong_lot_sang_nguoi_dang_cho():
    room, ids, socks = wired_room()
    room.start()
    late, late_sock = seat_late(room)

    asyncio.run(room.broadcast({"type": "night_result", "deaths": []}))

    assert late_sock.sent == []
    assert types(socks[ids[0]]) == ["night_result"]


def test_ket_thuc_van_thi_nguoi_cho_duoc_bao():
    room, _, _ = wired_room()
    room.start()
    late, late_sock = seat_late(room)

    asyncio.run(room.broadcast({"type": "game_over"}, include_pending=True))

    assert types(late_sock) == ["game_over"]


def test_nguoi_dang_cho_roi_phong_thi_xoa_han():
    room, _, _ = wired_room()
    room.start()
    late, _ = seat_late(room)

    room.leave_room(late)

    assert late not in room.names
    assert late not in room.pending


def test_nguoi_trong_van_roi_phong_van_giu_ghe():
    room, ids, _ = wired_room()
    room.start()

    room.leave_room(ids[1])

    assert ids[1] in room.names           # còn ghế để vào lại bằng token
    assert room.connections[ids[1]] is None


def test_phong_day_thi_khong_cho_vao_nua():
    room, _, _ = wired_room(MAX_PLAYERS)
    room.start()

    try:
        room.join_or_reconnect(None, "Thừa", None)
        assert False, "phải báo phòng đầy"
    except ValueError as e:
        assert "đầy" in str(e)


# ── Ván mới trong cùng phòng ──

def test_van_moi_xep_ghe_cho_nguoi_dang_cho():
    room, ids, _ = wired_room()
    room.start()
    late, _ = seat_late(room)
    room.machine._set_phase("game_over")

    asyncio.run(room.handle_rematch(ids[0]))

    assert room.machine is None
    assert room.pending == set()
    assert late in room.seated_ids()
    assert len(room.seated_ids()) == 7


def test_van_moi_nhuong_cho_nguoi_da_mat_ket_noi():
    room, ids, _ = wired_room()
    room.start()
    room.machine._set_phase("game_over")
    room.disconnect(ids[3])

    asyncio.run(room.handle_rematch(ids[0]))

    assert ids[3] not in room.names
    assert len(room.seated_ids()) == 5


def test_van_moi_xoa_chat_cua_van_truoc():
    room, ids, _ = wired_room()
    room.start()
    room.chat_log.append({"channel": "wolf", "text": "bí mật"})
    room.machine._set_phase("game_over")

    asyncio.run(room.handle_rematch(ids[0]))

    assert room.chat_log == []


def test_chi_host_moi_mo_duoc_van_moi():
    room, ids, socks = wired_room()
    room.start()
    room.machine._set_phase("game_over")

    asyncio.run(room.handle_rematch(ids[2]))

    assert room.machine is not None
    assert types(socks[ids[2]]) == ["error"]


def test_khong_mo_van_moi_khi_van_dang_chay():
    room, ids, socks = wired_room()
    room.start()

    asyncio.run(room.handle_rematch(ids[0]))

    assert room.machine is not None
    assert types(socks[ids[0]]) == ["error"]
