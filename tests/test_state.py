from app.game.state import Faction, GameState, Player


def make_state(**role_by_name: str) -> GameState:
    """Tạo state nhanh: make_state(lam="seer", an="wolf")."""
    players = {
        name: Player(id=name, name=name.capitalize(), role_id=role)
        for name, role in role_by_name.items()
    }
    return GameState(players=players)


def test_alive_players_bo_qua_nguoi_chet():
    state = make_state(lam="seer", an="wolf", binh="villager")
    state.get("an").alive = False

    assert [p.id for p in state.alive_players()] == ["lam", "binh"]
    assert state.is_alive("an") is False
    assert state.is_alive("lam") is True


def test_add_log_ghi_theo_thu_tu():
    state = make_state(lam="seer")
    state.add_log("dòng 1")
    state.add_log("dòng 2")

    assert state.log == ["dòng 1", "dòng 2"]


def test_faction_gia_tri_chuoi():
    assert Faction.WOLF.value == "wolf"
    assert Faction.VILLAGE.value == "village"
