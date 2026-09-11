from app.game.winner import WINNER_LABEL, check_winner
from tests.test_state import make_state


def kill(state, *pids):
    for pid in pids:
        state.get(pid).alive = False


def test_chua_ket_thuc():
    state = make_state(lam="villager", binh="villager", an="wolf")

    assert check_winner(state) is None


def test_dan_thang_khi_het_soi():
    state = make_state(lam="villager", binh="villager", an="wolf")
    kill(state, "an")

    assert check_winner(state) == "village"


def test_soi_thang_khi_bang_so_dan():
    state = make_state(lam="villager", binh="villager", an="wolf")
    kill(state, "binh")

    assert check_winner(state) == "wolf"


def test_thang_ngo_bi_treo_thang_ngay():
    state = make_state(lam="fool", binh="villager", an="wolf")
    kill(state, "lam")
    state.fool_lynched = True

    assert check_winner(state) == "fool"


def test_cap_doi_khac_phe_thang_khi_con_hai_nguoi():
    state = make_state(lam="villager", an="wolf", binh="villager")
    state.get("lam").lover_id = "an"
    state.get("an").lover_id = "lam"
    kill(state, "binh")

    assert check_winner(state) == "lovers"


def test_cap_doi_cung_phe_khong_thang_rieng():
    state = make_state(lam="villager", binh="villager", an="wolf")
    state.get("lam").lover_id = "binh"
    state.get("binh").lover_id = "lam"
    kill(state, "an")

    assert check_winner(state) == "village"


def test_soi_trang_song_sot_duy_nhat():
    state = make_state(tuyet="white_wolf", an="wolf", lam="villager")
    kill(state, "an", "lam")

    assert check_winner(state) == "white_wolf"


def test_soi_trang_giet_soi_cuoi_lam_dan_thang():
    state = make_state(tuyet="white_wolf", an="wolf", lam="villager", binh="villager")
    kill(state, "tuyet", "an")

    assert check_winner(state) == "village"


def test_moi_ket_qua_deu_co_nhan_tieng_viet():
    for key in ("village", "wolf", "white_wolf", "lovers", "fool"):
        assert key in WINNER_LABEL
