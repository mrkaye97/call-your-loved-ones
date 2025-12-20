from datetime import UTC, datetime, timedelta

import jwt
from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException, status
from pydantic import BaseModel

from config import settings


class TokenData(BaseModel):
    username: str | None
    expires_at: datetime | None


def hash_password(password: str) -> str:
    return hashpw(password.encode(), gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return checkpw(plain_password.encode(), hashed_password.encode())
    except ValueError:
        return False


def create_access_token(username: str) -> str:
    return jwt.encode(
        {
            "sub": username,
            "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def parse_token(token: str) -> TokenData:
    try:
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )

        return TokenData(
            username=decoded.get("sub"),
            expires_at=decoded.get("exp"),
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
