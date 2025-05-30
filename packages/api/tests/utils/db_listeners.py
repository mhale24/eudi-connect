"""SQLAlchemy event listeners for debugging async session issues."""
import logging
from functools import wraps

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

def setup_sqlalchemy_debug_listeners(engine):
    """Set up debug listeners for SQLAlchemy async operations.
    
    Args:
        engine: SQLAlchemy async engine to monitor
    """
    # For async engines, we must use the sync_engine for events
    sync_engine = getattr(engine, 'sync_engine', engine)
    
    # Add listener for connect events
    @event.listens_for(sync_engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        logger.debug("SQLAlchemy connection opened")
    
    # Add listener for checkout events
    @event.listens_for(sync_engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("SQLAlchemy connection checkout")
    
    # Add listener for checkin events
    @event.listens_for(sync_engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        logger.debug("SQLAlchemy connection checkin")
    
    # Add listener for close events
    @event.listens_for(sync_engine, "close")
    def on_close(dbapi_connection, connection_record):
        logger.debug("SQLAlchemy connection closed")

def debug_async_session(session_class):
    """Decorator to debug async session operations.
    
    Args:
        session_class: The AsyncSession class to monitor
    """
    # Add debug logging to key session methods
    original_execute = session_class.execute
    original_commit = session_class.commit
    original_rollback = session_class.rollback
    original_close = session_class.close
    
    @wraps(original_execute)
    async def debug_execute(self, *args, **kwargs):
        logger.debug(f"AsyncSession.execute called - args: {args}")
        try:
            result = await original_execute(self, *args, **kwargs)
            logger.debug("AsyncSession.execute completed successfully")
            return result
        except Exception as e:
            logger.error(f"AsyncSession.execute failed: {e}")
            raise
    
    @wraps(original_commit)
    async def debug_commit(self, *args, **kwargs):
        logger.debug("AsyncSession.commit called")
        try:
            result = await original_commit(self, *args, **kwargs)
            logger.debug("AsyncSession.commit completed successfully")
            return result
        except Exception as e:
            logger.error(f"AsyncSession.commit failed: {e}")
            raise
    
    @wraps(original_rollback)
    async def debug_rollback(self, *args, **kwargs):
        logger.debug("AsyncSession.rollback called")
        try:
            result = await original_rollback(self, *args, **kwargs)
            logger.debug("AsyncSession.rollback completed successfully")
            return result
        except Exception as e:
            logger.error(f"AsyncSession.rollback failed: {e}")
            raise
            
    @wraps(original_close)
    async def debug_close(self, *args, **kwargs):
        logger.debug("AsyncSession.close called")
        try:
            result = await original_close(self, *args, **kwargs)
            logger.debug("AsyncSession.close completed successfully")
            return result
        except Exception as e:
            logger.error(f"AsyncSession.close failed: {e}")
            raise
    
    # Replace methods with debug versions
    session_class.execute = debug_execute
    session_class.commit = debug_commit
    session_class.rollback = debug_rollback
    session_class.close = debug_close
    
    return session_class
