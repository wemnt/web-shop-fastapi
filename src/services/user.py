from asyncio import to_thread
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    CannotChangeOwnRoleError,
    IncorrectPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from core.security import hash_password, verify_password
from models.user import User, UserRole
from schemas.user import PasswordChange, UserCreate, UserUpdate
from services.token import revoke_all_user_tokens


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    existing = await session.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        raise UserAlreadyExistsError("Email already exists")

    hashed = await to_thread(hash_password, data.password)
    user = User(**data.model_dump(exclude={"password"}), hashed_password=hashed)
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        raise UserAlreadyExistsError("Email already exists") from None
    return user


async def get_user(session: AsyncSession, user_id: UUID) -> User:
    query = select(User).where(
        User.id == user_id,
        User.is_active.is_(True),
        User.deleted_at.is_(None),
    )

    user = await session.scalar(query)
    if user is None:
        raise UserNotFoundError("User not found")
    return user


async def update_user(session: AsyncSession, user_id: UUID, data: UserUpdate) -> User:
    user = await get_user(session, user_id)
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "email" and value != user.email:
            existing = await session.scalar(select(User).where(User.email == value))
            if existing is not None:
                raise UserAlreadyExistsError("Email already exists")
        setattr(user, key, value)

    try:
        await session.flush()
    except IntegrityError:
        raise UserAlreadyExistsError("Email already exists") from None
    return user


async def delete_user(session: AsyncSession, user_id: UUID) -> None:
    user = await get_user(session, user_id)
    user.deleted_at = datetime.now(tz=UTC)
    await revoke_all_user_tokens(session, user.id)


async def update_password(
    session: AsyncSession, user_id: UUID, data: PasswordChange
) -> None:
    user = await get_user(session, user_id)
    is_valid = await to_thread(
        verify_password, data.current_password, user.hashed_password
    )
    if not is_valid:
        raise IncorrectPasswordError("Incorrect password")
    user.hashed_password = await to_thread(hash_password, data.new_password)
    await revoke_all_user_tokens(session, user.id)


async def change_user_role(
    session: AsyncSession, user_id: UUID, actor_id: UUID, role: UserRole
) -> User:
    if user_id == actor_id:
        raise CannotChangeOwnRoleError("Cannot change your own role")
    user = await get_user(session, user_id)
    user.role = role
    return user
