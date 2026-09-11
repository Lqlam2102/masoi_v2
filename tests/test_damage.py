from app.game.effects import Heal, Kill, KillSource, Protect, resolve_damage
from tests.test_state import make_state


def test_bao_ve_chan_don_soi():
    state = make_state(lam="villager", an="wolf")
    effects = [Protect("lam"), Kill("lam", KillSource.WOLF)]

    landed, log = resolve_damage(state, effects)

    assert landed == []
    assert any("được bảo vệ" in line for line in log)


def test_phu_thuy_cuu_chan_don_soi():
    state = make_state(lam="villager", an="wolf")
    landed, _ = resolve_damage(state, [Heal("lam"), Kill("lam", KillSource.WOLF)])

    assert landed == []


def test_doc_khong_bi_chan():
    state = make_state(lam="villager", an="wolf")
    landed, _ = resolve_damage(
        state, [Protect("lam"), Heal("lam"), Kill("lam", KillSource.WITCH)]
    )

    assert landed == [Kill("lam", KillSource.WITCH)]


def test_gia_lang_an_giap_thay_vi_chet():
    state = make_state(lam="elder", an="wolf")
    state.get("lam").armor = 1

    landed, log = resolve_damage(state, [Kill("lam", KillSource.WOLF)])

    assert landed == []
    assert state.get("lam").armor == 0
    assert any("Già Làng" in line for line in log)


def test_gia_lang_het_giap_thi_chet():
    state = make_state(lam="elder", an="wolf")
    state.get("lam").armor = 0

    landed, _ = resolve_damage(state, [Kill("lam", KillSource.WOLF)])

    assert landed == [Kill("lam", KillSource.WOLF)]


def test_don_trung_lap_chi_tinh_mot_lan():
    state = make_state(lam="villager", an="wolf")
    landed, _ = resolve_damage(
        state, [Kill("lam", KillSource.WOLF), Kill("lam", KillSource.WITCH)]
    )

    assert [k.target for k in landed] == ["lam"]


def test_bo_qua_don_vao_nguoi_da_chet():
    state = make_state(lam="villager", an="wolf")
    state.get("lam").alive = False

    landed, _ = resolve_damage(state, [Kill("lam", KillSource.WOLF)])

    assert landed == []
