from app.game.phases import PhaseMachine
from app.protocol import parse_client_msg
from app.views import can_see_role, prompt_for, state_view
from tests.test_phases import fixed_state


def test_khong_thay_vai_nguoi_khac():
    state = fixed_state(lam="seer", an="wolf", binh="villager")

    assert can_see_role(state, "lam", "lam") is True
    assert can_see_role(state, "lam", "an") is False


def test_soi_thay_dong_doi():
    state = fixed_state(lam="seer", an="wolf", tuyet="white_wolf")

    assert can_see_role(state, "an", "tuyet") is True
    assert can_see_role(state, "an", "lam") is False


def test_nguoi_chet_lo_vai():
    state = fixed_state(lam="seer", an="wolf")
    state.get("lam").alive = False

    assert can_see_role(state, "an", "lam") is True


def test_cap_doi_thay_vai_nhau():
    state = fixed_state(lam="seer", an="wolf", binh="villager")
    state.get("lam").lover_id = "binh"
    state.get("binh").lover_id = "lam"

    assert can_see_role(state, "lam", "binh") is True


def test_state_view_an_vai_nguoi_khac():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()

    view = state_view(machine, "lam", deadline=None)

    roles = {p["id"]: p["role"] for p in view["players"]}
    assert roles["an"] is None
    assert view["you"]["role"] == "seer"
    assert view["phase"] == "night_seer"


def test_prompt_chi_hien_cho_nguoi_den_luot():
    machine = PhaseMachine(fixed_state(lam="seer", an="wolf", binh="villager"))
    machine.start()

    assert prompt_for(machine, "lam")["count"] == 1
    assert prompt_for(machine, "binh") is None


def test_prompt_phu_thuy_kem_nan_nhan():
    machine = PhaseMachine(fixed_state(lam="witch", an="wolf", binh="villager"))
    machine.start()
    machine.submit_action("an", ("binh",))
    machine.advance()

    prompt = prompt_for(machine, "lam")

    assert prompt["action"] == "witch"
    assert prompt["bitten"] == "binh"


def test_parse_client_msg_nhan_dien_loai():
    msg = parse_client_msg({"type": "vote", "target": "p1"})

    assert msg.type == "vote"
    assert msg.target == "p1"
