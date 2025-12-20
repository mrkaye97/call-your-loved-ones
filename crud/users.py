from datetime import datetime
from typing import Any

import asyncpg
from pydantic import BaseModel

from services.auth import hash_password, verify_password


class UserRegistration(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_db(row: dict[str, Any]) -> "User":
        return User(
            username=row["user_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def get_user(conn: asyncpg.Connection, username: str) -> User | None:
    query = """
        SELECT id, created_at, updated_at
        FROM "user"
        WHERE id = $1
    """

    row = await conn.fetchrow(query, username)

    if not row:
        return None

    return User.from_db(row)


async def create_user(conn: asyncpg.Connection, registration: UserRegistration) -> User:
    async with conn.transaction():
        user_query = """
            WITH user_insert AS (
                INSERT INTO "user" (id)
                VALUES ($1)
                RETURNING id, created_at, updated_at
            ), password_insert AS (
                INSERT INTO user_password (user_id, password_hash)
                VALUES ($1, $2)
            )

            SELECT id, created_at, updated_at
            FROM user_insert
        """

        row = await conn.fetchrow(
            user_query,
            registration.username,
            hash_password(registration.password),
        )

    return User.from_db(row)


async def authenticate_user(conn: asyncpg.Connection, username: str, password: str) -> User | None:
    query = """
        SELECT u.id, u.created_at, u.updated_at, up.password_hash
        FROM "user" u
        JOIN user_password up ON up.user_id = u.id
        WHERE u.id = $1
    """

    row = await conn.fetchrow(query, username)

    if not row:
        return None

    if verify_password(password, row["password_hash"]):
        return User.from_db(row)

    return None
