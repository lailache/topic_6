# src/models.py
from typing import ClassVar, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


SPECIALS = set("!@#$%^&*")


class BaseUser(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    email: EmailStr
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("Name must be a string")
        s = v.strip()
        if not s:
            raise ValueError("Name must not be empty")
        return s.lower().capitalize()


class User(BaseUser):
    password: str = Field(min_length=8)
    age: int = Field(ge=18)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("Password must be a string")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(ch.isdigit() for ch in v):
            raise ValueError("Password must contain at least one digit")
        if not any(ch in SPECIALS for ch in v):
            raise ValueError(f"Password must contain at least one special char from {''.join(SPECIALS)}")
        return v


class AdminUser(User):
    role: Literal["admin", "superadmin"]

    ADMIN_PERMISSIONS: ClassVar[set[str]] = {
        "read",
        "write",
        "delete",
        "view_reports",
        "manage_users",
    }

    def has_permission(self, permission: str) -> bool:
        if self.role == "superadmin":
            return True
        return permission in self.ADMIN_PERMISSIONS
