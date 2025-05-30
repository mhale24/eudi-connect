from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import MetaData, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Mapped, mapped_column

class BaseModelMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),  # Explicitly use timezone-naive timestamps
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # Convert to naive datetime
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),  # Explicitly use timezone-naive timestamps
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),  # Convert to naive datetime
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # Convert to naive datetime
    )

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Define metadata at the module level
metadata = MetaData(naming_convention=convention)

Base = declarative_base(metadata=metadata)
