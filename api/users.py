from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from common.dependencies import Connection
from crud.users import UserRegistration, authenticate_user, create_user
from services.auth import create_access_token

router = APIRouter(prefix="/api")


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=Token)
async def register(
    user_data: UserRegistration,
    conn: asyncpg.Connection = Connection,
) -> Token:
    username = await create_user(conn, user_data)
    access_token = create_access_token(username)

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    conn: asyncpg.Connection = Connection,
) -> Token:
    username = await authenticate_user(
        conn,
        username=form_data.username,
        password=form_data.password,
    )

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(username)

    return Token(access_token=access_token, token_type="bearer")
