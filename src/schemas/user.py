from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PastDate, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber

from models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def to_lowercase(cls, v: str | None) -> str | None:
        return v.lower() if isinstance(v, str) else v

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


class UserUpdate(BaseModel):
    email: EmailStr | None = None

    @field_validator("email", mode="before")
    @classmethod
    def to_lowercase(cls, v: str | None) -> str | None:
        return v.lower() if isinstance(v, str) else v

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
