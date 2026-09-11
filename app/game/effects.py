from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.game.state import GameState


class KillSource(str, Enum):
    WOLF = "wolf"
    WHITE_WOLF = "white_wolf"
    WITCH = "witch"
    HUNTER = "hunter"
    LOVER = "lover"
    LYNCH = "lynch"


SOURCE_LABEL: dict[KillSource, str] = {
    KillSource.WOLF: "Sói cắn",
    KillSource.WHITE_WOLF: "Sói Trắng giết",
    KillSource.WITCH: "Phù Thủy đầu độc",
    KillSource.HUNTER: "Thợ Săn bắn",
    KillSource.LOVER: "chết theo người yêu",
    KillSource.LYNCH: "bị dân làng treo cổ",
}

# Chỉ đòn của phe Sói mới chặn được bằng Bảo Vệ / bình cứu / giáp Già Làng.
BLOCKABLE: set[KillSource] = {KillSource.WOLF, KillSource.WHITE_WOLF}


@dataclass(frozen=True)
class Kill:
    target: str
    source: KillSource


@dataclass(frozen=True)
class Protect:
    target: str


@dataclass(frozen=True)
class Heal:
    target: str


@dataclass(frozen=True)
class Pair:
    a: str
    b: str


@dataclass(frozen=True)
class Reveal:
    actor: str
    target: str
    text: str


Effect = Kill | Protect | Heal | Pair | Reveal


def resolve_damage(
    state: GameState, effects: list[Effect]
) -> tuple[list[Kill], list[str]]:
    """Tính xem đòn nào thực sự trúng. Không thay đổi state trừ giáp Già Làng."""
    protected = {e.target for e in effects if isinstance(e, Protect)}
    healed = {e.target for e in effects if isinstance(e, Heal)}
    shielded = protected | healed

    landed: list[Kill] = []
    hit: set[str] = set()
    log: list[str] = []

    for kill in [e for e in effects if isinstance(e, Kill)]:
        target = state.players.get(kill.target)
        if target is None or not target.alive:
            continue
        label = SOURCE_LABEL[kill.source]

        if kill.source in BLOCKABLE and kill.target in shielded:
            log.append(f"{target.name}: {label} nhưng được bảo vệ — không chết")
            continue
        if kill.source in BLOCKABLE and target.armor > 0:
            target.armor -= 1
            log.append(f"{target.name}: {label} nhưng Già Làng còn giáp — không chết")
            continue
        if kill.target in hit:
            continue

        hit.add(kill.target)
        landed.append(kill)
        log.append(f"{target.name}: {label} — chết")

    return landed, log
