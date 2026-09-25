"""Memoized word ladder neighbors."""
from __future__ import annotations

import functools
from collections.abc import Iterable

ALPHABET = "abcdefghijklmnopqrstuvwxyz"


@functools.lru_cache(maxsize=4096)
def neighbors(word: str) -> frozenset[str]:
    found = {
        word[:i] + letter + word[i + 1 :]
        for i in range(len(word))
        for letter in ALPHABET
        if letter != word[i]
    }
    return frozenset(found)


@functools.cache
def is_word(candidate: str, dictionary: frozenset[str]) -> bool:
    return candidate in dictionary


def ladder(start: str, goal: str, dictionary: Iterable[str]) -> list[str] | None:
    words = frozenset(dictionary)
    frontier: list[list[str]] = [[start]]
    seen = {start}
    while frontier:
        path = frontier.pop(0)
        if path[-1] == goal:
            return path
        for nxt in neighbors(path[-1]):
            if nxt not in seen and is_word(nxt, words):
                seen.add(nxt)
                frontier.append([*path, nxt])
    return None
