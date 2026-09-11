import pytest

from app.game.intents import Intent, InvalidIntent
from app.game.pipeline import PACK_ACTOR, resolve_night
from app.game.roles import get_role
from tests.test_state import make_state


def test_bao_ve_do_duoc_nguoi_bi_soi_can():
    state = make_state(lam="villager", an="wolf", binh="guard")
    state.night = 1
    intents = [
        Intent(PACK_ACTOR, "wolf", ("lam",)),
        Intent("binh", "guard", ("lam",)),
    ]

    result = resolve_night(state, intents)

    assert result.deaths == []
    assert state.get("lam").alive is True
    assert state.guard_last_target == "lam"


def test_bao_ve_duoc_tu_bao_ve():
    state = make_state(binh="guard", an="wolf")
    actor = state.get("binh")

    assert "binh" in get_role("guard").candidates(state, actor)


def test_khong_duoc_bao_ve_cung_nguoi_hai_dem_lien_tiep():
    state = make_state(lam="villager", binh="guard", an="wolf")
    state.guard_last_target = "lam"

    with pytest.raises(InvalidIntent):
        get_role("guard").validate(state, Intent("binh", "guard", ("lam",)))


def test_dem_sau_duoc_bao_ve_lai_nguoi_cu():
    state = make_state(lam="villager", binh="guard", an="wolf")
    state.guard_last_target = "binh"

    get_role("guard").validate(state, Intent("binh", "guard", ("lam",)))


def test_khong_bao_ve_thi_last_target_ve_none():
    state = make_state(lam="villager", an="wolf", binh="guard")
    state.night = 2
    state.guard_last_target = "lam"

    resolve_night(state, [Intent(PACK_ACTOR, "wolf", ("binh",))])

    assert state.guard_last_target is None
