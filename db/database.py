from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from config import settings


class DatabasePool:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            settings.database_url.get_secret_value(),
            min_size=10,
            max_size=20,
        )

    async def close(self):
        if self.pool is not None:
            await self.pool.close()


db_pool = DatabasePool()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db_pool.connect()

    yield

    await db_pool.close()


async def get_db() -> AsyncGenerator[asyncpg.Connection]:
    if db_pool.pool is None:
        raise RuntimeError("Database pool not initialized")
    async with db_pool.pool.acquire() as conn:
        yield conn
