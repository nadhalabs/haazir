from sqlalchemy import Column, String, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import PaymentMethod, PaymentStatus, PayoutStatus


class Payment(BaseModel):
    __tablename__ = "payments"

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    transaction_reference = Column(String(100), unique=True, nullable=True, index=True)

    booking = relationship("Booking", back_populates="payment")


class ProviderEarning(BaseModel):
    __tablename__ = "provider_earnings"

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)

    gross_amount = Column(Float, nullable=False)
    platform_commission = Column(Float, nullable=False)
    provider_earning = Column(Float, nullable=False)
    payout_status = Column(Enum(PayoutStatus), default=PayoutStatus.PENDING, nullable=False, index=True)

    booking = relationship("Booking", back_populates="earning")
    provider = relationship("ProviderProfile", back_populates="earnings")
