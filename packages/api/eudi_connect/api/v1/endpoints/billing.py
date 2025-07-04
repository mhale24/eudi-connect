from datetime import datetime, timedelta
from typing import Annotated, List
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.api.deps import CurrentUser, DB
from eudi_connect.api.v1.schemas.billing import (
    BillingPlanResponse,
    CheckoutSession,
    CreateCheckoutSession,
    SubscriptionResponse,
    UsageFilter,
    UsageMetrics,
)
from eudi_connect.core.config import settings
from eudi_connect.exceptions.billing import (
    PlanNotFoundError,
    StripeIntegrationError,
    StripeNotConfiguredError,
    SubscriptionNotFoundError,
)
from eudi_connect.models.billing import (
    BillingPlan,
    MerchantSubscription,
    UsageRecord,
)
from eudi_connect.services.billing import BillingService

router = APIRouter()

# Configure Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY.get_secret_value()


def get_billing_service(db: DB) -> BillingService:
    """Dependency to get billing service instance."""
    return BillingService(db)


BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]


# Models moved to eudi_connect.api.v1.schemas.billing


# Models moved to eudi_connect.api.v1.schemas.billing


# Models moved to eudi_connect.api.v1.schemas.billing


# Models moved to eudi_connect.api.v1.schemas.billing


# Models moved to eudi_connect.api.v1.schemas.billing


@router.get("/plans", response_model=List[BillingPlanResponse])
async def list_plans(
    db: DB,
    current_user: CurrentUser,
    billing_service: BillingServiceDep,
) -> List[BillingPlanResponse]:
    """List all active billing plans."""
    plans = await billing_service.get_plans()
    return [BillingPlanResponse.model_validate(p) for p in plans]


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    db: DB,
    current_user: CurrentUser,
    billing_service: BillingServiceDep,
) -> SubscriptionResponse:
    """Get current merchant subscription."""
    subscription = await billing_service.get_active_subscription(current_user.merchant_id)
    return SubscriptionResponse.model_validate(subscription)


@router.post("/checkout", response_model=CheckoutSession)
async def create_checkout_session(
    db: DB,
    current_user: CurrentUser,
    billing_service: BillingServiceDep,
    request: CreateCheckoutSession,
) -> CheckoutSession:
    """Create a Stripe checkout session for subscription."""
    session = await billing_service.create_checkout_session(
        merchant_id=current_user.merchant_id,
        merchant_email=current_user.email,
        merchant_name=current_user.merchant.name,
        plan_id=request.plan_id,
        billing_cycle=request.billing_cycle,
        success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
    )
    
    return CheckoutSession(
        url=session.url,
        session_id=session.id,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: DB,
    billing_service: BillingServiceDep,
):
    """Handle Stripe webhook events."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise ValueError("Stripe webhook secret not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
        )
        
        # Handle the event based on type
        if event.type == "checkout.session.completed":
            await billing_service.handle_checkout_completed(event.data.object)
        elif event.type == "customer.subscription.updated":
            await billing_service.handle_subscription_updated(event.data.object)
        elif event.type == "customer.subscription.deleted":
            await billing_service.handle_subscription_deleted(event.data.object)
            
        return {"status": "success"}

    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except Exception as e:
        raise StripeIntegrationError(f"Stripe error: {e}")


@router.get("/usage", response_model=List[UsageMetrics])
async def get_usage_metrics(
    db: DB,
    current_user: CurrentUser,
    billing_service: BillingServiceDep,
    usage_filter: UsageFilter = UsageFilter(),
) -> List[UsageMetrics]:
    """Get usage metrics for the merchant."""
    metrics = await billing_service.get_usage_metrics(
        merchant_id=current_user.merchant_id,
        start_date=usage_filter.start_date,
        end_date=usage_filter.end_date,
        operations=usage_filter.operations,
    )
    return metrics


# These helper functions have been moved to the BillingService class
