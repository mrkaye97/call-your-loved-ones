from datetime import datetime
from typing import Any

import asyncpg
from pydantic import BaseModel, Field


class LovedOne(BaseModel):
    username: str
    name: str
    last_called: datetime | None
    created_at: datetime = Field(default_factory=datetime.now)

    @staticmethod
    def from_db(row: dict[str, Any]) -> "LovedOne":
        return LovedOne(
            username=row["username"],
            name=row["name"],
            last_called=row["last_called"],
            created_at=row["created_at"],
        )


async def get_loved_ones(conn: asyncpg.Connection, username: str) -> list[LovedOne]:
    query = """
        SELECT user_id, name, last_called, created_at
        FROM loved_one
        WHERE username = $1
        ORDER BY
            CASE WHEN last_called IS NULL THEN 0 ELSE 1 END,
            CASE WHEN last_called IS NULL THEN created_at END DESC,
            last_called ASC
    """

    rows = await conn.fetch(query, username)

    return [LovedOne.from_db(row) for row in rows]


async def create_loved_one(conn: asyncpg.Connection, username: str, name: str) -> LovedOne:
    query = """
        INSERT INTO loved_one (username, name, last_called)
        VALUES ($1, $2, NULL)
        RETURNING username, name, last_called, created_at
    """

    row = await conn.fetchrow(query, username, name)

    return LovedOne.from_db(row)


async def mark_loved_one_called(
    conn: asyncpg.Connection, username: str, loved_one_name: str
) -> LovedOne | None:
    query = """
        UPDATE loved_one
        SET last_called = NOW()
        WHERE name = $1 AND username = $2
        RETURNING user_id, name, last_called, created_at
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

    print(result)

    return bool(result == "DELETE 1")
