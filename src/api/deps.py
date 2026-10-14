from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from core.exceptions import (
    AuthTokenError,
    InactiveUserError,
    InsufficientRoleError,
    UserNotFoundError,
)
from core.security import decode_access_token
from db.session import SessionDep
from models.user import User, UserRole
from services.auth import AuthService
from services.cart import CartService
from services.order import OrderService
from services.product import ProductService
from services.token import TokenService
from services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_product_service(session: SessionDep) -> ProductService:
    return ProductService(session)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


def get_token_service(session: SessionDep) -> TokenService:
    return TokenService(session)


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def get_user_service(session: SessionDep, tokens: TokenServiceDep) -> UserService:
    return UserService(session, tokens)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_cart_service(session: SessionDep, products: ProductServiceDep) -> CartService:
    return CartService(session, products)


CartServiceDep = Annotated[CartService, Depends(get_cart_service)]


def get_order_service(session: SessionDep, cart: CartServiceDep) -> OrderService:
    return OrderService(session, cart)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], users: UserServiceDep
) -> User:
    user_id = decode_access_token(token)
    try:
        user = await users.get(user_id)
    except UserNotFoundError as e:
        raise AuthTokenError("Invalid token") from e
    if not user.is_active:
        raise InactiveUserError("Account is disabled")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    async def dependency(user: CurrentUserDep) -> User:
        if user.role not in roles:
            raise InsufficientRoleError("Operation not permitted")
        return user

    return dependency


require_admin = require_roles(UserRole.ADMIN)
AdminUserDep = Annotated[User, Depends(require_admin)]
