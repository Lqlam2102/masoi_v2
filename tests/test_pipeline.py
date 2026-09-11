from app.game.effects import KillSource
from app.game.intents import Intent
from app.game.pipeline import PACK_ACTOR, resolve_night
from tests.test_state import make_state


def bite(target: str) -> Intent:
    return Intent(actor_id=PACK_ACTOR, role_id="wolf", targets=(target,))


def test_soi_can_thi_nan_nhan_chet():
    state = make_state(lam="villager", an="wolf", binh="villager")
    state.night = 1

    result = resolve_night(state, [bite("lam")])

    assert [d.player_id for d in result.deaths] == ["lam"]
    assert result.deaths[0].source == KillSource.WOLF
    assert state.get("lam").alive is False
    assert state.get("lam").death_reason == "wolf"
    assert state.get("lam").death_night == 1


def test_dem_khong_ai_hanh_dong_thi_khong_ai_chet():
    state = make_state(lam="villager", an="wolf")
    state.night = 1

    result = resolve_night(state, [])

    assert result.deaths == []
    assert state.get("lam").alive is True


def test_dan_thuong_khong_co_hanh_dong_dem():
    from app.game.roles import get_role

    assert get_role("villager").night_phase is None
    assert get_role("villager").acts_tonight(make_state(lam="villager")) is False
