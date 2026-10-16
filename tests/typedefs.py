from collections.abc import Awaitable, Callable
from typing import Any

from models.product import Product
from models.user import User

CreateUser = Callable[..., Awaitable[User]]
AuthHeaders = Callable[[User], dict[str, str]]
CreateProduct = Callable[..., Awaitable[Product]]
CreateOrder = Callable[..., Awaitable[dict[str, Any]]]
