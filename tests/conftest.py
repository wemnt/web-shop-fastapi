from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

import models  # noqa: F401
from app import app
from core.config import settings
from core.security import create_access_token
from db.base import Base
from db.session import get_session
from models.user import User, UserRole
from schemas.user import UserCreate
from services.token import TokenService
from services.user import UserService
from tests.typedefs import AuthHeaders, CreateUser

TEST_DATABASE_URL = settings.database_url.set(database="webshop_test")


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        yield session
        await session.close()
        await transaction.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def create_user(session: AsyncSession) -> CreateUser:
    async def _create(
        *,
        email: str = "user@test.com",
        password: str = "password123",
        role: UserRole = UserRole.CUSTOMER,
        name: str = "Test",
    ) -> User:
        users = UserService(session, TokenService(session))
        user = await users.create(
            data=UserCreate(email=email, password=password, name=name)
        )
        if role != UserRole.CUSTOMER:
            user.role = role
            await session.flush()
        return user

    return _create


@pytest.fixture
def auth_headers() -> AuthHeaders:
    def _headers(user: User) -> dict[str, str]:
        token = create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    return _headers
