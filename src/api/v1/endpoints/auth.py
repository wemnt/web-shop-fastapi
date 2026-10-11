from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from db.session import SessionDep
from schemas.auth import RefreshRequest, Token
from services.auth import authenticate_user
from services.token import (
    issue_token_pair,
    revoke_refresh_token,
    rotate_refresh_token,
)

LoginFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form: LoginFormDep, session: SessionDep) -> Token:
    user = await authenticate_user(session, form.username, form.password)
    return await issue_token_pair(session, user.id)


@router.post("/refresh", response_model=Token)
async def refresh(data: RefreshRequest, session: SessionDep) -> Token:
    return await rotate_refresh_token(session, data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, session: SessionDep) -> None:
    await revoke_refresh_token(session, data.refresh_token)
