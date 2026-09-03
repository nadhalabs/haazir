from sqlalchemy import Column, String, Boolean, Float, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ServiceCategory(BaseModel):
    __tablename__ = "service_categories"

    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    display_order = Column(Integer, default=0, nullable=False)

    services = relationship("Service", back_populates="category", cascade="all, delete-orphan")


class Service(BaseModel):
    __tablename__ = "services"

    category_id = Column(UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    estimated_duration_mins = Column(Integer, default=60, nullable=False)

    base_visit_charge = Column(Float, nullable=False)
    min_charge = Column(Float, nullable=True)
    emergency_surcharge_rate = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    category = relationship("ServiceCategory", back_populates="services")
    provider_services = relationship("ProviderService", back_populates="service", cascade="all, delete-orphan")
    quotes = relationship("PriceQuote", back_populates="service")
    bookings = relationship("Booking", back_populates="service")


class ProviderService(BaseModel):
    __tablename__ = "provider_services"
    __table_args__ = (
        UniqueConstraint("provider_id", "service_id", name="uq_provider_service"),
    )

    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    custom_base_charge = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    provider = relationship("ProviderProfile", back_populates="services_offered")
    service = relationship("Service", back_populates="provider_services")
