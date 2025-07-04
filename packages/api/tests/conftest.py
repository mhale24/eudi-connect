import asyncio
import logging
from typing import AsyncGenerator, Dict, Generator
from uuid import uuid4

import os
import pytest
import pytest_asyncio

@pytest.fixture(autouse=True, scope="session")
def patch_didkit_key_path():
    from eudi_connect.core.config import settings
    test_key_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "data", "didkit_test_key.json"
        )
    )
    old_path = settings.DIDKIT_KEY_PATH
    settings.DIDKIT_KEY_PATH = test_key_path
    yield
    settings.DIDKIT_KEY_PATH = old_path
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .utils.db_listeners import setup_sqlalchemy_debug_listeners, debug_async_session

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from eudi_connect.api.deps import get_db
from eudi_connect.services.didkit import DIDKitService, get_didkit_service
from eudi_connect.core.config import settings
from eudi_connect.core.security import generate_api_key, get_password_hash, hash_api_key
from eudi_connect.db.init_db import init_db
from eudi_connect.main import app
from eudi_connect.models.base import Base
from eudi_connect.models.merchant import APIKey, Merchant, MerchantUser

# Create a single test engine for all tests
TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/eudi_connect_test"

# We'll use a single engine instance with proper isolation levels
test_engine = create_async_engine(
    TEST_DB_URL,
    isolation_level="SERIALIZABLE",  # Use serializable for maximum isolation
    poolclass=NullPool,  # Disable connection pooling for test isolation
    echo=True,  # Enable SQL query logging
)

# Set up debug listeners to track SQLAlchemy connection events
setup_sqlalchemy_debug_listeners(test_engine)

@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Database fixture.
    
    Creates a completely isolated database session for each test function.
    Each test runs in its own transaction that gets rolled back at the end.
    This ensures complete isolation between tests.
    """
    # Create tables from scratch for clean state
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a session with transaction isolation
    async with AsyncSession(test_engine) as session:
        # Start a transaction that will be rolled back
        await session.begin()
        try:
            logging.debug("Database session initialized with clean tables")
            yield session
        finally:
            # Always rollback the transaction at the end of the test
            await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def app_fixture(db: AsyncSession, test_merchant: Dict[str, str]) -> AsyncGenerator[FastAPI, None]:
    """FastAPI app fixture with properly initialized async dependencies."""
    # Define async database dependency override
    async def override_get_db():
        try:
            # We'll use the same session for the entire test
            yield db
        except Exception as e:
            # Log any errors that occur
            logging.error(f"Error in database dependency: {e}")
            raise
    
    # Mock the API key validation to avoid database lookups
    from uuid import UUID
    from eudi_connect.api.deps import APIKeyAuth, validate_api_key
    from eudi_connect.models.merchant import APIKey
    
    # Create a mock API key object that matches our test merchant
    mock_api_key = APIKey(
        id=UUID('33333333-3333-3333-3333-333333333333'),
        merchant_id=UUID(test_merchant["merchant_id"]),
        key_prefix="eudi_live_test",
        key_hash="mock_hash_not_used",
        name="Test Key",
        scopes=["*"],
    )
    
    # Override the validate_api_key dependency to return our mock API key
    async def mock_validate_api_key(*args, **kwargs):
        return mock_api_key

    # Create and initialize test DIDKit service
    from eudi_connect.core.config import settings
    test_service = DIDKitService(key_path=settings.DIDKIT_KEY_PATH)
    test_service.init()  # Initialize synchronously for test setup
    
    # Override dependencies for testing
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_didkit_service] = lambda: test_service
    app.dependency_overrides[validate_api_key] = mock_validate_api_key
    
    # Provide the configured app to the test
    try:
        yield app
    finally:
        # Clean up dependency overrides after the test
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app_fixture: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client fixture."""
    from httpx import ASGITransport
    transport = ASGITransport(app=app_fixture)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_merchant(db: AsyncSession) -> Dict[str, str]:
    """Create a test merchant with API key."""
    # Use fixed values to ensure consistent behavior across tests
    from uuid import UUID
    import uuid
    
    # Generate a fixed UUID for the merchant for test consistency
    merchant_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Create merchant with fixed ID
    merchant = Merchant(
        id=merchant_id,  # Fixed ID for test consistency
        name="Test Merchant",
        did="did:web:test.com",
        is_active=True,  # Ensure the merchant is active
    )
    db.add(merchant)

    # Create merchant user
    user = MerchantUser(
        id=UUID('22222222-2222-2222-2222-222222222222'),  # Fixed ID
        merchant=merchant,
        email="test@test.com",
        password_hash=get_password_hash("testpass123"),
        role="admin",  # Required field based on the model
    )
    db.add(user)

    # Create API key with fixed key for test consistency
    # Use a key that starts with eudi_live_ to trigger the special case in validate_api_key
    full_key = "eudi_live_test12345678901234"  # This follows the prefix pattern in validate_api_key
    key_prefix = "eudi_live_test"  # Just the prefix part (first 16 chars)
    
    # Since we're using the special case for test keys, we don't need to hash it
    # But we'll hash it anyway for consistency
    raw_key = full_key[key_prefix.rfind('_')+1:]  # Get the part after the last underscore
    hashed_key = hash_api_key(raw_key)
    
    api_key = APIKey(
        id=UUID('33333333-3333-3333-3333-333333333333'),  # Fixed ID
        merchant=merchant,
        key_hash=hashed_key,
        key_prefix=key_prefix,  # Just the prefix part
        name="Test Key",
        scopes=["*"],
    )
    db.add(api_key)

    await db.commit()
    await db.refresh(merchant)  # Ensure all merchant attributes are loaded

    # Print merchant ID to verify it's correctly set up
    print(f"Test merchant created with ID: {merchant.id}")
    
    return {
        "merchant_id": str(merchant.id),
        "user_id": str(user.id),
        "api_key": full_key,  # Return the full API key including prefix
    }


@pytest_asyncio.fixture
async def auth_headers(test_merchant: Dict[str, str]) -> Dict[str, str]:
    """Authorization headers with API key."""
    # Use the full API key as returned by test_merchant fixture
    # This should be in the format expected by the validate_api_key function
    api_key = test_merchant['api_key']
    return {"X-API-Key": api_key}
