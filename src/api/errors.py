import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from schemas.error import ErrorResponse, FieldError

ERROR_STATUS: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    BadRequestError: status.HTTP_400_BAD_REQUEST,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
}

logger = logging.getLogger(__name__)


def error_response(
    status_code: int,
    message: str,
    detail: list[FieldError] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(message=message, detail=detail)
    return JSONResponse(
        status_code=status_code, content=body.model_dump(), headers=headers
    )


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = str(exc)
    headers = None
    for exc_type, code in ERROR_STATUS.items():
        if isinstance(exc, exc_type):
            status_code = code
            break
    else:
        logger.error("Unmapped AppError: %r", exc)
        message = "Internal server error"
    if isinstance(exc, UnauthorizedError):
        headers = {"WWW-Authenticate": "Bearer"}
    return error_response(status_code, message, headers=headers)


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors: list[FieldError] = []
    for err in exc.errors():
        loc = err["loc"]
        field = ".".join(str(part) for part in loc[1:]) or str(loc[0])
        errors.append(FieldError(field=field, message=err["msg"]))
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "Validation error", errors
    )


async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %r", exc)
    return error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"
    )


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return error_response(exc.status_code, str(exc.detail), headers=exc.headers)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(Exception, unhandled_error_handler)
