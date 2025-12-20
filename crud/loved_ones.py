from datetime import datetime
from typing import Any

import asyncpg
from pydantic import BaseModel, Field


class LovedOne(BaseModel):
    name: str
    last_called_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    @staticmethod
    def from_db(row: dict[str, Any]) -> "LovedOne":
        return LovedOne(
            name=row["name"],
            last_called_at=row["last_called_at"],
            created_at=row["created_at"],
        )


async def get_loved_ones(conn: asyncpg.Connection, username: str) -> list[LovedOne]:
    query = """
        SELECT name, last_called_at, created_at
        FROM loved_one
        WHERE username = $1
    """

    rows = await conn.fetch(query, username)

    return [LovedOne.from_db(row) for row in rows]


async def create_loved_one(conn: asyncpg.Connection, username: str, name: str) -> LovedOne:
    query = """
        INSERT INTO loved_one (username, name, last_called_at)
        VALUES ($1, $2, NULL)
        RETURNING name, last_called_at, created_at
    """

    row = await conn.fetchrow(query, username, name)

    return LovedOne.from_db(row)


async def mark_loved_one_called(
    conn: asyncpg.Connection, username: str, loved_one_name: str
) -> LovedOne | None:
    query = """
        UPDATE loved_one
        SET last_called_at = NOW()
        WHERE name = $1 AND username = $2
        RETURNING name, last_called_at, created_at
    """

    row = await conn.fetchrow(query, loved_one_name, username)

    if not row:
        return None

    return LovedOne.from_db(row)


async def delete_loved_one(conn: asyncpg.Connection, username: str, loved_one_name: str) -> bool:
    query = """
        DELETE FROM loved_one
        WHERE name = $1 AND username = $2
    """

    result = await conn.execute(query, loved_one_name, username)

    return bool(result == "DELETE 1")
