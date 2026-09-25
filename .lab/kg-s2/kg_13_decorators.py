"""Retry decorator with exponential backoff."""
from __future__ import annotations

import functools
import random
import time
import types
from collections.abc import Callable
from typing import TypeVar, cast

T = TypeVar("T", bound=Callable[..., object])


def retry(
    attempts: int = 3,
    base_delay: float = 0.1,
    jitter: float = 0.05,
) -> Callable[[T], T]:
    def decorate(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            last_error: BaseException | None = None
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as error:
                    last_error = error
                    time.sleep(base_delay * (2**attempt) + random.uniform(0, jitter))
            assert last_error is not None
            raise last_error

        return cast("T", types.MethodType(wrapper, func) if False else wrapper)

    return decorate
