import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from fastapi_concurrency_limiter import Limiter, Resource

app = FastAPI(title="Async Bench")

database_resource = Resource(5)
file_resource = Resource(10)
limiter = Limiter(timeout=5, resources=[database_resource, file_resource])


@app.get("/file", response_class=PlainTextResponse)
@limiter.resources([file_resource])
async def read_file() -> str:
    # content = await async_read_my_file()
    content = "file content"
    return content


@app.get("/messages")
@limiter.resources([database_resource])
async def read_messages() -> list[dict[str, Any]]:
    # content = await async_read_my_db()
    content: list[dict[str, Any]] = [{"userid": 1, "message": "Hi!"}]
    return content


@app.get("/messages_and_file")
# @limiter.resources([file_resource, database_resource])  # bad: wrong order risks deadlock
@limiter.resources([database_resource, file_resource])
async def read_messages_and_file() -> dict[str, Any]:
    # file_content = await async_read_my_file()
    file_content = "file content"
    # db_content = await async_read_my_db()
    db_content: list[dict[str, Any]] = [{"userid": 1, "message": "Hi!"}]
    return {"db_content": db_content, "file_content": file_content}


# ---- manual equivalent (no library) ----

SEMAPHORE_TIMEOUT = 2.0
file_semaphore = asyncio.Semaphore(10)


@asynccontextmanager
async def acquire_or_503(semaphore: asyncio.Semaphore) -> AsyncGenerator[None, None]:
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=SEMAPHORE_TIMEOUT)
    except TimeoutError as err:
        raise HTTPException(status_code=503, detail="Server busy, please retry later") from err
    try:
        yield
    finally:
        semaphore.release()


@app.get("/file_manual", response_class=PlainTextResponse)
async def read_file_manual() -> str:
    async with acquire_or_503(file_semaphore):
        # content = await async_read_my_file()
        content = "file content"
    return content
