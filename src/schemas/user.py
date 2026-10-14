from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    PastDate,
    field_validator,
)
from pydantic_extra_types.phone_numbers import PhoneNumber

from models.user import UserRole

LowerEmail = Annotated[EmailStr, BeforeValidator(str.lower)]


class UserCreate(BaseModel):
    email: LowerEmail
    name: str = Field(min_length=2, max_length=32)
    date_birth: PastDate | None = None
    mobile_number: PhoneNumber | None = None
    password: str = Field(min_length=8, max_length=32, pattern=r"^\S+$")


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    date_birth: date | None = None
    role: UserRole
    mobile_number: PhoneNumber | None = None
    created_at: datetime
    updated_at: datetime


class AdminUserRead(UserRead):
    is_active: bool
    deleted_at: datetime | None


class UserUpdate(BaseModel):
    email: LowerEmail | None = None
    name: str | None = Field(None, min_length=2, max_length=32)
    date_birth: PastDate | None = None
    mobile_number: PhoneNumber | None = None

    @field_validator("email", "name")
    @classmethod
    def not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=32, pattern=r"^\S+$")


class RoleUpdate(BaseModel):
    role: UserRole
