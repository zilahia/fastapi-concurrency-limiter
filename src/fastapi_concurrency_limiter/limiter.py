import asyncio
import functools
import inspect
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import HTTPException

from .resource import Resource


class Limiter:
    def __init__(self, timeout: float, resources: list[Resource]) -> None:
        self.timeout = timeout
        self._resources = resources
        # Canonical index for each resource — used to sort acquisition order and prevent deadlocks.
        self._order: dict[int, int] = {id(r): i for i, r in enumerate(resources)}

    def resources(self, resources: list[Resource]) -> Callable:
        for r in resources:
            if id(r) not in self._order:
                raise ValueError(f"Resource {r!r} was not registered with this Limiter")

        ordered = sorted(resources, key=lambda r: self._order[id(r)])

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                async with self._acquire_all(ordered):
                    return await func(*args, **kwargs)

            # Let FastAPI see the original signature for dependency injection.
            wrapper.__signature__ = inspect.signature(func)
            return wrapper

        return decorator

    @asynccontextmanager
    async def _acquire_all(self, resources: list[Resource]):
        acquired: list[Resource] = []
        try:
            for resource in resources:
                try:
                    await asyncio.wait_for(resource._semaphore.acquire(), timeout=self.timeout)
                    acquired.append(resource)
                except asyncio.TimeoutError:
                    raise HTTPException(
                        status_code=503,
                        detail="Server busy, please retry later",
                    )
            yield
        finally:
            for resource in reversed(acquired):
                resource._semaphore.release()
