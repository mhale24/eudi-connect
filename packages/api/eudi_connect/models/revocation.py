import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, String, LargeBinary, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from eudi_connect.models.base import Base


class RevocationList(Base):
    """Model for storing revocation lists."""
    __tablename__ = "revocation_lists"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    issuer_did = Column(String, nullable=False, index=True)
    credential_type_id = Column(String, nullable=False, index=True)
    encoded_list = Column(LargeBinary, nullable=False)  # ZLIB-compressed and base64-encoded bitstring
    revocation_metadata = Column(JSON, nullable=True)  # Additional metadata about the revocation list
    revoked_count = Column(Integer, default=0)  # Number of revoked credentials in this list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint on issuer_did + credential_type_id
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<RevocationList(id={self.id}, issuer_did={self.issuer_did}, credential_type_id={self.credential_type_id}, revoked_count={self.revoked_count})>"


class ScheduledRevocation(Base):
    """Model for storing scheduled revocations."""
    __tablename__ = "scheduled_revocations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String, nullable=False, index=True)
    revocation_list_id = Column(String, ForeignKey("revocation_lists.id"), nullable=False, index=True)
    revocation_list_index = Column(Integer, nullable=False)
    issuer_did = Column(String, nullable=False, index=True)
    credential_type_id = Column(String, nullable=False, index=True)
    scheduled_for = Column(DateTime, nullable=False, index=True)  # When to execute the revocation
    executed = Column(Boolean, default=False)  # Whether the revocation has been executed
    executed_at = Column(DateTime, nullable=True)  # When the revocation was executed
    reason = Column(String, nullable=True)  # Reason for revocation
    revocation_metadata = Column(JSON, nullable=True)  # Additional metadata about the scheduled revocation
    created_by = Column(String, nullable=True)  # User ID who scheduled the revocation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with RevocationList
    revocation_list = relationship("RevocationList")

    def __repr__(self):
        return f"<ScheduledRevocation(id={self.id}, credential_id={self.credential_id}, scheduled_for={self.scheduled_for}, executed={self.executed})>"
