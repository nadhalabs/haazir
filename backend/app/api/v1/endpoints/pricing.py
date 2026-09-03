from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_customer
from app.models.user import User
from app.schemas.pricing import QuoteRequest, PriceQuoteResponse
from app.services.pricing_service import PricingService

router = APIRouter()


@router.post("/quote", response_model=PriceQuoteResponse)
def get_price_quote(
    req: QuoteRequest,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Server-authoritative price quote generation.
    Client never passes final price. Quote has a defined validity window.
    """
    quote = PricingService.calculate_quote(
        db=db,
        service_id=req.service_id,
        customer=current_user,
        is_emergency=req.is_emergency,
        provider_id=req.provider_id
    )
    return quote
