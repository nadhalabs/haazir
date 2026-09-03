from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException, ConflictException
from app.models.booking import Booking
from app.models.rating import Rating
from app.models.user import User
from app.models.enums import BookingStatus
from app.schemas.rating import RatingCreate, RatingResponse
from app.api.deps import get_current_customer

router = APIRouter()


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def submit_rating(
    data: RatingCreate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    if not booking:
        raise NotFoundException("Booking not found")

    if booking.customer_id != current_user.id:
        raise ForbiddenException("Booking does not belong to you")

    if booking.status != BookingStatus.COMPLETED:
        raise BadRequestException("Ratings can only be submitted for completed bookings")

    if not booking.provider_id:
        raise BadRequestException("No provider was assigned to this booking")

    existing = db.query(Rating).filter(Rating.booking_id == booking.id).first()
    if existing:
        raise ConflictException("Rating has already been submitted for this booking")

    rating = Rating(
        booking_id=booking.id,
        customer_id=current_user.id,
        provider_id=booking.provider_id,
        score=data.score,
        review_text=data.review_text
    )
    db.add(rating)

    # Recalculate provider average rating
    provider = booking.provider
    new_count = provider.rating_count + 1
    new_avg = ((provider.rating_average * provider.rating_count) + data.score) / new_count
    provider.rating_count = new_count
    provider.rating_average = round(new_avg, 2)

    db.commit()
    db.refresh(rating)
    return rating
