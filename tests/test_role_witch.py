import pytest

from app.game.intents import Intent, InvalidIntent
from app.game.pipeline import PACK_ACTOR, pending_bite, resolve_night
from app.game.roles import get_role
from tests.test_state import make_state


def witch(heal: str | None = None, poison: str | None = None) -> Intent:
    return Intent("hoa", "witch", (), {"heal": heal, "poison": poison})


def test_binh_cuu_cuu_duoc_nguoi_bi_can():
    state = make_state(lam="villager", an="wolf", hoa="witch")
    state.night = 1

    result = resolve_night(state, [Intent(PACK_ACTOR, "wolf", ("lam",)), witch(heal="lam")])

    assert result.deaths == []
    assert state.witch_heal_used is True
    assert state.witch_poison_used is False


def test_binh_doc_giet_nguoi_du_co_bao_ve():
    state = make_state(lam="villager", an="wolf", hoa="witch", binh="guard")
    state.night = 1
    intents = [
        Intent("binh", "guard", ("lam",)),
        Intent(PACK_ACTOR, "wolf", ("binh",)),
        witch(poison="lam"),
    ]

    result = resolve_night(state, intents)

    assert "lam" in [d.player_id for d in result.deaths]
    assert state.witch_poison_used is True


def test_cuu_va_doc_cung_mot_dem():
    state = make_state(lam="villager", an="wolf", hoa="witch", binh="villager")
    state.night = 1
    intents = [Intent(PACK_ACTOR, "wolf", ("lam",)), witch(heal="lam", poison="an")]

    result = resolve_night(state, intents)

    assert [d.player_id for d in result.deaths] == ["an"]
    assert state.witch_heal_used is True
    assert state.witch_poison_used is True


def test_khong_duoc_dung_lai_binh_da_het():
    state = make_state(lam="villager", an="wolf", hoa="witch")
    state.witch_heal_used = True

    with pytest.raises(InvalidIntent):
        get_role("witch").validate(state, witch(heal="lam"))


def test_ca_kinh_dien_bao_ve_va_phu_thuy_cung_cuu_mot_nguoi():
    state = make_state(lam="villager", an="wolf", hoa="witch", binh="guard")
    state.night = 1
    intents = [
        Intent("binh", "guard", ("lam",)),
        Intent(PACK_ACTOR, "wolf", ("lam",)),
        witch(heal="lam"),
    ]

    result = resolve_night(state, intents)

    assert result.deaths == []
    assert state.get("lam").alive is True


def test_pending_bite_bao_nan_nhan_cho_phu_thuy():
    intents = [Intent(PACK_ACTOR, "wolf", ("lam",))]

    assert pending_bite(intents) == "lam"
    assert pending_bite([]) is None
