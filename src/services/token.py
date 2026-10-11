from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from models.refresh_token import RefreshToken
from models.user import User
from schemas.auth import Token
from services.exceptions import (
    InvalidRefreshTokenError,
)


async def issue_token_pair(session: AsyncSession, user_id: UUID) -> Token:
    raw_token = generate_refresh_token()

    db_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(UTC)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    session.add(db_token)

    await session.commit()

    return Token(
        access_token=create_access_token(user_id),
        refresh_token=raw_token,
    )


async def revoke_all_user_tokens(session: AsyncSession, user_id: UUID) -> None:
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )
    await session.execute(stmt)


async def rotate_refresh_token(session: AsyncSession, raw_token: str) -> Token:
    db_token = await _get_refresh_token(session, raw_token)
    if db_token is None:
        raise InvalidRefreshTokenError("Invalid refresh token")

    if db_token.revoked_at is not None:
        await revoke_all_user_tokens(session, db_token.user_id)
        await session.commit()
        raise InvalidRefreshTokenError("Invalid refresh token")

    if db_token.expires_at <= datetime.now(UTC):
        raise InvalidRefreshTokenError("Invalid refresh token")

    query = select(User.id).where(
        User.id == db_token.user_id,
        User.is_active.is_(True),
        User.deleted_at.is_(None),
    )

    if await session.scalar(query) is None:
        raise InvalidRefreshTokenError("Invalid refresh token")

    db_token.revoked_at = datetime.now(UTC)
    return await issue_token_pair(session, db_token.user_id)


async def revoke_refresh_token(session: AsyncSession, raw_token: str) -> None:
    db_token = await _get_refresh_token(session, raw_token)
    if db_token is None or db_token.revoked_at is not None:
        return
    db_token.revoked_at = datetime.now(UTC)
    await session.commit()


async def _get_refresh_token(
    session: AsyncSession, raw_token: str
) -> RefreshToken | None:
    query = select(RefreshToken).where(
        RefreshToken.token_hash == hash_refresh_token(raw_token)
    )
    return await session.scalar(query)
