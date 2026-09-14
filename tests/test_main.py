import json

import pytest
from fastapi import WebSocketDisconnect

import main as app_main
from app.room import Room


class ScriptedSocket:
    """WebSocket giả cho test: `receive_json()` trả lần lượt từng mục của
    `script`; nếu mục là một Exception thì raise thay vì trả về."""

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.sent: list[dict] = []
        self.closed = False

    async def accept(self) -> None:
        pass

    async def receive_json(self):
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)

    async def close(self, code: int = 1000) -> None:
        self.closed = True


def make_room(n: int = 6) -> tuple[Room, list[str]]:
    room = app_main.manager.create()
    ids = [room.join(f"Người {i}", token=None)[0] for i in range(n)]
    return room, ids


def forget_room(room: Room) -> None:
    app_main.manager.rooms.pop(room.code, None)
    app_main.connections.pop(room.code, None)


async def test_join_tre_khi_van_da_bat_dau_thi_duoc_ngoi_cho():
    """Vào giữa ván không còn là lỗi — người đến muộn giữ ghế cho ván sau.
    Vẫn giữ yêu cầu gốc của Finding 1: handler không được bật ngoại lệ."""
    room, _ = make_room()
    room.start()
    socket = ScriptedSocket(
        [
            {"type": "join", "room": room.code, "name": "Chậm chân", "token": None},
            WebSocketDisconnect(code=1000),
        ]
    )

    try:
        await app_main.websocket_endpoint(socket)  # không được raise
    finally:
        forget_room(room)

    joined = [m for m in socket.sent if m.get("type") == "joined"]
    assert len(joined) == 1
    assert joined[0]["waiting"] is True
    # Màn hình chờ, tuyệt đối không có state của ván đang chạy.
    assert [m["type"] for m in socket.sent if m["type"] == "waiting"]
    assert not [m for m in socket.sent if m.get("type") == "state"]


async def test_nguoi_ngoi_cho_khong_nhan_thong_tin_cua_van():
    """Kết quả đêm / chuông bình minh là thông tin mật của ván đang chạy."""
    room, ids = make_room()
    room.start()
    late = room.join("Chậm chân", token=None)[0]
    room.pending.add(late)
    sent: list[dict] = []
    room.connections[late] = type(
        "C", (), {"ws": type("S", (), {"send_json": lambda s, m: _collect(sent, m)})(),
                  "player_id": late, "token": ""}
    )()

    try:
        await room.broadcast({"type": "night_result", "deaths": []})
    finally:
        forget_room(room)

    assert sent == []


async def _collect(bucket: list, msg: dict) -> None:
    bucket.append(msg)


async def test_frame_dau_tien_khong_phai_json_nhan_loi():
    """Finding 2: một frame không parse được thành JSON (json.JSONDecodeError,
    một subclass của ValueError) không được thoát khỏi mọi try/except."""
    socket = ScriptedSocket([json.JSONDecodeError("Expecting value", "", 0)])

    await app_main.websocket_endpoint(socket)  # không được raise

    assert socket.closed
    assert len(socket.sent) == 1
    assert socket.sent[0]["type"] == "error"


async def test_frame_dau_tien_la_json_hop_le_nhung_khong_phai_object():
    """Finding 2: JSON hợp lệ nhưng không phải dict (ví dụ một mảng) trước
    kia làm `raw.get("type", "")` ném AttributeError không bị bắt."""
    socket = ScriptedSocket([[1, 2, 3]])

    await app_main.websocket_endpoint(socket)  # không được raise

    assert socket.closed
    assert len(socket.sent) == 1
    assert socket.sent[0]["type"] == "error"


async def test_frame_hong_giua_van_chi_mat_dung_mot_thong_bao_loi():
    """Finding 2: sau khi join thành công, một frame hỏng giữa chừng chỉ
    tốn người gửi một thông báo lỗi — không giết cả kết nối/ghế ngồi."""
    room, _ = make_room()
    socket = ScriptedSocket(
        [
            {"type": "join", "room": room.code, "name": "Ổn định", "token": None},
            json.JSONDecodeError("Expecting value", "", 0),
            WebSocketDisconnect(code=1000),
        ]
    )

    try:
        await app_main.websocket_endpoint(socket)
    finally:
        forget_room(room)

    joined = [m for m in socket.sent if m.get("type") == "joined"]
    errors = [m for m in socket.sent if m.get("type") == "error"]
    assert len(joined) == 1
    assert len(errors) == 1
