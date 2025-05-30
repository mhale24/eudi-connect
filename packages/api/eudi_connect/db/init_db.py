from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from eudi_connect.core.config import settings
from eudi_connect.models.base import Base

# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URI),
    echo=False,
    future=True,
    poolclass=NullPool,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_test_data() -> None:
    """Initialize test data for development."""
    from datetime import datetime, timedelta
    from uuid import uuid4

    from eudi_connect.core.security import get_password_hash
    from eudi_connect.models.merchant import Merchant, MerchantUser
    from eudi_connect.models.billing import BillingPlan

    async with async_session_factory() as db:
        # Create test merchant
        merchant = Merchant(
            name="Test Merchant",
            did=f"did:eudi:{uuid4().hex}",
            is_active=True
        )
        db.add(merchant)
        await db.flush()

        # Create admin user
        user = MerchantUser(
            merchant_id=merchant.id,
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            role="admin"
        )
        db.add(user)

        # Create billing plans
        starter_plan = BillingPlan(
            name="Starter",
            description="Perfect for small businesses",
            price_monthly=49,
            price_yearly=490,
            features={
                "max_api_keys": 2,
                "max_requests_per_month": 10000,
                "max_webhooks": 2,
                "support_level": "email",
            }
        )
        db.add(starter_plan)

        pro_plan = BillingPlan(
            name="Pro",
            description="For growing businesses",
            price_monthly=199,
            price_yearly=1990,
            features={
                "max_api_keys": 5,
                "max_requests_per_month": 50000,
                "max_webhooks": 5,
                "support_level": "priority",
            }
        )
        db.add(pro_plan)

        enterprise_plan = BillingPlan(
            name="Enterprise",
            description="For large organizations",
            price_monthly=999,
            price_yearly=9990,
            features={
                "max_api_keys": -1,  # Unlimited
                "max_requests_per_month": -1,  # Unlimited
                "max_webhooks": -1,  # Unlimited
                "support_level": "dedicated",
            }
        )
        db.add(enterprise_plan)

        await db.commit()


async def init_models() -> None:
    """Initialize all models."""
    # Import all models to ensure they are registered
    from eudi_connect.models import (  # noqa: F401
        merchant,
        credential,
        compliance,
        billing,
    )
