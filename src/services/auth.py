from asyncio import to_thread

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    InvalidCredentialsError,
)
from core.security import (
    DUMMY_HASH,
    verify_password,
)
from models.user import User


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def authenticate(self, email: str, password: str) -> User:

        query = select(User).where(
            User.email == email.lower(),
            User.can_login(),
        )

        user = await self.session.scalar(query)
        if user is None:
            await to_thread(verify_password, password, DUMMY_HASH)
            raise InvalidCredentialsError("Invalid email or password")

        if not await to_thread(verify_password, password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        return user
