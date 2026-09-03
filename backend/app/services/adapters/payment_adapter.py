from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
from app.models.enums import PaymentStatus


class PaymentAdapter(ABC):
    @abstractmethod
    def initiate_payment(self, amount: float, currency: str, booking_id: uuid.UUID, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiate payment transaction"""
        pass

    @abstractmethod
    def verify_payment(self, transaction_reference: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Verify status of payment with underlying provider"""
        pass


class CashPaymentAdapter(PaymentAdapter):
    """
    Cash on Delivery / Service Completion Payment Adapter.
    Authoritative verification occurs when provider/admin confirms receipt of cash.
    """
    def initiate_payment(self, amount: float, currency: str, booking_id: uuid.UUID, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ref = f"CASH-{booking_id.hex[:10]}-{uuid.uuid4().hex[:6]}".upper()
        return {
            "status": PaymentStatus.PENDING,
            "transaction_reference": ref,
            "instructions": "Pay provider upon job completion."
        }

    def verify_payment(self, transaction_reference: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "status": PaymentStatus.PAID,
            "transaction_reference": transaction_reference,
            "verified": True
        }


class GatewayStubAdapter(PaymentAdapter):
    """
    Gateway stub for future UPI / Razorpay / Stripe integrations.
    Clean interface without fake network calls or insecure keys.
    """
    def initiate_payment(self, amount: float, currency: str, booking_id: uuid.UUID, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ref = f"GATEWAY-PENDING-{uuid.uuid4().hex[:12]}".upper()
        return {
            "status": PaymentStatus.PENDING,
            "transaction_reference": ref,
            "gateway_order_id": f"order_{uuid.uuid4().hex[:8]}",
            "amount": amount,
            "currency": currency,
        }

    def verify_payment(self, transaction_reference: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Production gateway signature verification logic plugs in here cleanly
        return {
            "status": PaymentStatus.PAID,
            "transaction_reference": transaction_reference,
            "verified": True
        }
