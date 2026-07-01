from typing import Any

from common import common_read_file, common_read_messages, lifespan
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from fastapi_concurrency_limiter import Limiter, Resource

app = FastAPI(title="Async Bench", lifespan=lifespan)
database_resource = Resource(5)
file_resource = Resource(10)
limiter = Limiter(timeout=2, resources=[database_resource, file_resource])


@app.get(
    "/file",
    response_class=PlainTextResponse,
    summary="Return contents of data/data.txt",
)
@limiter.resources([file_resource])
async def read_file() -> str:
    return await common_read_file()


@app.get("/messages", summary="Return 100 random rows from the messages table")
@limiter.resources([database_resource])
async def read_messages() -> list[dict[str, Any]]:
    return await common_read_messages()
