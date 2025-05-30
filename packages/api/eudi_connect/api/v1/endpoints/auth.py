from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.api.deps import DB, CurrentUser
from eudi_connect.core.config import settings
from eudi_connect.core.security import create_access_token, get_password_hash, verify_password
from eudi_connect.models.merchant import MerchantUser

router = APIRouter()


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response model."""
    email: EmailStr
    role: str
    merchant_id: str


@router.post("/login", response_model=Token)
async def login(
    db: DB,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """Login endpoint for merchant users."""
    # Get user from database
    result = await db.execute(
        select(MerchantUser).where(MerchantUser.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Verify user and password
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if merchant account is active
    if not user.merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant account is inactive"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()

    return Token(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: CurrentUser
) -> UserResponse:
    """Get current user information."""
    return UserResponse(
        email=current_user.email,
        role=current_user.role,
        merchant_id=str(current_user.merchant_id)
    )
