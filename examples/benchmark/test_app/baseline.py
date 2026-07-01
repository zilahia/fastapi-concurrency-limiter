from typing import Any

from common import (
    common_read_file,
    common_read_messages,
    lifespan,
)
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Async Bench", lifespan=lifespan)


@app.get("/file", response_class=PlainTextResponse, summary="Return contents of data/data.txt")
async def read_file() -> str:
    return await common_read_file()


@app.get("/messages", summary="Return 100 random rows from the messages table")
async def read_messages() -> list[dict[str, Any]]:
    return await common_read_messages()
