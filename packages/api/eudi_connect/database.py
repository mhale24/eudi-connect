"""
Database compatibility module.
Re-exports from db package to maintain backward compatibility.
"""

from typing import Generator, Any

# Re-export from db module
try:
    from eudi_connect.db.session import SessionLocal, engine
    from eudi_connect.db.base import Base
    
    # Define get_db function to match existing usage in performance tests
    def get_db() -> Generator[Any, None, None]:
        """
        Dependency for getting DB session.
        Yields a SQLAlchemy session and ensures it is closed after use.
        """
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
except ImportError:
    # Define empty placeholders for type checking
    SessionLocal = None
    engine = None
    Base = None
    
    # Empty get_db function in case of import error
    def get_db() -> Generator[Any, None, None]:
        """Placeholder for get_db function"""
        yield None
