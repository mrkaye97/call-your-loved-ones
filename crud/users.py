import asyncpg
from pydantic import BaseModel

from services.auth import hash_password, verify_password


class UserRegistration(BaseModel):
    username: str
    password: str


async def get_user(conn: asyncpg.Connection, username: str) -> str | None:
    query = """
        SELECT id, created_at
        FROM "user"
        WHERE id = $1
    """

    row = await conn.fetchrow(query, username)

    if not row:
        return None

    return str(row["id"])


async def create_user(conn: asyncpg.Connection, registration: UserRegistration) -> str:
    async with conn.transaction():
        user_query = """
            WITH user_insert AS (
                INSERT INTO "user" (id)
                VALUES ($1)
                RETURNING id, created_at
            ), password_insert AS (
                INSERT INTO user_password (user_id, password_hash)
                VALUES ($1, $2)
            )

            SELECT id, created_at
            FROM user_insert
        """

        row = await conn.fetchrow(
            user_query,
            registration.username,
            hash_password(registration.password),
        )

    return str(row["id"])


async def authenticate_user(conn: asyncpg.Connection, username: str, password: str) -> str | None:
    query = """
        SELECT u.id, u.created_at, up.password_hash
        FROM "user" u
        JOIN user_password up ON up.user_id = u.id
        WHERE u.id = $1
    """

    row = await conn.fetchrow(query, username)

    if not row:
        return None

    if verify_password(password, row["password_hash"]):
        return str(row["id"])

    return None
