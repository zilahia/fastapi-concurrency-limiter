import random
import string
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiofiles
import aiosqlite
from fastapi import FastAPI

DB_PATH = "messages.db"
DATA_FILE = "data/data.txt"
FILE_SIZE = 5000
FILE_CHUNKSIZE = 1024
DB_SIZE = 1_000_000

WORDS = [
    "hello",
    "world",
    "the",
    "quick",
    "brown",
    "fox",
    "jumps",
    "over",
    "lazy",
    "dog",
    "forum",
    "post",
    "reply",
    "thread",
    "user",
    "message",
    "content",
    "topic",
    "discussion",
    "community",
    "great",
    "awesome",
    "interesting",
    "thanks",
    "welcome",
    "please",
    "help",
    "question",
    "answer",
    "problem",
    "solution",
    "feature",
    "request",
    "update",
    "news",
    "event",
    "share",
    "idea",
    "feedback",
    "opinion",
    "review",
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting test data generation, please wait")
    print(f"size: {FILE_SIZE}")
    print(f"chunksize: {FILE_CHUNKSIZE}")
    print(f"chunksize: {DB_SIZE}")

    Path("data").mkdir(exist_ok=True)
    random_text = "".join(random.choices(string.ascii_letters + string.digits + " ", k=FILE_SIZE))
    async with aiofiles.open(DATA_FILE, "w") as f:
        await f.write(random_text)

    base_date = datetime(2020, 1, 1)
    rows = [
        (
            i,
            random.randint(1, 1000),
            " ".join(random.choices(WORDS, k=random.randint(5, 30))),
            (base_date + timedelta(minutes=random.randint(0, 525_600))).isoformat(),
        )
        for i in range(1, DB_SIZE)
    ]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS messages")
        await db.execute("""
            CREATE TABLE messages (
                message_id INTEGER PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                message    TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            )
        """)
        await db.executemany("INSERT INTO messages VALUES (?, ?, ?, ?)", rows)
        await db.commit()
    print("Done, service starts")

    yield


async def common_read_file() -> str:
    chunks: list[str] = []
    async with aiofiles.open(DATA_FILE) as f:
        while chunk := await f.read(FILE_CHUNKSIZE):
            chunks.append(chunk)
    return "".join(chunks)


async def common_read_messages() -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT message_id, user_id, message, created_at FROM messages "
            "WHERE user_id = 1 ORDER BY RANDOM() LIMIT 100"
        ) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]
