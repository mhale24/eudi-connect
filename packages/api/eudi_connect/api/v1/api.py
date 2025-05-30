from fastapi import APIRouter

from eudi_connect.api.v1.endpoints import (
    auth,
    billing,
    compliance,
    credentials,
    merchants,
    wallet,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)
api_router.include_router(
    merchants.router,
    prefix="/merchants",
    tags=["Merchant Management"]
)
api_router.include_router(
    credentials.router,
    prefix="/credentials",
    tags=["Credential Operations"]
)
api_router.include_router(
    wallet.router,
    prefix="/wallet",
    tags=["Wallet Integration"]
)
api_router.include_router(
    compliance.router,
    prefix="/compliance",
    tags=["Compliance Scanner"]
)
api_router.include_router(
    billing.router,
    prefix="/billing",
    tags=["Billing & Analytics"]
)
