from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Faction(str, Enum):
    VILLAGE = "village"
    WOLF = "wolf"


@dataclass
class Player:
    id: str
    name: str
    role_id: str = "villager"
    alive: bool = True
    armor: int = 0
    lover_id: str | None = None
    death_reason: str | None = None
    death_night: int | None = None


@dataclass
class GameState:
    players: dict[str, Player]
    night: int = 0
    phase: str = "lobby"
    witch_heal_used: bool = False
    witch_poison_used: bool = False
    guard_last_target: str | None = None
    fool_lynched: bool = False
    log: list[str] = field(default_factory=list)

    def get(self, pid: str) -> Player:
        return self.players[pid]

    def is_alive(self, pid: str) -> bool:
        player = self.players.get(pid)
        return player is not None and player.alive

    def alive_players(self) -> list[Player]:
        return [p for p in self.players.values() if p.alive]

    def add_log(self, line: str) -> None:
        self.log.append(line)
