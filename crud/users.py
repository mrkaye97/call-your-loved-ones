import asyncpg
from pydantic import BaseModel

from crud.loved_ones import LovedOne
from services.auth import hash_password, verify_password


class UserRegistration(BaseModel):
    username: str
    password: str


class RegistrationRequest(BaseModel):
    registration: UserRegistration
    loved_ones: list[LovedOne] = []


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


async def create_user(conn: asyncpg.Connection, registration: RegistrationRequest) -> str:
    loved_one_names = [lo.name for lo in registration.loved_ones]
    loved_one_last_called_ats = [lo.last_called for lo in registration.loved_ones]
    loved_one_created_ats = [lo.created_at for lo in registration.loved_ones]

    async with conn.transaction():
        user_query = """
            WITH user_insert AS (
                INSERT INTO "user" (id)
                VALUES ($1)
                RETURNING id, created_at
            ), password_insert AS (
                INSERT INTO user_password (username, password_hash)
                VALUES ($1, $2)
            ), loved_one_inputs AS (
                SELECT
                    UNNEST($3::TEXT[]) AS name,
                    UNNEST($4::TIMESTAMP[]) AS last_called_at,
                    UNNEST($5::TIMESTAMP[]) AS created_at
            ), loved_one_insert AS (
                INSERT INTO loved_one (username, name, last_called_at, created_at)
                SELECT
                    $1 AS username,
                    loi.name,
                    loi.last_called_at,
                    loi.created_at
                FROM loved_one_inputs loi
            )

            SELECT id, created_at
            FROM user_insert
        """

        row = await conn.fetchrow(
            user_query,
            registration.registration.username,
            hash_password(registration.registration.password),
            loved_one_names,
            loved_one_last_called_ats,
            loved_one_created_ats,
        )

    return str(row["id"])


async def authenticate_user(conn: asyncpg.Connection, username: str, password: str) -> str | None:
    query = """
        SELECT u.id, u.created_at, up.password_hash
        FROM "user" u
        JOIN user_password up ON up.username = u.id
        WHERE u.id = $1
    """

    row = await conn.fetchrow(query, username)

    if not row:
        return None

    if verify_password(password, row["password_hash"]):
        return str(row["id"])

    return None
