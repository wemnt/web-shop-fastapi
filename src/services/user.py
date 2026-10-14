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
from services.token import TokenService


class UserService:
    def __init__(self, session: AsyncSession, token: TokenService) -> None:
        self.session = session
        self.token = token

    async def create(self, data: UserCreate) -> User:
        existing = await self.session.scalar(
            select(User).where(User.email == data.email)
        )
        if existing is not None:
            raise UserAlreadyExistsError("Email already exists")

        hashed = await to_thread(hash_password, data.password)
        user = User(**data.model_dump(exclude={"password"}), hashed_password=hashed)
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError:
            raise UserAlreadyExistsError("Email already exists") from None
        return user

    async def get(self, user_id: UUID) -> User:
        query = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )

        user = await self.session.scalar(query)
        if user is None:
            raise UserNotFoundError("User not found")
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == "email" and value != user.email:
                existing = await self.session.scalar(
                    select(User).where(User.email == value)
                )
                if existing is not None:
                    raise UserAlreadyExistsError("Email already exists")
            setattr(user, key, value)

        try:
            await self.session.flush()
        except IntegrityError:
            raise UserAlreadyExistsError("Email already exists") from None
        return user

    async def delete(self, user: User) -> None:
        user.deleted_at = datetime.now(tz=UTC)
        await self.token.revoke_all(user.id)

    async def change_password(self, user: User, data: PasswordChange) -> None:
        is_valid = await to_thread(
            verify_password, data.current_password, user.hashed_password
        )
        if not is_valid:
            raise IncorrectPasswordError("Incorrect password")
        user.hashed_password = await to_thread(hash_password, data.new_password)
        await self.token.revoke_all(user.id)

    async def change_role(self, user_id: UUID, actor_id: UUID, role: UserRole) -> User:
        if user_id == actor_id:
            raise CannotChangeOwnRoleError("Cannot change your own role")
        user = await self.get(user_id)
        user.role = role
        return user
