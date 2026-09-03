from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.service import Service, ProviderService
from app.models.pricing import PriceQuote
from app.models.user import User
import uuid


class PricingService:
    @staticmethod
    def calculate_quote(
        db: Session,
        service_id: uuid.UUID,
        customer: User,
        is_emergency: bool = False,
        provider_id: uuid.UUID = None,
        duration_minutes: int = 15  # Quote valid for 15 minutes
    ) -> PriceQuote:
        service = db.query(Service).filter(Service.id == service_id, Service.is_active == True).first()
        if not service:
            raise NotFoundException(detail="Service not found or is currently unavailable")

        base_charge = service.base_visit_charge

        # If a specific provider was requested with a custom base charge
        if provider_id:
            provider_service = db.query(ProviderService).filter(
                ProviderService.provider_id == provider_id,
                ProviderService.service_id == service_id,
                ProviderService.is_active == True
            ).first()
            if provider_service and provider_service.custom_base_charge:
                base_charge = max(base_charge, provider_service.custom_base_charge)

        # Enforce service minimum charge
        if service.min_charge and base_charge < service.min_charge:
            base_charge = service.min_charge

        # Platform Convenience / Service Fee
        service_fee = float(settings.DEFAULT_SERVICE_FEE)

        # Emergency Surcharge
        emergency_surcharge = 0.0
        if is_emergency:
            if service.emergency_surcharge_rate > 0:
                emergency_surcharge = service.emergency_surcharge_rate
            else:
                emergency_surcharge = float(settings.DEFAULT_EMERGENCY_SURCHARGE)

        # Subtotal before tax
        subtotal = base_charge + service_fee + emergency_surcharge

        # Taxes
        tax_amount = round(subtotal * (settings.DEFAULT_TAX_PERCENTAGE / 100.0), 2)
        discount_amount = 0.0

        # Authoritative final amount
        total_amount = round(subtotal + tax_amount - discount_amount, 2)

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)

        quote = PriceQuote(
            service_id=service.id,
            customer_id=customer.id,
            base_charge=base_charge,
            service_fee=service_fee,
            emergency_surcharge=emergency_surcharge,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency="INR",
            is_emergency=is_emergency,
            expires_at=expires_at,
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote

    @staticmethod
    def validate_and_lock_quote(db: Session, quote_id: uuid.UUID, customer_id: uuid.UUID) -> PriceQuote:
        quote = db.query(PriceQuote).filter(PriceQuote.id == quote_id).first()
        if not quote:
            raise NotFoundException("Price quote not found")

        if quote.customer_id != customer_id:
            raise BadRequestException("Quote belongs to a different user")

        if quote.booking is not None:
            raise BadRequestException("Quote has already been used for another booking")

        now = datetime.now(timezone.utc)
        expires_at = quote.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            raise BadRequestException("Quote has expired. Please request a new price quote.")

        return quote
