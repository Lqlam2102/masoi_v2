"""Hồi quy cho các lỗi làm ván treo hoặc giấu thông tin của người chơi."""

import asyncio
import random

from app.game.phases import PhaseMachine
from app.protocol import parse_client_msg
from app.room import DEFAULT_TIMERS, Room
from app.views import prompt_for
from tests.test_phases import fixed_state


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


def wired_room(n: int = 6) -> tuple[Room, list[str], dict[str, FakeSocket]]:
    room = Room(code="TEST", rng=random.Random(3))
    ids = [room.join(f"Người {i}", token=None)[0] for i in range(n)]
    sockets = {pid: FakeSocket() for pid in ids}
    for pid, sock in sockets.items():
        room.connections[pid] = type(
            "C", (), {"ws": sock, "player_id": pid, "token": ""}
        )()
    return room, ids, sockets


def sent_types(sock: FakeSocket, msg_type: str) -> list[dict]:
    return [m for m in sock.sent if m.get("type") == msg_type]


# ── Pha kết quả không được treo ──

def test_moi_pha_tu_chay_deu_co_thoi_luong():
    """Trước đây night_result và day_result không có timer nên ván đứng im."""
    room = Room(code="TEST", rng=random.Random(1))
    for phase in (
        "night_cupid", "night_seer", "night_wolf", "night_witch",
        "night_result", "day_discuss", "day_vote", "day_result", "hunter_shot",
    ):
        assert room.phase_duration(phase) is not None, phase


def test_lobby_va_game_over_khong_co_timer():
    room = Room(code="TEST", rng=random.Random(1))

    assert room.phase_duration("lobby") is None
    assert room.phase_duration("game_over") is None


def test_bao_hieu_binh_minh_truoc_khi_cong_bo():
    room, ids, sockets = wired_room()
    room.start()
    room.machine._set_phase("night_result")

    asyncio.run(room._post_advance())

    dawn = sent_types(sockets[ids[0]], "dawn")
    assert len(dawn) == 1
    assert dawn[0]["duration"] == DEFAULT_TIMERS["night_result"]
    room._cancel_timer()


def test_ket_qua_ngay_duoc_cong_bo():
    """Treo cổ xong phải có thông báo, không chỉ im lặng sang đêm."""
    # 1 Sói / 4 Dân — treo cổ một người Dân thì ván vẫn chưa kết thúc.
    state = fixed_state(
        lam="villager", an="wolf", binh="villager", hoa="villager", tuyet="villager"
    )
    room, ids, sockets = wired_room(5)
    room.machine = PhaseMachine(state)
    room.connections = {
        pid: room.connections[old]
        for pid, old in zip(state.players, ids, strict=True)
    }
    sockets = dict(zip(state.players, (sockets[i] for i in ids), strict=True))
    room.machine._set_phase("day_vote")
    for voter in ("an", "binh", "hoa", "tuyet"):
        room.machine.submit_vote(voter, "lam")

    asyncio.run(room._do_advance())
    room._cancel_timer()

    results = sent_types(sockets["an"], "day_result")
    assert len(results) == 1
    assert [d["id"] for d in results[0]["deaths"]] == ["lam"]


# ── Tiên Tri biết kết quả ngay ──

def test_tien_tri_nhan_ket_qua_ngay_trong_dem():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()

    machine.submit_action("lam", ("an",))

    reveals = machine.take_instant_reveals()
    assert len(reveals) == 1
    assert reveals[0].actor == "lam"
    assert "thuộc phe Sói" in reveals[0].text
    assert machine.take_instant_reveals() == []


def test_soi_tien_tri_nhan_ten_vai_ngay():
    machine = PhaseMachine(
        fixed_state(lam="wolf_seer", an="wolf", binh="witch", hoa="villager")
    )
    machine.start()

    machine.submit_action("lam", ("binh",))

    assert "Phù Thủy" in machine.take_instant_reveals()[0].text


def test_reveal_da_bao_som_khong_lap_lai_luc_sang():
    machine = PhaseMachine(
        fixed_state(lam="seer", an="wolf", binh="villager", hoa="villager")
    )
    machine.start()
    machine.submit_action("lam", ("an",))
    machine.take_instant_reveals()
    machine.advance()                     # night_seer -> night_wolf
    machine.submit_action("an", ("binh",))
    machine.advance()                     # -> night_result
    machine.advance()                     # -> day_discuss, chốt đêm

    assert machine.last_result.reveals == []


# ── Phù Thủy thấy được hai bình ──

def test_prompt_phu_thuy_noi_ro_dung_duoc_binh_nao():
    machine = PhaseMachine(fixed_state(lam="witch", an="wolf", binh="villager"))
    machine.start()
    machine.submit_action("an", ("binh",))
    machine.advance()

    prompt = prompt_for(machine, "lam")

    assert prompt["can_heal"] is True
    assert prompt["can_poison"] is True


def test_khong_con_binh_thi_khong_dung_duoc():
    machine = PhaseMachine(fixed_state(lam="witch", an="wolf", binh="villager"))
    machine.start()
    machine.state.witch_heal_used = True
    machine.state.witch_poison_used = True
    machine.submit_action("an", ("binh",))
    machine.advance()

    prompt = prompt_for(machine, "lam")

    assert prompt["can_heal"] is False
    assert prompt["can_poison"] is False


def test_khong_ai_bi_can_thi_khong_cuu_duoc():
    machine = PhaseMachine(fixed_state(lam="witch", an="wolf", binh="villager"))
    machine.start()
    machine.advance()   # sói không chọn ai

    prompt = prompt_for(machine, "lam")

    assert prompt["bitten"] is None
    assert prompt["can_heal"] is False


# ── Bỏ lượt ──

def test_bo_luot_duoc_tinh_la_da_hanh_dong():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()

    assert machine.everyone_acted() is False
    machine.submit_pass("lam")
    assert machine.everyone_acted() is True


def test_phieu_trang_duoc_tinh_la_da_quyet_dinh():
    machine = PhaseMachine(fixed_state(lam="villager", an="wolf", binh="villager"))
    machine._set_phase("day_vote")
    machine.submit_vote("lam", "an")
    machine.submit_vote("an", None)

    assert machine.everyone_acted() is False
    machine.submit_vote("binh", None)
    assert machine.everyone_acted() is True


def test_bo_luot_duoc_xoa_khi_sang_pha_moi():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()
    machine.submit_pass("lam")

    machine.advance()

    assert machine.passed == set()


# ── Host chỉnh thời gian ──

def test_config_nhan_dinh_dang_client_gui():
    """Client gửi `roles`, trước đây ConfigMsg chỉ có `disabled_roles`."""
    msg = parse_client_msg({
        "type": "config",
        "roles": {"cupid": False, "seer": True},
        "timers": {"night_phase": 90},
    })

    assert msg.roles == {"cupid": False, "seer": True}


def test_host_chinh_duoc_thoi_gian_pha_dem():
    room, ids, sockets = wired_room()
    msg = parse_client_msg({
        "type": "config",
        "roles": {"cupid": False, "seer": True},
        "timers": {"night_phase": 90, "day_discuss": 300},
    })

    asyncio.run(room.handle_config(ids[0], msg))

    assert room.timers["night_phase"] == 90
    assert room.timers["night"] == 90
    assert room.timers["day_discuss"] == 300
    assert "cupid" in room.disabled_roles
    assert "seer" not in room.disabled_roles
    assert sent_types(sockets[ids[0]], "config_ok")


def test_host_ket_thuc_thao_luan_som():
    room, ids, sockets = wired_room()
    room.start()
    room.machine._set_phase("day_discuss")

    asyncio.run(room.handle_advance(ids[0]))
    room._cancel_timer()

    assert room.machine.phase == "day_vote"
    notices = sent_types(sockets[ids[1]], "notice")
    assert notices and "thảo luận" in notices[0]["text"]


def test_khong_phai_host_thi_khong_chot_pha_duoc():
    room, ids, sockets = wired_room()
    room.start()
    room.machine._set_phase("day_discuss")

    asyncio.run(room.handle_advance(ids[1]))
    room._cancel_timer()

    assert room.machine.phase == "day_discuss"
    assert sent_types(sockets[ids[1]], "error")


def test_pha_khong_co_dong_ho_thi_khong_chot_duoc():
    """game_over không có đồng hồ — bấm chốt sớm phải là no-op, không nổ."""
    room, ids, _ = wired_room()
    room.start()
    room.machine._set_phase("game_over")

    asyncio.run(room.handle_advance(ids[0]))

    assert room.machine.phase == "game_over"


def test_state_doi_pha_luon_kem_han_chot():
    """Trước đây broadcast chạy trước _start_timer nên deadline luôn None
    và client không vẽ được đồng hồ đếm ngược."""
    async def scenario():
        room, ids, sockets = wired_room()
        room.start()
        await room._post_advance()
        room._cancel_timer()
        return sent_types(sockets[ids[0]], "state")[-1]

    view = asyncio.run(scenario())

    assert view["deadline"] is not None
    assert view["duration"] == DEFAULT_TIMERS["night_phase"]


def test_state_view_bao_ai_dang_la_host():
    room, ids, sockets = wired_room()
    room.start()

    asyncio.run(room.broadcast_state())
    room._cancel_timer()

    assert sent_types(sockets[ids[0]], "state")[-1]["is_host"] is True
    assert sent_types(sockets[ids[1]], "state")[-1]["is_host"] is False


def test_thoi_gian_bi_kep_trong_khoang_hop_le():
    room, ids, _ = wired_room()
    msg = parse_client_msg({
        "type": "config",
        "timers": {"night_phase": 9999, "day_vote": 1},
    })

    asyncio.run(room.handle_config(ids[0], msg))

    assert room.timers["night_phase"] == 180
    assert room.timers["day_vote"] == 15
