from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.enums import UserRole


class UserRegister(BaseModel):
    phone: str
    password: str
    full_name: str
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.CUSTOMER


class UserLogin(BaseModel):
    phone: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None
