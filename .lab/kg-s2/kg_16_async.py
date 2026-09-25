"""Async semaphore-bounded fetcher simulation."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable


async def fetch_one(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"result:{name}"


async def bounded_gather(
    names: Iterable[str],
    fetch: Callable[[str, float], Awaitable[str]],
    limit: int = 4,
    delay: float = 0.01,
) -> list[str]:
    semaphore = asyncio.Semaphore(limit)

    async def guarded(name: str) -> str:
        async with semaphore:
            return await fetch(name, delay)

    return list(await asyncio.gather(*(guarded(n) for n in names)))


async def main() -> None:
    outcomes = await bounded_gather([f"n{i}" for i in range(8)], fetch_one)
    print(len(outcomes))


if __name__ == "__main__":
    asyncio.run(main())
