from __future__ import annotations

import random

from app.game.roles.elder import ELDER_ARMOR
from app.game.roles import get_role
from app.game.state import GameState, Player

MIN_PLAYERS = 5
MAX_PLAYERS = 18

DEFAULT_SETUPS: dict[int, list[str]] = {
    5: ["wolf", "seer", "guard", "witch", "villager"],
    6: ["wolf", "wolf", "seer", "guard", "witch", "villager"],
    7: ["wolf", "wolf", "seer", "guard", "witch", "hunter", "villager"],
    8: ["wolf", "wolf", "seer", "guard", "witch", "hunter", "villager", "villager"],
    9: [
        "wolf", "wolf", "wolf_seer", "seer", "guard", "witch", "hunter",
        "villager", "villager",
    ],
}

for _n, _extra in (
    (10, "cupid"),
    (11, "elder"),
    (12, "white_wolf"),
    (13, "fool"),
    (14, "villager"),
    (15, "wolf"),
    (16, "villager"),
    (17, "villager"),
    (18, "wolf"),
):
    DEFAULT_SETUPS[_n] = DEFAULT_SETUPS[_n - 1] + [_extra]


def build_state(
    names: dict[str, str],
    rng: random.Random,
    disabled: set[str] = frozenset(),
    custom_roles: list[str] | None = None,
) -> GameState:
    """Gán vai ngẫu nhiên cho danh sách người chơi.

    Nếu `custom_roles` được cung cấp (danh sách đủ len(names) phần tử và hợp lệ),
    dùng nó thay cho DEFAULT_SETUPS. Ngược lại dùng preset + disabled.
    """
    count = len(names)
    if not MIN_PLAYERS <= count <= MAX_PLAYERS:
        raise ValueError(
            f"Cần {MIN_PLAYERS}–{MAX_PLAYERS} người chơi, đang có {count}"
        )

    if custom_roles and len(custom_roles) == count:
        # Validate: tất cả role_id phải tồn tại trong registry
        valid = []
        for r in custom_roles:
            try:
                get_role(r)
                valid.append(r)
            except KeyError:
                valid.append("villager")
        roles = valid
    else:
        roles = [
            r if r not in disabled else "villager"
            for r in DEFAULT_SETUPS[count]
        ]

    rng.shuffle(roles)
    players: dict[str, Player] = {}
    for (pid, display_name), role_id in zip(names.items(), roles):
        player = Player(id=pid, name=display_name, role_id=role_id)
        if role_id == "elder":
            player.armor = ELDER_ARMOR
        players[pid] = player
    return GameState(players=players)
