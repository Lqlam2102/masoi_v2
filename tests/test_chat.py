"""Chat bầy Sói và bảng phiếu trực tiếp."""

import asyncio
import random

from app.game.phases import PhaseMachine
from app.protocol import parse_client_msg
from app.room import MAX_CHAT_LEN, Room
from app.views import can_read_chat, chat_channel_for, live_votes, state_view
from tests.test_phases import fixed_state


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


def room_with(state) -> tuple[Room, dict[str, FakeSocket]]:
    """Phòng gắn state cố định + socket giả cho từng người chơi."""
    room = Room(code="TEST", rng=random.Random(3))
    room.machine = PhaseMachine(state)
    sockets = {}
    for pid, player in state.players.items():
        sock = FakeSocket()
        sockets[pid] = sock
        room.names[pid] = player.name
        room.connections[pid] = type("C", (), {"ws": sock, "player_id": pid, "token": ""})()
    room.host_id = next(iter(state.players))
    return room, sockets


def chats(sock: FakeSocket) -> list[dict]:
    return [m for m in sock.sent if m.get("type") == "chat"]


def say(room, pid, text):
    asyncio.run(room.handle_chat(pid, parse_client_msg({"type": "chat", "text": text})))


# ── Ai được nói, lúc nào ──

def test_ban_dem_chi_soi_noi_duoc():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()
    machine._set_phase("night_wolf")

    assert chat_channel_for(machine, "an") == "wolf"
    assert chat_channel_for(machine, "lam") is None
    assert chat_channel_for(machine, "binh") is None


def test_soi_noi_duoc_trong_moi_pha_dem():
    """Bầy Sói cần bàn từ đầu đêm, không chỉ đúng lúc tới lượt cắn."""
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()
    machine._set_phase("night_seer")

    assert chat_channel_for(machine, "an") == "wolf"


def test_ban_ngay_ai_con_song_cung_noi_duoc():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine._set_phase("day_discuss")

    assert chat_channel_for(machine, "lam") == "village"
    assert chat_channel_for(machine, "an") == "village"


def test_nguoi_chet_khong_noi_duoc():
    state = fixed_state(lam="seer", an="wolf", binh="villager")
    state.get("lam").alive = False
    machine = PhaseMachine(state)
    machine._set_phase("day_discuss")

    assert chat_channel_for(machine, "lam") is None


def test_kenh_soi_chi_phe_soi_doc_duoc():
    state = fixed_state(lam="seer", an="wolf", binh="villager", tuyet="white_wolf")
    state.get("tuyet").alive = False
    machine = PhaseMachine(state)

    assert can_read_chat(machine, "an", "wolf") is True
    assert can_read_chat(machine, "tuyet", "wolf") is True   # sói chết vẫn nghe
    assert can_read_chat(machine, "lam", "wolf") is False
    assert can_read_chat(machine, "lam", "village") is True


# ── Gửi tin ──

def test_tin_cua_soi_khong_lot_ra_ngoai():
    state = fixed_state(lam="seer", an="wolf", binh="villager", tuyet="wolf")
    room, sockets = room_with(state)
    room.machine._set_phase("night_wolf")

    say(room, "an", "cắn thằng Lâm nhé")

    assert [m["text"] for m in chats(sockets["an"])] == ["cắn thằng Lâm nhé"]
    assert [m["text"] for m in chats(sockets["tuyet"])] == ["cắn thằng Lâm nhé"]
    assert chats(sockets["lam"]) == []
    assert chats(sockets["binh"]) == []


def test_dan_lang_noi_dem_thi_bi_tu_choi():
    state = fixed_state(lam="seer", an="wolf", binh="villager")
    room, sockets = room_with(state)
    room.machine._set_phase("night_wolf")

    say(room, "lam", "tôi soi thấy An là sói")

    assert chats(sockets["an"]) == []
    assert [m["type"] for m in sockets["lam"].sent] == ["error"]


def test_tin_ban_ngay_ca_lang_nghe():
    state = fixed_state(lam="seer", an="wolf", binh="villager")
    room, sockets = room_with(state)
    room.machine._set_phase("day_discuss")

    say(room, "lam", "An khả nghi lắm")

    assert all(len(chats(s)) == 1 for s in sockets.values())


def test_tin_rong_va_qua_dai():
    state = fixed_state(lam="seer", an="wolf", binh="villager")
    room, sockets = room_with(state)
    room.machine._set_phase("day_discuss")

    say(room, "lam", "   \n  ")
    assert chats(sockets["binh"]) == []

    room._last_chat_at.clear()
    say(room, "lam", "x" * 500)
    assert len(chats(sockets["binh"])[0]["text"]) == MAX_CHAT_LEN


def test_lich_su_chat_loc_theo_quyen_doc():
    state = fixed_state(lam="seer", an="wolf", binh="villager")
    room, _ = room_with(state)
    room.machine._set_phase("night_wolf")
    say(room, "an", "bí mật của sói")
    room._last_chat_at.clear()
    room.machine._set_phase("day_discuss")
    say(room, "lam", "công khai")

    assert [m["text"] for m in room.chat_history_for("an")] == ["bí mật của sói", "công khai"]
    assert [m["text"] for m in room.chat_history_for("lam")] == ["công khai"]


# ── Bảng phiếu trực tiếp ──

def test_phieu_soi_chi_soi_thay():
    state = fixed_state(lam="seer", an="wolf", binh="villager", tuyet="wolf")
    machine = PhaseMachine(state)
    machine.start()
    machine._set_phase("night_wolf")
    machine.submit_action("an", ("lam",))

    assert live_votes(machine, "an")["counts"] == {"lam": 1}
    assert live_votes(machine, "lam") is None


def test_phieu_treo_co_cong_khai():
    state = fixed_state(lam="seer", an="wolf", binh="villager", hoa="villager")
    machine = PhaseMachine(state)
    machine._set_phase("day_vote")
    machine.submit_vote("lam", "an")
    machine.submit_vote("binh", "an")

    votes = live_votes(machine, "an")
    assert votes["scope"] == "all"
    assert votes["counts"] == {"an": 2}
    assert votes["by_voter"] == {"lam": "an", "binh": "an"}
    assert votes["decided"] is True
    assert set(votes["pending"]) == {"an", "hoa"}


def test_hoa_phieu_thi_chua_thong_nhat():
    state = fixed_state(lam="seer", an="wolf", binh="villager", hoa="villager")
    machine = PhaseMachine(state)
    machine._set_phase("day_vote")
    machine.submit_vote("lam", "an")
    machine.submit_vote("an", "lam")

    assert live_votes(machine, "lam")["decided"] is False


def test_ngoai_pha_bo_phieu_thi_khong_co_bang():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()

    assert live_votes(machine, "an") is None


def test_state_view_kem_phieu_va_kenh_chat():
    state = fixed_state(lam="seer", an="wolf", binh="villager")
    machine = PhaseMachine(state)
    machine.start()
    machine._set_phase("night_wolf")
    machine.submit_action("an", ("lam",))

    wolf_view = state_view(machine, "an", None)
    seer_view = state_view(machine, "lam", None)

    assert wolf_view["chat_channel"] == "wolf"
    assert wolf_view["votes"]["counts"] == {"lam": 1}
    assert seer_view["chat_channel"] is None
    assert seer_view["votes"] is None
