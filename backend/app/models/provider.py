from sqlalchemy import Column, String, Boolean, Float, Integer, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import VerificationStatus


class ProviderProfile(BaseModel):
    __tablename__ = "provider_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    business_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String(512), nullable=True)

    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False, index=True)
    service_radius_km = Column(Float, default=15.0, nullable=False)

    base_latitude = Column(Float, nullable=True, index=True)
    base_longitude = Column(Float, nullable=True, index=True)

    is_online = Column(Boolean, default=False, nullable=False, index=True)
    is_available = Column(Boolean, default=False, nullable=False, index=True)

    rating_average = Column(Float, default=0.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    completed_jobs_count = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="provider_profile")
    documents = relationship("ProviderDocument", back_populates="provider", cascade="all, delete-orphan")
    services_offered = relationship("ProviderService", back_populates="provider", cascade="all, delete-orphan")
    assignments = relationship("BookingAssignment", back_populates="provider")
    bookings = relationship("Booking", back_populates="provider", foreign_keys="Booking.provider_id")
    earnings = relationship("ProviderEarning", back_populates="provider")
    ratings_received = relationship("Rating", back_populates="provider", foreign_keys="Rating.provider_id")


class ProviderDocument(BaseModel):
    __tablename__ = "provider_documents"

    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False)  # e.g., GOVT_ID, TRADE_LICENSE, CERTIFICATE
    document_number = Column(String(100), nullable=True)
    file_url = Column(String(512), nullable=False)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)

    provider = relationship("ProviderProfile", back_populates="documents")
