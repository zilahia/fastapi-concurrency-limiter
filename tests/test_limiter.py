import asyncio

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fastapi_concurrency_limiter import Limiter, Resource


def build_app(capacity: int = 1, timeout: float = 0.1):
    resource = Resource(capacity)
    limiter = Limiter(timeout=timeout, resources=[resource])
    app = FastAPI()

    @app.get("/test")
    @limiter.resources([resource])
    async def endpoint():
        await asyncio.sleep(0.05)
        return {"ok": True}

    return app, resource, limiter


async def test_successful_request():
    app, _, _ = build_app(capacity=2)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/test")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


async def test_503_when_capacity_exhausted():
    started = asyncio.Event()
    can_finish = asyncio.Event()

    resource = Resource(1)
    limiter = Limiter(timeout=0.05, resources=[resource])
    app = FastAPI()

    @app.get("/slow")
    @limiter.resources([resource])
    async def slow():
        started.set()
        await can_finish.wait()
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        task = asyncio.create_task(client.get("/slow"))
        await started.wait()
        r2 = await client.get("/slow")
        can_finish.set()
        r1 = await task

    assert r1.status_code == 200
    assert r2.status_code == 503
    assert r2.json()["detail"] == "Server busy, please retry later"


async def test_semaphore_released_after_request():
    app, _, _ = build_app(capacity=1, timeout=1.0)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.get("/test")
        r2 = await client.get("/test")
    assert r1.status_code == 200
    assert r2.status_code == 200


async def test_semaphore_released_after_endpoint_exception():
    resource = Resource(1)
    limiter = Limiter(timeout=1.0, resources=[resource])
    app = FastAPI()
    call_count = 0

    @app.get("/boom")
    @limiter.resources([resource])
    async def boom():
        nonlocal call_count
        call_count += 1
        raise ValueError("oops")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/boom")
        r2 = await client.get("/boom")

    assert call_count == 2


async def test_wrong_resource_order_raises():
    db = Resource(1)
    fs = Resource(1)
    limiter = Limiter(timeout=1.0, resources=[db, fs])
    app = FastAPI()

    with pytest.raises(ValueError, match="registration order"):
        @app.get("/bad")
        @limiter.resources([fs, db])
        async def bad():
            return {}


async def test_unregistered_resource_raises():
    limiter = Limiter(timeout=1.0, resources=[Resource(1)])
    app = FastAPI()

    with pytest.raises(ValueError, match="not registered"):
        @app.get("/x")
        @limiter.resources([Resource(1)])
        async def x():
            return {}


async def test_concurrent_requests_within_capacity():
    resource = Resource(3)
    limiter = Limiter(timeout=1.0, resources=[resource])
    app = FastAPI()

    @app.get("/concurrent")
    @limiter.resources([resource])
    async def concurrent():
        await asyncio.sleep(0.05)
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        results = await asyncio.gather(*[client.get("/concurrent") for _ in range(3)])

    assert all(r.status_code == 200 for r in results)


async def test_resource_capacity_validation():
    with pytest.raises(ValueError):
        Resource(0)
    with pytest.raises(ValueError):
        Resource(-1)
