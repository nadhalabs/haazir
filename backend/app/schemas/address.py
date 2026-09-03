from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class AddressBase(BaseModel):
    label: str = "Home"
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    latitude: float
    longitude: float
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: Optional[bool] = None


class AddressResponse(AddressBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
