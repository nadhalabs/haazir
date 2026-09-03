from sqlalchemy import Column, String, Float, Integer, Text, Enum, DateTime, ForeignKey, JSON, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import BookingStatus, AssignmentStatus


class Booking(BaseModel):
    __tablename__ = "bookings"

    booking_number = Column(String(50), unique=True, nullable=False, index=True)

    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="RESTRICT"), nullable=False, index=True)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("price_quotes.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)

    status = Column(Enum(BookingStatus), default=BookingStatus.REQUESTED, nullable=False, index=True)

    customer_notes = Column(Text, nullable=True)
    issue_image_urls = Column(JSON, default=list, nullable=False)

    # Immutable Snapshots at time of booking creation / assignment
    address_snapshot = Column(JSON, nullable=False)  # Lat, Lng, formatted address, etc.
    service_snapshot = Column(JSON, nullable=False)  # Name, category, base fee, etc.
    provider_snapshot = Column(JSON, nullable=True)  # Snapshot of provider info once assigned

    # Lifecycle Timestamps
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    customer = relationship("User", back_populates="bookings", foreign_keys=[customer_id])
    provider = relationship("ProviderProfile", back_populates="bookings", foreign_keys=[provider_id])
    service = relationship("Service", back_populates="bookings")
    price_quote = relationship("PriceQuote", back_populates="booking")

    assignments = relationship("BookingAssignment", back_populates="booking", cascade="all, delete-orphan")
    status_history = relationship("BookingStatusHistory", back_populates="booking", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    earning = relationship("ProviderEarning", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    rating = relationship("Rating", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    support_cases = relationship("SupportCase", back_populates="booking")


class BookingAssignment(BaseModel):
    __tablename__ = "booking_assignments"
    __table_args__ = (
        Index(
            "uq_booking_single_accepted_assignment",
            "booking_id",
            unique=True,
            postgresql_where=text("status = 'ACCEPTED'")
        ),
    )

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.OFFERED, nullable=False, index=True)
    response_time_seconds = Column(Integer, nullable=True)

    booking = relationship("Booking", back_populates="assignments")
    provider = relationship("ProviderProfile", back_populates="assignments")


class BookingStatusHistory(BaseModel):
    __tablename__ = "booking_status_history"

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(Enum(BookingStatus), nullable=True)
    to_status = Column(Enum(BookingStatus), nullable=False)
    changed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String(255), nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    booking = relationship("Booking", back_populates="status_history")
