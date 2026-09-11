from __future__ import annotations

import asyncio
import os
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from app.game.intents import InvalidIntent
from app.game.winner import WINNER_LABEL
from app.protocol import parse_client_msg
from app.room import Room, RoomManager

app = FastAPI(title="Ma Sói")
manager = RoomManager()
connections: dict[str, dict[str, WebSocket]] = {}


async def broadcast(room: Room) -> None:
    sockets = connections.get(room.code, {})
    if room.machine is None:
        for socket in list(sockets.values()):
            await _safe_send(socket, room.lobby_view())
        return

    for player_id, view in room.views().items():
        socket = sockets.get(player_id)
        if socket is not None:
            await _safe_send(socket, view)

    # Ruling R5: mỗi reveal chỉ gửi một lần — xoá sau khi đã phát,
    # nếu không Tiên Tri sẽ nhận lại cùng một dòng ở mỗi broadcast sau
    # trong cùng pha.
    if room.machine.last_result is not None:
        for reveal in room.machine.last_result.reveals:
            socket = sockets.get(reveal.actor)
            if socket is not None:
                await _safe_send(socket, {"type": "private", "text": reveal.text})
        room.machine.last_result.reveals = []

    if room.is_over():
        payload = {
            "type": "game_over",
            "winner": room.machine.winner,
            "label": WINNER_LABEL[room.machine.winner],
            "roles": {
                p.id: p.role_id for p in room.machine.state.players.values()
            },
            "full_log": room.machine.state.log,
        }
        for socket in list(sockets.values()):
            await _safe_send(socket, payload)


async def _safe_send(socket: WebSocket, payload: dict) -> None:
    try:
        await socket.send_json(payload)
    except (WebSocketDisconnect, RuntimeError):
        pass


async def phase_clock(room: Room) -> None:
    """Một task duy nhất cho mỗi phòng: hết giờ thì tự chuyển pha."""
    while not room.is_over():
        await asyncio.sleep(0.5)
        if room.deadline is not None and time.time() >= room.deadline:
            room.advance()
            await broadcast(room)


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    room: Room | None = None
    player_id: str | None = None

    try:
        first = parse_client_msg(await socket.receive_json())
        if first.type != "join":
            await socket.send_json({"type": "error", "message": "Phải join trước"})
            return

        room = manager.get(first.room or "") or manager.create()
        player_id, token = room.join(first.name, first.token)
        connections.setdefault(room.code, {})[player_id] = socket
        await socket.send_json(
            {
                "type": "joined",
                "you": {"id": player_id, "name": first.name},
                "token": token,
                "room": room.code,
                "is_host": player_id == room.host_id,
            }
        )
        await broadcast(room)

        while True:
            raw = await socket.receive_json()
            try:
                was_lobby = room.machine is None
                room.handle(player_id, raw)
                if was_lobby and room.machine is not None:
                    asyncio.create_task(phase_clock(room))
            except (InvalidIntent, ValueError) as exc:
                await socket.send_json({"type": "error", "message": str(exc)})
                continue
            await broadcast(room)

    except WebSocketDisconnect:
        if room and player_id:
            connections.get(room.code, {}).pop(player_id, None)


# static/ được .gitignore và trống tại HEAD — Task 16-17 mới đổ frontend vào.
# Tạo thư mục nếu chưa có để StaticFiles không crash khi khởi động.
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
