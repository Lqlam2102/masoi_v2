from __future__ import annotations

from app.game.roles.base import Role

REGISTRY: dict[str, Role] = {}


def register(role_cls: type[Role]) -> type[Role]:
    REGISTRY[role_cls.id] = role_cls()
    return role_cls


def get_role(role_id: str) -> Role:
    return REGISTRY[role_id]


def all_roles() -> list[Role]:
    return list(REGISTRY.values())


from app.game.roles import (  # noqa: E402,F401
    cupid, elder, guard, hunter, seer, villager, white_wolf, witch, wolf, wolf_seer,
)
