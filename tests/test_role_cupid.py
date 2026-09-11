import pytest

from app.game.effects import Kill, KillSource
from app.game.intents import Intent, InvalidIntent
from app.game.pipeline import PACK_ACTOR, apply_deaths, resolve_night
from app.game.roles import get_role
from tests.test_state import make_state


def test_cupid_ghep_doi_dem_dau():
    state = make_state(lam="cupid", an="wolf", binh="villager")
    state.night = 1

    resolve_night(state, [Intent("lam", "cupid", ("an", "binh"))])

    assert state.get("an").lover_id == "binh"
    assert state.get("binh").lover_id == "an"


def test_nguoi_yeu_chet_theo():
    state = make_state(lam="villager", an="wolf", binh="villager")
    state.night = 2
    state.get("lam").lover_id = "binh"
    state.get("binh").lover_id = "lam"

    result = resolve_night(state, [Intent(PACK_ACTOR, "wolf", ("lam",))])

    dead = {d.player_id for d in result.deaths}
    assert dead == {"lam", "binh"}
    assert state.get("binh").death_reason == "lover"


def test_cupid_duoc_ghep_chinh_minh():
    state = make_state(lam="cupid", an="wolf", binh="villager")
    actor = state.get("lam")

    assert "lam" in get_role("cupid").candidates(state, actor)


def test_cupid_phai_chon_hai_nguoi_khac_nhau():
    state = make_state(lam="cupid", an="wolf", binh="villager")

    with pytest.raises(InvalidIntent):
        get_role("cupid").validate(state, Intent("lam", "cupid", ("an", "an")))


def test_cupid_chi_hanh_dong_dem_dau():
    state = make_state(lam="cupid", an="wolf")
    state.night = 2

    assert get_role("cupid").acts_tonight(state) is False


def test_apply_deaths_dung_duoc_doc_lap_cho_pha_ngay():
    state = make_state(lam="villager", an="wolf", binh="villager")
    state.get("lam").lover_id = "binh"
    state.get("binh").lover_id = "lam"

    result = apply_deaths(state, [Kill("lam", KillSource.LYNCH)])

    assert {d.player_id for d in result.deaths} == {"lam", "binh"}
