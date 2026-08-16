import os
from datetime import datetime, timedelta
from typing import Optional

from asyncpg import UniqueViolationError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.database import get_pool
from app.models import TokenData, UserCreate, UserLogin, UserOut
from app.roles import normalize_role

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Use pbkdf2_sha256 so long passwords work and we avoid the bcrypt 72-byte limit.
# This also avoids the current passlib/bcrypt backend issue in the environment.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_by_email(email: str) -> Optional[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, role, hashed_password, created_at FROM users WHERE email = $1",
            email.lower(),
        )
        return dict(row) if row else None


async def authenticate_user(email: str, password: str) -> UserOut:
    user = await get_user_by_email(email)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserOut(
        id=user["id"],
        email=user["email"],
        role=normalize_role(user["role"]),
        created_at=user["created_at"],
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    if "role" in payload:
        payload["role"] = normalize_role(payload.get("role"))
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserOut:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise ValueError("Token payload missing required claims")
        token_data = TokenData(email=email, role=normalize_role(role))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, role, created_at FROM users WHERE email = $1",
            token_data.email.lower(),
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

    row = dict(row)
    row["role"] = normalize_role(row.get("role"))
    return UserOut(**row)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[UserOut]:
    """Return the current user when a valid Bearer token is provided, else None.

    If credentials are present but invalid, raise the same 401 as `get_current_user`.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise ValueError("Token payload missing required claims")
        token_data = TokenData(email=email, role=normalize_role(role))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, role, created_at FROM users WHERE email = $1",
            token_data.email.lower(),
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

    row = dict(row)
    row["role"] = normalize_role(row.get("role"))
    return UserOut(**row)


async def get_current_admin_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    if normalize_role(current_user.role) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_current_staff_or_admin_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    if normalize_role(current_user.role) not in ("staff", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or admin privileges required",
        )
    return current_user


async def create_user(payload: UserCreate) -> UserOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO users (email, hashed_password, role, admin_requested, staff_requested) "
                "VALUES ($1, $2, $3, $4, $5) "
                "RETURNING id, email, role, created_at",
                payload.email.lower(),
                hash_password(payload.password),
                "client",
                payload.request_admin,
                payload.request_staff,
            )
        except UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with that email already exists",
            )

    row = dict(row)
    row["role"] = normalize_role(row.get("role"))
    return UserOut(**row)
