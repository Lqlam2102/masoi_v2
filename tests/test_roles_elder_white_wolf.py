import pytest

from app.game.intents import Intent, InvalidIntent
from app.game.pipeline import PACK_ACTOR, resolve_night
from app.game.roles import get_role
from app.game.roles.elder import ELDER_ARMOR
from tests.test_state import make_state


def test_gia_lang_song_sot_don_can_dau_tien():
    state = make_state(lam="elder", an="wolf")
    state.get("lam").armor = ELDER_ARMOR
    state.night = 1

    result = resolve_night(state, [Intent(PACK_ACTOR, "wolf", ("lam",))])

    assert result.deaths == []
    assert state.get("lam").armor == 0


def test_gia_lang_chet_o_don_can_thu_hai():
    state = make_state(lam="elder", an="wolf")
    state.get("lam").armor = 0
    state.night = 2

    result = resolve_night(state, [Intent(PACK_ACTOR, "wolf", ("lam",))])

    assert [d.player_id for d in result.deaths] == ["lam"]


def test_gia_lang_chet_ngay_khi_bi_doc():
    state = make_state(lam="elder", an="wolf", hoa="witch")
    state.get("lam").armor = ELDER_ARMOR
    state.night = 1

    result = resolve_night(
        state, [Intent("hoa", "witch", (), {"heal": None, "poison": "lam"})]
    )

    assert [d.player_id for d in result.deaths] == ["lam"]


def test_soi_trang_chi_nham_soi_khac():
    state = make_state(tuyet="white_wolf", an="wolf", lam="villager")
    actor = state.get("tuyet")

    assert get_role("white_wolf").candidates(state, actor) == ["an"]


def test_soi_trang_khong_duoc_giet_dan():
    state = make_state(tuyet="white_wolf", an="wolf", lam="villager")

    with pytest.raises(InvalidIntent):
        get_role("white_wolf").validate(state, Intent("tuyet", "white_wolf", ("lam",)))


def test_soi_trang_chi_hanh_dong_dem_chan():
    state = make_state(tuyet="white_wolf", an="wolf")
    state.night = 1
    assert get_role("white_wolf").acts_tonight(state) is False
    state.night = 2
    assert get_role("white_wolf").acts_tonight(state) is True


def test_soi_trang_giet_soi_that():
    state = make_state(tuyet="white_wolf", an="wolf", lam="villager")
    state.night = 2

    result = resolve_night(state, [Intent("tuyet", "white_wolf", ("an",))])

    assert [d.player_id for d in result.deaths] == ["an"]
    assert state.get("an").death_reason == "white_wolf"
