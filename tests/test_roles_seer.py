from app.game.intents import Intent
from app.game.pipeline import resolve_night
from app.game.state import Faction
from app.game.roles import get_role
from tests.test_state import make_state


def test_tien_tri_soi_ra_soi():
    state = make_state(lam="seer", an="wolf")
    state.night = 1

    result = resolve_night(state, [Intent("lam", "seer", ("an",))])

    assert len(result.reveals) == 1
    assert result.reveals[0].actor == "lam"
    assert "thuộc phe Sói" in result.reveals[0].text
    assert "KHÔNG" not in result.reveals[0].text


def test_tien_tri_soi_ra_dan():
    state = make_state(lam="seer", an="wolf", binh="witch")
    state.night = 1

    result = resolve_night(state, [Intent("lam", "seer", ("binh",))])

    assert "KHÔNG thuộc phe Sói" in result.reveals[0].text


def test_soi_tien_tri_biet_vai_chinh_xac():
    state = make_state(lam="wolf_seer", binh="witch")
    state.night = 1

    result = resolve_night(state, [Intent("lam", "wolf_seer", ("binh",))])

    assert "Phù Thủy" in result.reveals[0].text


def test_soi_tien_tri_thuoc_phe_soi():
    assert get_role("wolf_seer").faction is Faction.WOLF


def test_reveal_khong_giet_ai():
    state = make_state(lam="seer", an="wolf")
    state.night = 1

    result = resolve_night(state, [Intent("lam", "seer", ("an",))])

    assert result.deaths == []
