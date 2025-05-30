from datetime import datetime, timedelta
from typing import Dict
from unittest.mock import patch

import pytest
from typing import Any
from typing import Any
import stripe
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.models.billing import (
    BillingPlan,
    MerchantSubscription,
    UsageRecord,
)

pytestmark = pytest.mark.asyncio


async def test_list_plans_empty(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test listing billing plans when none exist."""
    response = await client.get("/api/v1/billing/plans", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_plans(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test listing billing plans."""
    # Create test plan
    plan = BillingPlan(
        name="Test Plan",
        description="A test plan",
        price_monthly=1000,  # $10.00
        price_yearly=10000,  # $100.00
        features={"test": "feature"},
        is_active=True,
        stripe_price_id_monthly="price_monthly_test",
        stripe_price_id_yearly="price_yearly_test",
    )
    db.add(plan)
    await db.commit()

    response = await client.get("/api/v1/billing/plans", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Plan"
    assert data[0]["price_monthly"] == 1000
    assert data[0]["price_yearly"] == 10000


async def test_get_subscription(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
    auth_headers: Dict[str, str],
) -> None:
    """Test getting current subscription."""
    # Create test plan
    plan = BillingPlan(
        name="Test Plan",
        description="A test plan",
        price_monthly=1000,
        price_yearly=10000,
        features={},
        is_active=True,
    )
    db.add(plan)

    # Create test subscription
    subscription = MerchantSubscription(
        merchant_id=test_merchant["merchant_id"],
        plan=plan,
        billing_cycle="monthly",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
        is_active=True,
    )
    db.add(subscription)
    await db.commit()

    response = await client.get("/api/v1/billing/subscription", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["billing_cycle"] == "monthly"
    assert data["is_active"] is True
    assert data["plan"]["name"] == "Test Plan"


async def test_get_subscription_not_found(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test getting subscription when none exists."""
    response = await client.get("/api/v1/billing/subscription", headers=auth_headers)
    assert response.status_code == 404


@patch("stripe.checkout.Session.create")
async def test_create_checkout_session(
    mock_create_session: Any,
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test creating a checkout session."""
    # Mock Stripe response
    mock_create_session.return_value = stripe.checkout.Session(
        id="cs_test",
        url="https://checkout.stripe.com/test",
    )

    # Create test plan
    plan = BillingPlan(
        name="Test Plan",
        description="A test plan",
        price_monthly=1000,
        price_yearly=10000,
        features={},
        is_active=True,
        stripe_price_id_monthly="price_monthly_test",
        stripe_price_id_yearly="price_yearly_test",
    )
    db.add(plan)
    await db.commit()

    response = await client.post(
        "/api/v1/billing/checkout",
        headers=auth_headers,
        json={
            "plan_id": str(plan.id),
            "billing_cycle": "monthly",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "cs_test"
    assert data["url"] == "https://checkout.stripe.com/test"


async def test_get_usage_metrics(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
    auth_headers: Dict[str, str],
) -> None:
    """Test getting usage metrics."""
    # Create test plan and subscription
    plan = BillingPlan(
        name="Test Plan",
        description="A test plan",
        price_monthly=1000,
        price_yearly=10000,
        features={},
        is_active=True,
    )
    db.add(plan)

    subscription = MerchantSubscription(
        merchant_id=test_merchant["merchant_id"],
        plan=plan,
        billing_cycle="monthly",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
        is_active=True,
    )
    db.add(subscription)

    # Create test usage records
    usage1 = UsageRecord(
        subscription=subscription,
        operation="credential_issue",
        quantity=5,
        metadata={},
    )
    usage2 = UsageRecord(
        subscription=subscription,
        operation="credential_verify",
        quantity=3,
        metadata={},
    )
    db.add_all([usage1, usage2])
    await db.commit()

    response = await client.get("/api/v1/billing/usage", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    operations = {metric["operation"]: metric["total_quantity"] for metric in data}
    assert operations["credential_issue"] == 5
    assert operations["credential_verify"] == 3


@patch("stripe.Webhook.construct_event")
async def test_stripe_webhook_checkout_completed(
    mock_construct_event: Any,
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
) -> None:
    """Test handling checkout.session.completed webhook."""
    # Create test plan
    plan = BillingPlan(
        name="Test Plan",
        description="A test plan",
        price_monthly=1000,
        price_yearly=10000,
        features={},
        is_active=True,
        stripe_price_id_monthly="price_monthly_test",
    )
    db.add(plan)
    await db.commit()

    # Mock Stripe event
    mock_construct_event.return_value = stripe.Event(
        id="evt_test",
        type="checkout.session.completed",
        data={
            "object": stripe.checkout.Session(
                id="cs_test",
                customer="cus_test",
                subscription="sub_test",
            )
        }
    )

    # Mock additional Stripe calls
    with patch("stripe.Customer.retrieve") as mock_customer:
        mock_customer.return_value = stripe.Customer(
            id="cus_test",
            metadata={"merchant_id": test_merchant["merchant_id"]},
        )
        with patch("stripe.Subscription.retrieve") as mock_subscription:
            mock_subscription.return_value = stripe.Subscription(
                id="sub_test",
                current_period_start=int(datetime.now().timestamp()),
                current_period_end=int((datetime.now() + timedelta(days=30)).timestamp()),
                plan=stripe.Plan(id="price_monthly_test", interval="month"),
            )

            response = await client.post(
                "/api/v1/billing/webhook",
                headers={"stripe-signature": "test_sig"},
                content=b"test_payload",
            )
            assert response.status_code == 200
            assert response.json() == {"status": "success"}

            # Verify subscription was created
            result = await db.execute(
                select(MerchantSubscription)
                .where(MerchantSubscription.merchant_id == test_merchant["merchant_id"])
            )
            subscription = result.scalar_one()
            assert subscription.stripe_subscription_id == "sub_test"
            assert subscription.stripe_customer_id == "cus_test"
            assert subscription.billing_cycle == "monthly"
