from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    providers,
    services,
    pricing,
    bookings,
    payments,
    ratings,
    support,
    admin,
    ws
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users & Addresses"])
api_router.include_router(providers.router, prefix="/providers", tags=["Providers"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["Ratings"])
api_router.include_router(support.router, prefix="/support", tags=["Support"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(ws.router, prefix="/ws", tags=["Realtime WebSockets"])
