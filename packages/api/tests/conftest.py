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

# Use a test PostgreSQL database
engine = create_async_engine(
    "postgresql+asyncpg://postgres:postgres@localhost:5432/eudi_connect_test",
)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Database fixture.
    
    Creates a completely isolated database session for each test function.
    Tables are created at the start of each test and dropped at the end.
    This ensures complete isolation between tests.
    """
    # Create a unique engine for each test with a function-level scope
    # This ensures complete isolation between test functions
    test_engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/eudi_connect_test",
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,  # Disable connection pooling for test isolation
        echo=True  # Enable SQL query logging
    )
    
    # Set up debug listeners to track SQLAlchemy connection events
    setup_sqlalchemy_debug_listeners(test_engine)
    
    # Create session factory with debugging enabled
    TestSessionClass = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Apply debug instrumentation to AsyncSession class
    debug_async_session(AsyncSession)
    
    # Create all tables before the test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide an isolated session to the test
    async with TestSessionClass() as session:
        # Make session active and ready for use
        await session.begin()
        logging.debug("Database session initialized and transaction begun")
        
        try:
            # Give session to test
            yield session
        except Exception as e:
            logging.error(f"Exception during test execution: {e}")
            raise
        finally:
            # Clean up after test
            logging.debug("Cleaning up database session")
            await session.rollback()
            await session.close()

    # Drop all tables after the test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose of the engine
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def app_fixture(db: AsyncSession) -> AsyncGenerator[FastAPI, None]:
    """FastAPI app fixture with properly initialized async dependencies."""
    # Define async database dependency override
    async def override_get_db():
        # Ensure the session is in a clean state
        await db.commit()
        try:
            yield db
        finally:
            # Always clean up the session after use
            await db.rollback()

    # Create and initialize test DIDKit service properly
    from eudi_connect.core.config import settings
    test_service = DIDKitService(key_path=settings.DIDKIT_KEY_PATH)
    test_service.init()  # Initialize synchronously for test setup
    
    # Set up clean dependency overrides for each test
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_didkit_service] = lambda: test_service
    
    # Provide the configured app to the test
    yield app
    
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
    # Create merchant
    merchant = Merchant(
        name="Test Merchant",
        did="did:web:test.com",
    )
    db.add(merchant)

    # Create merchant user
    user = MerchantUser(
        merchant=merchant,
        email="test@test.com",
        password_hash=get_password_hash("testpass123"),
        role="admin",  # Required field based on the model
    )
    db.add(user)

    # Create API key
    key, prefix = generate_api_key()
    hashed_key = hash_api_key(key)
    api_key = APIKey(
        merchant=merchant,
        key_hash=hashed_key,
        key_prefix=prefix,
        name="Test Key",
        scopes=["*"],
    )
    db.add(api_key)

    await db.commit()

    return {
        "merchant_id": str(merchant.id),
        "user_id": str(user.id),
        "api_key": f"Bearer {key}",
    }


@pytest_asyncio.fixture
async def auth_headers(test_merchant: Dict[str, str]) -> Dict[str, str]:
    """Authorization headers with API key."""
    # Extract the actual key value without the 'Bearer ' prefix
    api_key = test_merchant["api_key"].replace("Bearer ", "")
    return {"X-API-Key": api_key}
