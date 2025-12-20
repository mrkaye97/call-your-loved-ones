from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg
from pydantic import BaseModel, Field


class LovedOne(BaseModel):
    username: str
    name: str
    last_called: datetime | None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @staticmethod
    def from_db(row: dict[str, Any]) -> "LovedOne":
        return LovedOne(
            username=row["user_id"],
            name=row["name"],
            last_called=row["last_called"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def get_loved_ones(conn: asyncpg.Connection, user_id: UUID) -> list[LovedOne]:
    query = """
        SELECT user_id, name, last_called, created_at, updated_at
        FROM loved_one
        WHERE user_id = $1
        ORDER BY
            CASE WHEN last_called IS NULL THEN 0 ELSE 1 END,
            CASE WHEN last_called IS NULL THEN created_at END DESC,
            last_called ASC
    """

    rows = await conn.fetch(query, user_id)

    return [LovedOne.from_db(row) for row in rows]


async def create_loved_one(conn: asyncpg.Connection, user_id: UUID, name: str) -> LovedOne:
    query = """
        INSERT INTO loved_one (user_id, name, last_called)
        VALUES ($1, $2, NULL)
        RETURNING user_id, name, last_called, created_at, updated_at
    """

    row = await conn.fetchrow(query, user_id, name)

    return LovedOne.from_db(row)


async def mark_loved_one_called(
    conn: asyncpg.Connection, user_id: UUID, loved_one_id: UUID
) -> LovedOne | None:
    query = """
        UPDATE loved_one
        SET
            last_called = NOW(),
            updated_at = NOW()
        WHERE name = $1 AND user_id = $2
        RETURNING user_id, name, last_called, created_at, updated_at
    """

    row = await conn.fetchrow(query, loved_one_id, user_id)

    if not row:
        return None

    return LovedOne.from_db(row)


async def delete_loved_one(conn: asyncpg.Connection, user_id: UUID, loved_one_id: UUID) -> bool:
    query = """
        DELETE FROM loved_one
        WHERE name = $1 AND user_id = $2
    """

    result = await conn.execute(query, loved_one_id, user_id)

    print(result)

    return result == "DELETE 1"
