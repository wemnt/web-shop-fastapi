from collections.abc import Awaitable, Callable

from models.user import User

CreateUser = Callable[..., Awaitable[User]]
AuthHeaders = Callable[[User], dict[str, str]]
