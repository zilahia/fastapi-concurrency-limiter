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

    def resources(self, resources: list[Resource]) -> Callable:
        for r in resources:
            if r not in self._resources:
                raise ValueError(f"Resource {r!r} was not registered with this Limiter")

        positions = [self._resources.index(r) for r in resources]
        if positions != sorted(positions):
            raise ValueError(
                "Resources must be passed in registration order to prevent deadlocks"
            )

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                async with self._acquire_all(resources):
                    return await func(*args, **kwargs)

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
