import random

import pytest

from app.game.intents import InvalidIntent
from app.game.phases import PhaseMachine
from app.game.setup import build_state
from app.game.state import GameState, Player


def fixed_state(**role_by_name: str) -> GameState:
    return GameState(
        players={
            name: Player(id=name, name=name.capitalize(), role_id=role)
            for name, role in role_by_name.items()
        }
    )


def test_bat_dau_mo_pha_dem_dau_tien():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="guard"))
    machine.start()

    assert machine.state.night == 1
    assert machine.phase == "night_seer"


def test_bo_qua_pha_cua_vai_khong_con_song():
    state = fixed_state(lam="seer", an="wolf", binh="guard")
    state.get("lam").alive = False
    machine = PhaseMachine(state)
    machine.start()

    assert machine.phase == "night_guard"


def test_bo_qua_cupid_tu_dem_hai():
    state = fixed_state(lam="cupid", an="wolf", binh="guard")
    machine = PhaseMachine(state)
    machine.start()
    assert machine.phase == "night_cupid"

    state.night = 2
    machine.phase = "lobby"
    machine.start()
    assert machine.phase == "night_guard"


def test_chuoi_pha_dem_sang_ngay():
    # Ruling R2: cast 4 người (không phải 3) — nếu chỉ 3 người, Sói cắn xong
    # đạt tỉ lệ áp đảo và check_winner trả "wolf" trước khi tới day_discuss.
    machine = PhaseMachine(
        fixed_state(lam="seer", an="wolf", binh="villager", hoa="villager")
    )
    machine.start()

    machine.submit_action("lam", ("an",))
    assert machine.advance() == "night_wolf"
    machine.submit_action("an", ("lam",))
    assert machine.advance() == "night_result"
    assert machine.advance() == "day_discuss"


def test_soi_can_chet_sau_dem():
    machine = PhaseMachine(fixed_state(lam="villager", an="wolf", binh="villager"))
    machine.start()
    machine.submit_action("an", ("lam",))
    machine.advance()
    # Ruling R3: advance() đầu chỉ chuyển night_wolf -> night_result; cái chết
    # được áp dụng khi rời night_result, nên cần advance() lần hai.
    machine.advance()

    assert machine.state.get("lam").alive is False


def test_treo_co_theo_da_so():
    state = fixed_state(lam="villager", an="wolf", binh="villager", hoa="villager")
    machine = PhaseMachine(state)
    machine.phase = "day_vote"
    machine.submit_vote("lam", "an")
    machine.submit_vote("binh", "an")
    machine.submit_vote("hoa", "lam")

    machine.advance()

    assert state.get("an").alive is False
    assert state.get("an").death_reason == "lynch"


def test_treo_co_keo_theo_nguoi_yeu_ghi_du_log():
    # apply_deaths() lan chuỗi chết theo người yêu vào NightResult.log,
    # nhưng không tự ghi vào state.log — _finish_day_vote() phải flush nó,
    # y như resolve_night() và apply_hunter_shot() đã làm.
    state = fixed_state(
        lam="villager", an="wolf", binh="villager", hoa="villager", duc="villager"
    )
    state.get("lam").lover_id = "binh"
    state.get("binh").lover_id = "lam"
    machine = PhaseMachine(state)
    machine.phase = "day_vote"
    machine.submit_vote("an", "lam")
    machine.submit_vote("hoa", "lam")
    machine.submit_vote("duc", "lam")

    machine.advance()

    assert state.get("lam").alive is False
    assert state.get("binh").alive is False
    assert state.log.count("Ngày: Lam bị treo cổ") == 1
    assert state.log.count("Binh: chết theo người yêu") == 1


def test_treo_co_thang_ngo_ket_thuc_van():
    state = fixed_state(lam="fool", an="wolf", binh="villager", hoa="villager")
    machine = PhaseMachine(state)
    machine.phase = "day_vote"
    machine.submit_vote("an", "lam")
    machine.submit_vote("binh", "lam")

    machine.advance()

    assert machine.winner == "fool"
    assert machine.phase == "game_over"


def test_tho_san_bi_treo_mo_pha_ban():
    state = fixed_state(lam="hunter", an="wolf", binh="villager", hoa="villager")
    machine = PhaseMachine(state)
    machine.phase = "day_vote"
    machine.submit_vote("an", "lam")
    machine.submit_vote("binh", "lam")

    machine.advance()

    assert machine.phase == "hunter_shot"
    machine.submit_action("lam", ("an",))
    machine.advance()
    assert state.get("an").alive is False


def test_khong_duoc_hanh_dong_sai_pha():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="guard"))
    machine.start()

    with pytest.raises(InvalidIntent):
        machine.submit_action("binh", ("lam",))


def test_van_day_du_chay_duoc_tu_setup():
    state = build_state({f"p{i}": f"Người {i}" for i in range(9)}, random.Random(7))
    machine = PhaseMachine(state)
    machine.start()

    assert machine.phase.startswith("night_")
