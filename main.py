import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.protocol import parse_client_msg
from app.room import RoomManager, all_rooms, cleanup_empty_rooms, get_or_create_room, get_room
from app.views import state_view

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Ma Sói Online")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Module-level globals expected by tests
manager = RoomManager()
connections: dict[str, dict] = {}   # {room_code: {player_id: WebSocket}}


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/rooms")
async def list_rooms():
    """Phòng đang mở, để sảnh chờ gợi ý cho người mới thay vì bắt gõ mã."""
    cleanup_empty_rooms()
    rooms = [r for r in all_rooms() if r.online_count > 0]
    # Phòng còn chờ người xếp trước, rồi tới phòng đông nhất.
    rooms.sort(key=lambda r: (r.in_game, -r.online_count))
    return {"rooms": [r.summary() for r in rooms]}


async def broadcast(room) -> None:
    """Broadcast state to all connected sockets. Used by tests."""
    if room.machine is None:
        return
    sockets = connections.get(room.code, {})
    if not sockets:
        return

    # Send private reveals once then clear them
    if room.machine.last_result:
        for reveal in room.machine.last_result.reveals:
            sock = sockets.get(reveal.actor)
            if sock:
                try:
                    await sock.send_json({"type": "private", "text": reveal.text})
                except Exception:
                    pass
        room.machine.last_result.reveals = []

    for pid, sock in sockets.items():
        view = state_view(room.machine, pid, None)
        try:
            await sock.send_json(view)
        except Exception:
            pass


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    player_id: str | None = None
    room = None

    try:
        # ── Bước 1: nhận message join ──
        try:
            raw = await ws.receive_json()
        except Exception as e:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()
            return

        # raw phải là dict
        if not isinstance(raw, dict):
            await ws.send_json({"type": "error", "message": "Frame phải là JSON object"})
            await ws.close()
            return

        try:
            msg = parse_client_msg(raw)
        except ValueError as e:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()
            return

        if msg.type != "join":
            await ws.send_json({
                "type": "error",
                "message": "Tin nhắn đầu tiên phải là join",
            })
            await ws.close()
            return

        # ── Tìm / tạo phòng ──
        room_code = msg.room.strip().upper() if msg.room else None

        if msg.token:
            room = next(
                (r for r in all_rooms() if msg.token in r.token_index), None
            )
            # Also search module-level manager rooms
            if room is None:
                for r in manager._rooms.values():
                    if msg.token in r.token_index:
                        room = r
                        break
            if room is None:
                await ws.send_json({
                    "type": "error",
                    "message": "Token không hợp lệ hoặc phòng đã đóng",
                })
                await ws.close()
                return
        elif room_code:
            room = get_room(room_code)
            if room is None:
                room = manager.get(room_code)
            if room is None:
                await ws.send_json({
                    "type": "error",
                    "message": f"Phòng {room_code} không tồn tại",
                })
                await ws.close()
                return
        else:
            room, _ = get_or_create_room(None)

        try:
            player_id, token, is_host = room.join_or_reconnect(
                ws, msg.name, msg.token
            )
        except ValueError as e:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()
            return

        # ── Xác nhận join ──
        await ws.send_json({
            "type": "joined",
            "you": {"id": player_id, "name": room.names.get(player_id, "")},
            "token": token,
            "room": room.code,
            "is_host": is_host,
            "waiting": player_id in room.pending,
        })

        # ── Gửi state hiện tại ──
        if player_id in room.pending:
            # Vào giữa ván: chỉ thấy màn hình chờ, tuyệt đối không thấy state.
            # broadcast_waiting cập nhật luôn cho những người đã chờ sẵn.
            await room.broadcast_waiting()
        elif room.machine is not None:
            view = state_view(
                room.machine, player_id, room._deadline,
                room.phase_duration(room.machine.phase),
            )
            view["is_host"] = player_id == room.host_id
            await ws.send_json(view)
            # Vào lại giữa ván vẫn đọc được những gì đồng đội đã nói.
            history = room.chat_history_for(player_id)
            if history:
                await ws.send_json({"type": "chat_history", "messages": history})
        else:
            await _broadcast_lobby(room)

        # ── Vòng lắng nghe ──
        while True:
            try:
                raw = await ws.receive_json()
            except WebSocketDisconnect:
                raise
            except Exception as e:
                await ws.send_json({"type": "error", "message": str(e)})
                continue

            if not isinstance(raw, dict):
                await ws.send_json({"type": "error", "message": "Frame phải là JSON object"})
                continue

            try:
                msg = parse_client_msg(raw)
            except ValueError as e:
                await ws.send_json({"type": "error", "message": str(e)})
                continue

            if msg.type == "config":
                await room.handle_config(player_id, msg)
            elif msg.type == "start":
                await room.handle_start(player_id)
            elif msg.type == "action":
                await room.handle_action(player_id, msg)
            elif msg.type == "vote":
                await room.handle_vote(player_id, msg)
            elif msg.type == "skip":
                await room.handle_pass(player_id)
            elif msg.type == "chat":
                await room.handle_chat(player_id, msg)
            elif msg.type == "advance":
                await room.handle_advance(player_id)
            elif msg.type == "rematch":
                await room.handle_rematch(player_id)
                if room.machine is None:
                    await _broadcast_lobby(room)
            elif msg.type == "leave":
                # Acknowledge first, then break — finally block cleans up
                await ws.send_json({"type": "left", "message": "Bạn đã rời phòng"})
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if room and player_id:
            room.leave_room(player_id)
            if not room.empty:
                # Ván đang chạy thì người trong ván không cần tin lobby —
                # chỉ cập nhật danh sách cho những người đang ngồi chờ.
                if room.machine is None:
                    await _broadcast_lobby(room)
                elif room.pending:
                    await room.broadcast_waiting()
        cleanup_empty_rooms()


async def _broadcast_lobby(room) -> None:
    await room.broadcast({
        "type": "lobby",
        "room": room.code,
        "players": [
            {
                "id": pid,
                "name": name,
                "online": room.connections.get(pid) is not None,
            }
            for pid, name in room.names.items()
        ],
        "host": room.host_id,
    })
