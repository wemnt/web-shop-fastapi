from uuid import UUID

from fastapi import APIRouter, status

from api.deps import AdminUserDep, CurrentUserDep, UserServiceDep
from models.user import User
from schemas.user import PasswordChange, RoleUpdate, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    users: UserServiceDep,
) -> User:
    return await users.create(data=data)


@router.get("/me", response_model=UserRead)
async def get_me(user: CurrentUserDep) -> User:
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    user: CurrentUserDep,
    data: UserUpdate,
    users: UserServiceDep,
) -> User:
    return await users.update(user, data=data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user: CurrentUserDep,
    users: UserServiceDep,
) -> None:
    await users.delete(user)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_password(
    user: CurrentUserDep,
    data: PasswordChange,
    users: UserServiceDep,
) -> None:
    await users.change_password(user, data=data)


@router.patch("/{user_id}/role", response_model=UserRead)
async def change_user_role_by_id(
    user_id: UUID, data: RoleUpdate, users: UserServiceDep, admin: AdminUserDep
) -> User:

    return await users.change_role(user_id, actor_id=admin.id, role=data.role)
