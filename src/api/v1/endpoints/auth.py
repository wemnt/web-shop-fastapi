from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from api.deps import AuthServiceDep, TokenServiceDep
from schemas.auth import RefreshRequest, Token

LoginFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form: LoginFormDep, auth: AuthServiceDep, tokens: TokenServiceDep
) -> Token:
    user = await auth.authenticate(form.username, form.password)
    return await tokens.issue_pair(user.id)


@router.post("/refresh", response_model=Token)
async def refresh(data: RefreshRequest, token: TokenServiceDep) -> Token:
    return await token.rotate_refresh(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, token: TokenServiceDep) -> None:
    await token.revoke(data.refresh_token)
