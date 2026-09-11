import random

import pytest

from app.game.roles import get_role
from app.game.setup import DEFAULT_SETUPS, MAX_PLAYERS, MIN_PLAYERS, build_state
from app.game.state import Faction


def names(n: int) -> dict[str, str]:
    return {f"p{i}": f"Người {i}" for i in range(n)}


def test_moi_so_nguoi_tu_5_den_18_deu_co_bo_vai():
    for n in range(MIN_PLAYERS, MAX_PLAYERS + 1):
        assert len(DEFAULT_SETUPS[n]) == n


def test_moi_vai_trong_bang_deu_ton_tai_trong_registry():
    for roles in DEFAULT_SETUPS.values():
        for role_id in roles:
            assert get_role(role_id) is not None


def test_build_state_gan_du_vai():
    state = build_state(names(8), random.Random(1))

    assert len(state.players) == 8
    assert sorted(p.role_id for p in state.players.values()) == sorted(DEFAULT_SETUPS[8])


def test_gia_lang_duoc_gan_giap():
    state = build_state(names(11), random.Random(1))
    elder = next(p for p in state.players.values() if p.role_id == "elder")

    assert elder.armor == 1


def test_seed_giong_nhau_cho_ket_qua_giong_nhau():
    a = build_state(names(9), random.Random(42))
    b = build_state(names(9), random.Random(42))

    assert {p.id: p.role_id for p in a.players.values()} == {
        p.id: p.role_id for p in b.players.values()
    }


def test_vai_bi_tat_duoc_thay_bang_dan_thuong():
    state = build_state(names(13), random.Random(1), disabled={"fool"})

    assert all(p.role_id != "fool" for p in state.players.values())
    assert len(state.players) == 13


def test_it_hon_5_nguoi_thi_loi():
    with pytest.raises(ValueError):
        build_state(names(4), random.Random(1))


def test_moi_van_deu_co_it_nhat_mot_soi():
    for n in range(MIN_PLAYERS, MAX_PLAYERS + 1):
        state = build_state(names(n), random.Random(n))
        wolves = [
            p for p in state.players.values()
            if get_role(p.role_id).faction is Faction.WOLF
        ]
        assert wolves
