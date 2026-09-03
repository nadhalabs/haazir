from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.models.booking import Booking
from app.models.payment import Payment, ProviderEarning
from app.models.enums import BookingStatus, PaymentMethod, PaymentStatus, PayoutStatus
from app.services.adapters.payment_adapter import CashPaymentAdapter, GatewayStubAdapter
import uuid


class PaymentService:
    @staticmethod
    def get_adapter(method: PaymentMethod):
        if method == PaymentMethod.CASH:
            return CashPaymentAdapter()
        elif method in (PaymentMethod.UPI, PaymentMethod.GATEWAY):
            return GatewayStubAdapter()
        raise BadRequestException(f"Unsupported payment method: {method}")

    @classmethod
    def create_payment_for_booking(
        cls,
        db: Session,
        booking: Booking,
        payment_method: PaymentMethod
    ) -> Payment:
        # Check if payment already exists
        existing = db.query(Payment).filter(Payment.booking_id == booking.id).first()
        if existing:
            if existing.status == PaymentStatus.PAID:
                raise ConflictException("Payment for this booking is already completed")
            return existing

        amount = booking.price_quote.total_amount
        currency = booking.price_quote.currency

        adapter = cls.get_adapter(payment_method)
        result = adapter.initiate_payment(amount=amount, currency=currency, booking_id=booking.id)

        payment = Payment(
            booking_id=booking.id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status=result["status"],
            transaction_reference=result["transaction_reference"]
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @classmethod
    def mark_payment_successful(
        cls,
        db: Session,
        payment: Payment,
        transaction_reference: str = None
    ) -> Payment:
        if payment.status == PaymentStatus.PAID:
            return payment

        payment.status = PaymentStatus.PAID
        if transaction_reference:
            payment.transaction_reference = transaction_reference

        # Calculate provider earning automatically upon successful payment
        booking = payment.booking
        if booking and booking.provider_id:
            cls.calculate_provider_earning(db, booking)

        db.commit()
        db.refresh(payment)
        return payment

    @classmethod
    def calculate_provider_earning(cls, db: Session, booking: Booking) -> ProviderEarning:
        if not booking.provider_id:
            raise BadRequestException("Cannot calculate earning for booking without assigned provider")

        existing_earning = db.query(ProviderEarning).filter(ProviderEarning.booking_id == booking.id).first()
        if existing_earning:
            return existing_earning

        gross_amount = booking.price_quote.total_amount
        # Deduct platform commission
        commission_rate = settings.PLATFORM_COMMISSION_PERCENTAGE / 100.0
        platform_commission = round(gross_amount * commission_rate, 2)
        provider_amount = round(gross_amount - platform_commission, 2)

        earning = ProviderEarning(
            booking_id=booking.id,
            provider_id=booking.provider_id,
            gross_amount=gross_amount,
            platform_commission=platform_commission,
            provider_earning=provider_amount,
            payout_status=PayoutStatus.PENDING
        )
        db.add(earning)
        db.commit()
        db.refresh(earning)
        return earning
