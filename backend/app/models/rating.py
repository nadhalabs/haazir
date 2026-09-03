from sqlalchemy import Column, String, Integer, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Rating(BaseModel):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("booking_id", name="uq_rating_booking"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_rating_score_range"),
    )

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    score = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)

    booking = relationship("Booking", back_populates="rating")
    customer = relationship("User", back_populates="ratings_given", foreign_keys=[customer_id])
    provider = relationship("ProviderProfile", back_populates="ratings_received", foreign_keys=[provider_id])
