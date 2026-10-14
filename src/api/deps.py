from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from core.exceptions import AuthTokenError, InsufficientRoleError, UserNotFoundError
from core.security import decode_access_token
from db.session import SessionDep
from models.user import User, UserRole
from services.product import ProductService
from services.token import TokenService
from services.user import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> User:
    user_id = decode_access_token(token)
    try:
        return await get_user(session, user_id)
    except UserNotFoundError as e:
        raise AuthTokenError("Invalid token") from e


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    async def dependency(user: CurrentUserDep) -> User:
        if user.role not in roles:
            raise InsufficientRoleError("Operation not permitted")
        return user

    return dependency


def get_product_service(session: SessionDep) -> ProductService:
    return ProductService(session)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


def get_token_service(session: SessionDep) -> TokenService:
    return TokenService(session)


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


require_admin = require_roles(UserRole.ADMIN)
AdminUserDep = Annotated[User, Depends(require_admin)]
