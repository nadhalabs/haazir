from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import SupportCaseStatus


class SupportCase(BaseModel):
    __tablename__ = "support_cases"

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    raised_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    issue_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(SupportCaseStatus), default=SupportCaseStatus.OPEN, nullable=False, index=True)
    resolution_notes = Column(Text, nullable=True)

    booking = relationship("Booking", back_populates="support_cases")
    user = relationship("User", back_populates="support_cases")
