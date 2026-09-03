from datetime import datetime
from typing import Optional, List
import uuid
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.enums import UserRole
from app.schemas.address import AddressResponse


class UserBase(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    full_name: str
    role: UserRole


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_suspended: bool
    created_at: datetime
    addresses: List[AddressResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_suspended: Optional[bool] = None
    role: Optional[UserRole] = None
