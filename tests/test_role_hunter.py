from app.game.effects import Kill, KillSource
from app.game.intents import Intent
from app.game.pipeline import PACK_ACTOR, apply_deaths, apply_hunter_shot, resolve_night
from tests.test_state import make_state


def test_tho_san_chet_thi_vao_hang_doi_ban():
    state = make_state(lam="hunter", an="wolf", binh="villager")
    state.night = 1

    result = resolve_night(state, [Intent(PACK_ACTOR, "wolf", ("lam",))])

    assert result.pending_hunters == ["lam"]


def test_phat_ban_giet_muc_tieu():
    state = make_state(lam="hunter", an="wolf", binh="villager")
    state.get("lam").alive = False

    result = apply_hunter_shot(state, "lam", "an")

    assert [d.player_id for d in result.deaths] == ["an"]
    assert state.get("an").death_reason == "hunter"


def test_tho_san_khong_ban_ai_thi_khong_ai_chet():
    state = make_state(lam="hunter", an="wolf")
    state.get("lam").alive = False

    result = apply_hunter_shot(state, "lam", None)

    assert result.deaths == []


def test_phat_ban_khong_bi_bao_ve_chan():
    state = make_state(lam="hunter", an="wolf", binh="guard")
    state.get("lam").alive = False

    result = apply_hunter_shot(state, "lam", "an")

    assert [d.player_id for d in result.deaths] == ["an"]


def test_tho_san_bi_doc_chet_van_duoc_ban():
    state = make_state(lam="hunter", an="wolf", hoa="witch")
    state.night = 2

    result = resolve_night(
        state, [Intent("hoa", "witch", (), {"heal": None, "poison": "lam"})]
    )

    assert result.pending_hunters == ["lam"]


def test_cap_doi_chet_chung_keo_theo_tho_san():
    state = make_state(lam="villager", an="wolf", binh="hunter")
    state.get("lam").lover_id = "binh"
    state.get("binh").lover_id = "lam"

    result = apply_deaths(state, [Kill("lam", KillSource.LYNCH)])

    assert {d.player_id for d in result.deaths} == {"lam", "binh"}
    assert result.pending_hunters == ["binh"]
