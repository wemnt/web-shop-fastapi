class AppError(Exception):
    pass


class NotFoundError(AppError):
    pass


class AlreadyExistsError(AppError):
    pass


class BadRequestError(AppError):
    pass


class UnauthorizedError(AppError):
    pass


class UserAlreadyExistsError(AlreadyExistsError):
    pass


class UserNotFoundError(NotFoundError):
    pass


class IncorrectPasswordError(BadRequestError):
    pass


class ProductNotFoundError(NotFoundError):
    pass


class AuthTokenError(UnauthorizedError):
    pass


class InvalidCredentialsError(UnauthorizedError):
    pass


class ForbiddenError(AppError):
    pass


class InsufficientRoleError(ForbiddenError):
    pass


class CannotChangeOwnRoleError(BadRequestError):
    pass


class InvalidRefreshTokenError(UnauthorizedError):
    pass


class CartQuantityLimitError(BadRequestError):
    pass


class CartItemNotFoundError(NotFoundError):
    pass
