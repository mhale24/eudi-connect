from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select

from eudi_connect.api.deps import CurrentUser, DB
from eudi_connect.core.config import settings
from eudi_connect.models.billing import (
    BillingPlan,
    MerchantSubscription,
    UsageRecord,
)

router = APIRouter()

# Configure Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY.get_secret_value()


class BillingPlanResponse(BaseModel):
    """Billing plan response model."""
    id: UUID
    name: str
    description: str
    price_monthly: int
    price_yearly: int
    features: Dict[str, Any]


class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    id: UUID
    plan: BillingPlanResponse
    billing_cycle: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    is_active: bool


class UsageMetrics(BaseModel):
    """Usage metrics response model."""
    operation: str
    total_quantity: int
    period_start: datetime
    period_end: datetime


class CreateCheckoutSession(BaseModel):
    """Checkout session creation request model."""
    plan_id: UUID
    billing_cycle: str


class CheckoutSession(BaseModel):
    """Checkout session response model."""
    session_id: str
    url: str


@router.get("/plans", response_model=List[BillingPlanResponse])
async def list_plans(
    db: DB,
    current_user: CurrentUser,
) -> List[BillingPlanResponse]:
    """List all active billing plans."""
    result = await db.execute(
        select(BillingPlan)
        .where(BillingPlan.is_active.is_(True))
        .order_by(BillingPlan.price_monthly)
    )
    plans = result.scalars().all()
    return [BillingPlanResponse.model_validate(p) for p in plans]


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    db: DB,
    current_user: CurrentUser,
) -> SubscriptionResponse:
    """Get current merchant subscription."""
    result = await db.execute(
        select(MerchantSubscription)
        .where(MerchantSubscription.merchant_id == current_user.merchant_id)
        .where(MerchantSubscription.is_active.is_(True))
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    return SubscriptionResponse.model_validate(subscription)


@router.post("/checkout", response_model=CheckoutSession)
async def create_checkout_session(
    db: DB,
    current_user: CurrentUser,
    request: CreateCheckoutSession,
) -> CheckoutSession:
    """Create a Stripe checkout session for subscription."""
    if not settings.STRIPE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe integration not configured"
        )

    # Get plan
    result = await db.execute(
        select(BillingPlan)
        .where(BillingPlan.id == request.plan_id)
        .where(BillingPlan.is_active.is_(True))
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    try:
        # Create or get Stripe customer
        result = await db.execute(
            select(MerchantSubscription)
            .where(MerchantSubscription.merchant_id == current_user.merchant_id)
            .where(MerchantSubscription.stripe_customer_id.isnot(None))
        )
        existing_sub = result.scalar_one_or_none()

        if existing_sub and existing_sub.stripe_customer_id:
            stripe_customer_id = existing_sub.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={
                    "merchant_id": str(current_user.merchant_id),
                    "merchant_name": current_user.merchant.name,
                }
            )
            stripe_customer_id = customer.id

        # Get price ID based on billing cycle
        price_id = (
            plan.stripe_price_id_yearly
            if request.billing_cycle == "yearly"
            else plan.stripe_price_id_monthly
        )

        if not price_id:
            raise ValueError("Stripe price ID not configured for plan")

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
        )

        return CheckoutSession(
            session_id=checkout_session.id,
            url=checkout_session.url
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: DB,
) -> Dict[str, str]:
    """Handle Stripe webhook events."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe webhooks not configured"
        )

    # Get webhook payload and signature
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
        )

        # Handle specific events
        if event.type == "checkout.session.completed":
            session = event.data.object
            await handle_checkout_completed(db, session)
        elif event.type == "customer.subscription.updated":
            subscription = event.data.object
            await handle_subscription_updated(db, subscription)
        elif event.type == "customer.subscription.deleted":
            subscription = event.data.object
            await handle_subscription_deleted(db, subscription)

        return {"status": "success"}

    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/usage", response_model=List[UsageMetrics])
async def get_usage_metrics(
    db: DB,
    current_user: CurrentUser,
    days: int = 30,
) -> List[UsageMetrics]:
    """Get usage metrics for the merchant."""
    # Get current subscription
    result = await db.execute(
        select(MerchantSubscription)
        .where(MerchantSubscription.merchant_id == current_user.merchant_id)
        .where(MerchantSubscription.is_active.is_(True))
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    # Calculate period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get usage metrics
    result = await db.execute(
        select(
            UsageRecord.operation,
            func.sum(UsageRecord.quantity).label("total_quantity")
        )
        .where(UsageRecord.subscription_id == subscription.id)
        .where(UsageRecord.created_at.between(start_date, end_date))
        .group_by(UsageRecord.operation)
    )
    metrics = result.all()

    return [
        UsageMetrics(
            operation=metric.operation,
            total_quantity=metric.total_quantity,
            period_start=start_date,
            period_end=end_date
        )
        for metric in metrics
    ]


async def handle_checkout_completed(
    db: DB,
    session: stripe.checkout.Session,
) -> None:
    """Handle successful checkout completion."""
    # Get merchant ID from customer metadata
    customer = stripe.Customer.retrieve(session.customer)
    merchant_id = UUID(customer.metadata["merchant_id"])

    # Get subscription details
    subscription = stripe.Subscription.retrieve(session.subscription)

    # Get plan from price ID
    result = await db.execute(
        select(BillingPlan).where(
            (BillingPlan.stripe_price_id_monthly == subscription.plan.id) |
            (BillingPlan.stripe_price_id_yearly == subscription.plan.id)
        )
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise ValueError("Invalid price ID")

    # Create or update subscription
    result = await db.execute(
        select(MerchantSubscription)
        .where(MerchantSubscription.merchant_id == merchant_id)
        .where(MerchantSubscription.is_active.is_(True))
    )
    existing_sub = result.scalar_one_or_none()

    if existing_sub:
        # Update existing subscription
        existing_sub.plan_id = plan.id
        existing_sub.stripe_subscription_id = subscription.id
        existing_sub.stripe_customer_id = customer.id
        existing_sub.billing_cycle = "yearly" if subscription.plan.interval == "year" else "monthly"
        existing_sub.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
        existing_sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
    else:
        # Create new subscription
        new_sub = MerchantSubscription(
            merchant_id=merchant_id,
            plan_id=plan.id,
            stripe_subscription_id=subscription.id,
            stripe_customer_id=customer.id,
            billing_cycle="yearly" if subscription.plan.interval == "year" else "monthly",
            current_period_start=datetime.fromtimestamp(subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(subscription.current_period_end),
            is_active=True
        )
        db.add(new_sub)

    await db.commit()


async def handle_subscription_updated(
    db: DB,
    subscription: stripe.Subscription,
) -> None:
    """Handle subscription updates."""
    result = await db.execute(
        select(MerchantSubscription)
        .where(MerchantSubscription.stripe_subscription_id == subscription.id)
    )
    db_sub = result.scalar_one_or_none()

    if db_sub:
        db_sub.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
        db_sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        db_sub.cancel_at_period_end = subscription.cancel_at_period_end
        await db.commit()


async def handle_subscription_deleted(
    db: DB,
    subscription: stripe.Subscription,
) -> None:
    """Handle subscription deletions."""
    result = await db.execute(
        select(MerchantSubscription)
        .where(MerchantSubscription.stripe_subscription_id == subscription.id)
    )
    db_sub = result.scalar_one_or_none()

    if db_sub:
        db_sub.is_active = False
        await db.commit()
