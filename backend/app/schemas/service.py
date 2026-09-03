from typing import Optional, List
import uuid
from pydantic import BaseModel, ConfigDict


class ServiceCategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class ServiceCategoryCreate(ServiceCategoryBase):
    pass


class ServiceCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class ServiceCategoryResponse(ServiceCategoryBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ServiceBase(BaseModel):
    category_id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    estimated_duration_mins: int = 60
    base_visit_charge: float
    min_charge: Optional[float] = None
    emergency_surcharge_rate: float = 0.0
    is_active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    estimated_duration_mins: Optional[int] = None
    base_visit_charge: Optional[float] = None
    min_charge: Optional[float] = None
    emergency_surcharge_rate: Optional[float] = None
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
