"""
Datetime utilities for tests to ensure consistent timezone handling across all tests.
"""
from datetime import datetime, timedelta, UTC


def naive_utcnow():
    """
    Return a timezone-naive datetime object for the current UTC time.
    This is compatible with PostgreSQL's TIMESTAMP WITHOUT TIME ZONE.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def naive_utc_delta(minutes=0, hours=0, days=0):
    """
    Return a timezone-naive datetime object for UTC time with the specified delta.
    This is compatible with PostgreSQL's TIMESTAMP WITHOUT TIME ZONE.
    """
    return (datetime.now(UTC) + timedelta(minutes=minutes, hours=hours, days=days)).replace(tzinfo=None)
