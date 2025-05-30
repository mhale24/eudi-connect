from datetime import datetime, timedelta
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, SecretStr
from sqlalchemy import func, select

from eudi_connect.api.deps import CurrentUser, DB
from eudi_connect.core.security import generate_api_key, get_password_hash, hash_api_key
from eudi_connect.models.merchant import APIKey, Merchant, MerchantUser
from eudi_connect.models.billing import MerchantSubscription

router = APIRouter()


class MerchantCreate(BaseModel):
    """Merchant creation request model."""
    name: str
    email: EmailStr
    password: SecretStr


class MerchantResponse(BaseModel):
    """Merchant response model."""
    id: UUID
    name: str
    did: str
    is_active: bool
    created_at: datetime


class APIKeyCreate(BaseModel):
    """API key creation request model."""
    name: str
    scopes: List[str]
    expires_in_days: int | None = None


class APIKeyResponse(BaseModel):
    """API key response model."""
    id: UUID
    name: str
    key: str | None  # Only included when first created
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: datetime | None


async def get_merchant_subscription(
    db: DB,
    merchant_id: UUID
) -> MerchantSubscription:
    """Get the active subscription for a merchant."""
    result = await db.execute(
        select(MerchantSubscription)
        .where(MerchantSubscription.merchant_id == merchant_id)
        .where(MerchantSubscription.is_active.is_(True))
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active subscription found"
        )

    return subscription


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    db: DB,
    merchant_in: MerchantCreate
) -> MerchantResponse:
    """Create a new merchant account."""
    # Check if email already exists
    result = await db.execute(
        select(MerchantUser).where(MerchantUser.email == merchant_in.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create merchant
    merchant = Merchant(
        name=merchant_in.name,
        did=f"did:eudi:{uuid4().hex}",  # Generate DID
        is_active=True
    )
    db.add(merchant)
    await db.flush()  # Get merchant ID

    # Create admin user
    user = MerchantUser(
        merchant_id=merchant.id,
        email=merchant_in.email,
        password_hash=get_password_hash(merchant_in.password.get_secret_value()),
        role="admin"
    )
    db.add(user)
    await db.commit()

    return merchant


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    db: DB,
    api_key_in: APIKeyCreate,
    current_user: CurrentUser
) -> APIKeyResponse:
    """Create a new API key for the merchant."""
    # Check API key limit based on subscription
    result = await db.execute(
        select(func.count(APIKey.id))
        .where(APIKey.merchant_id == current_user.merchant_id)
        .where(APIKey.revoked_at.is_(None))
    )
    current_keys = result.scalar_one()

    subscription = await get_merchant_subscription(db, current_user.merchant_id)
    if current_keys >= subscription.plan.features["max_api_keys"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key limit reached for current plan"
        )

    # Generate API key
    api_key, key_prefix = generate_api_key()

    # Calculate expiry
    expires_at = None
    if api_key_in.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_in.expires_in_days)

    # Create API key
    api_key_obj = APIKey(
        merchant_id=current_user.merchant_id,
        name=api_key_in.name,
        key_prefix=key_prefix,
        key_hash=hash_api_key(api_key),
        scopes=api_key_in.scopes,
        expires_at=expires_at
    )
    db.add(api_key_obj)
    await db.commit()

    # Include the actual key in response (only time it's shown)
    response = APIKeyResponse.model_validate(api_key_obj)
    response.key = api_key

    return response


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: DB,
    current_user: CurrentUser
) -> List[APIKeyResponse]:
    """List all active API keys for the merchant."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.merchant_id == current_user.merchant_id)
        .where(APIKey.revoked_at.is_(None))
        .order_by(APIKey.created_at.desc())
    )
    api_keys = result.scalars().all()

    return [APIKeyResponse.model_validate(key) for key in api_keys]


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    db: DB,
    api_key_id: UUID,
    current_user: CurrentUser
) -> None:
    """Revoke an API key."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == api_key_id)
        .where(APIKey.merchant_id == current_user.merchant_id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    api_key.revoked_at = datetime.utcnow()
    await db.commit()
