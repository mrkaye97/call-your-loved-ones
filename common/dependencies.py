from datetime import UTC, datetime
from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from crud.users import UserSchema, get_user
from db.database import get_db
from services.auth import parse_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/login", auto_error=False)

Connection = Annotated[asyncpg.Connection, Depends(get_db)]


async def authenticate(conn: Connection, token: str = Depends(oauth2_scheme)) -> UserSchema:
    data = parse_token(token)

    if not data.expires_at or data.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user(conn, user_id=data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def maybe_authenticate(
    conn: Connection, token: str | None = Depends(oauth2_scheme_optional)
) -> UserSchema | None:
    if token is None:
        return None

    data = parse_token(token)

    if not data.expires_at or data.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user(conn, user_id=data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


User = Annotated[UserSchema, Depends(authenticate)]
MaybeUser = Annotated[UserSchema | None, Depends(maybe_authenticate)]
