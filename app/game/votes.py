from __future__ import annotations

from collections import Counter


def count_votes(votes: dict[str, str]) -> dict[str, int]:
    """votes: {người bỏ phiếu: người bị bỏ phiếu}."""
    return dict(Counter(votes.values()))


def tally(votes: dict[str, str]) -> str | None:
    """Đa số tương đối. Hòa hoặc không ai bỏ phiếu → None (không ai chết)."""
    counts = count_votes(votes)
    if not counts:
        return None
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]
