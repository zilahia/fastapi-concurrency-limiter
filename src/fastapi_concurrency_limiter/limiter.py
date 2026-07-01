import asyncio
import functools
import inspect
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any, ParamSpec, TypeVar

from fastapi import HTTPException

from .resource import Resource

P = ParamSpec("P")
R = TypeVar("R")


class Limiter:
    def __init__(self, timeout: float, resources: list[Resource]) -> None:
        self.timeout = timeout
        self._resources = resources

    def resources(
        self, resources: list[Resource]
    ) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
        for r in resources:
            if r not in self._resources:
                raise ValueError(f"Resource {r!r} was not registered with this Limiter")

        positions = [self._resources.index(r) for r in resources]
        if positions != sorted(positions):
            raise ValueError("Resources must be passed in registration order to prevent deadlocks")

        def decorator(
            func: Callable[P, Coroutine[Any, Any, R]],
        ) -> Callable[P, Coroutine[Any, Any, R]]:
            @functools.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                async with self._acquire_all(resources):
                    return await func(*args, **kwargs)

            wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
            return wrapper  # type: ignore[return-value]

        return decorator  # type: ignore[return-value]

    @asynccontextmanager
    async def _acquire_all(self, resources: list[Resource]) -> AsyncGenerator[None, None]:
        acquired: list[Resource] = []
        try:
            try:
                async with asyncio.timeout(self.timeout):
                    for resource in resources:
                        await resource.acquire()
                        acquired.append(resource)
            except TimeoutError as err:
                raise HTTPException(
                    status_code=503,
                    detail="Server busy, please retry later",
                ) from err
            yield
        finally:
            for resource in reversed(acquired):
                resource.release()
