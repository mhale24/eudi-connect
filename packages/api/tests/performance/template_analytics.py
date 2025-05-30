"""Template analytics system for tracking usage and generating insights."""
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter, defaultdict

import numpy as np
from pydantic import BaseModel, Field

from .template_config import TemplateConfig
from .template_presets import TemplatePreset


class EventType(str, Enum):
    """Type of template event."""
    VIEW = "view"
    EDIT = "edit"
    EXPORT = "export"
    SHARE = "share"
    FAVORITE = "favorite"
    COPY = "copy"
    DELETE = "delete"


class TemplateEvent(BaseModel):
    """Record of a template event."""
    id: str
    template_id: str
    merchant_id: str
    event_type: EventType
    timestamp: datetime
    metadata: Optional[Dict[str, str]] = None
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None


class TemplateMetrics(BaseModel):
    """Analytics metrics for a template."""
    total_views: int = 0
    unique_views: int = 0
    total_exports: int = 0
    total_shares: int = 0
    favorites: int = 0
    copies: int = 0
    avg_view_duration_ms: Optional[float] = None
    top_merchants: List[Tuple[str, int]] = Field(default_factory=list)
    popular_tags: List[Tuple[str, int]] = Field(default_factory=list)
    trend_score: float = 0.0


class TimeRange(str, Enum):
    """Time range for analytics."""
    LAST_24H = "24h"
    LAST_7D = "7d"
    LAST_30D = "30d"
    LAST_90D = "90d"
    ALL_TIME = "all"


class TemplateAnalytics:
    """Template analytics system."""

    def __init__(self, supabase_client):
        """Initialize analytics.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client

    def record_event(
        self,
        template_id: str,
        merchant_id: str,
        event_type: EventType,
        metadata: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """Record a template event.

        Args:
            template_id: Template ID
            merchant_id: Merchant ID
            event_type: Type of event
            metadata: Optional event metadata
            session_id: Optional session ID for tracking view duration
            duration_ms: Optional duration in milliseconds

        Raises:
            ValueError: If event recording fails
        """
        event = TemplateEvent(
            id=f"{template_id}_{merchant_id}_{datetime.utcnow().isoformat()}",
            template_id=template_id,
            merchant_id=merchant_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            metadata=metadata,
            session_id=session_id,
            duration_ms=duration_ms,
        )

        result = self.supabase.table("template_events").insert(
            event.dict()
        ).execute()

        if "error" in result:
            raise ValueError(f"Failed to record event: {result['error']}")

    def _get_time_range_start(self, time_range: TimeRange) -> datetime:
        """Get start datetime for time range.

        Args:
            time_range: Time range enum

        Returns:
            Start datetime
        """
        now = datetime.utcnow()
        if time_range == TimeRange.LAST_24H:
            return now - timedelta(days=1)
        elif time_range == TimeRange.LAST_7D:
            return now - timedelta(days=7)
        elif time_range == TimeRange.LAST_30D:
            return now - timedelta(days=30)
        elif time_range == TimeRange.LAST_90D:
            return now - timedelta(days=90)
        else:  # ALL_TIME
            return datetime.min

    def get_metrics(
        self,
        template_id: str,
        time_range: TimeRange = TimeRange.LAST_30D,
    ) -> TemplateMetrics:
        """Get analytics metrics for a template.

        Args:
            template_id: Template ID
            time_range: Time range to analyze

        Returns:
            Template metrics

        Raises:
            ValueError: If template not found
        """
        start_time = self._get_time_range_start(time_range)

        # Get events in time range
        result = self.supabase.table("template_events").select("*").eq(
            "template_id", template_id
        ).gte("timestamp", start_time.isoformat()).execute()

        if not result.data:
            return TemplateMetrics()

        events = [TemplateEvent(**e) for e in result.data]

        # Calculate metrics
        metrics = TemplateMetrics()

        # Views
        views = [e for e in events if e.event_type == EventType.VIEW]
        metrics.total_views = len(views)
        metrics.unique_views = len({e.merchant_id for e in views})

        # View duration
        durations = [e.duration_ms for e in views if e.duration_ms is not None]
        if durations:
            metrics.avg_view_duration_ms = sum(durations) / len(durations)

        # Other events
        metrics.total_exports = len(
            [e for e in events if e.event_type == EventType.EXPORT]
        )
        metrics.total_shares = len(
            [e for e in events if e.event_type == EventType.SHARE]
        )
        metrics.favorites = len(
            [e for e in events if e.event_type == EventType.FAVORITE]
        )
        metrics.copies = len([e for e in events if e.event_type == EventType.COPY])

        # Top merchants
        merchant_counts = Counter(e.merchant_id for e in events)
        metrics.top_merchants = merchant_counts.most_common(5)

        # Popular tags
        tags = []
        for e in events:
            if e.metadata and "tags" in e.metadata:
                tags.extend(e.metadata["tags"].split(","))
        metrics.popular_tags = Counter(tags).most_common(5)

        # Trend score (weighted sum of recent events)
        weights = {
            EventType.VIEW: 1,
            EventType.EXPORT: 3,
            EventType.SHARE: 4,
            EventType.FAVORITE: 5,
            EventType.COPY: 2,
        }

        now = datetime.utcnow()
        trend_score = 0.0
        for event in events:
            # More recent events have higher weight
            days_old = (now - event.timestamp).days
            time_weight = np.exp(-days_old / 30)  # Exponential decay
            event_weight = weights.get(event.event_type, 1)
            trend_score += time_weight * event_weight

        metrics.trend_score = trend_score

        return metrics

    def get_merchant_usage(
        self,
        merchant_id: str,
        time_range: TimeRange = TimeRange.LAST_30D,
    ) -> Dict[str, TemplateMetrics]:
        """Get template usage metrics for a merchant.

        Args:
            merchant_id: Merchant ID
            time_range: Time range to analyze

        Returns:
            Dict of template ID to metrics
        """
        start_time = self._get_time_range_start(time_range)

        # Get merchant's events
        result = self.supabase.table("template_events").select("*").eq(
            "merchant_id", merchant_id
        ).gte("timestamp", start_time.isoformat()).execute()

        if not result.data:
            return {}

        events = [TemplateEvent(**e) for e in result.data]

        # Group events by template
        template_events = defaultdict(list)
        for event in events:
            template_events[event.template_id].append(event)

        # Calculate metrics for each template
        metrics = {}
        for template_id, template_events in template_events.items():
            m = TemplateMetrics()

            # Views
            views = [e for e in template_events if e.event_type == EventType.VIEW]
            m.total_views = len(views)
            m.unique_views = 1  # Single merchant

            # View duration
            durations = [e.duration_ms for e in views if e.duration_ms is not None]
            if durations:
                m.avg_view_duration_ms = sum(durations) / len(durations)

            # Other events
            m.total_exports = len(
                [e for e in template_events if e.event_type == EventType.EXPORT]
            )
            m.total_shares = len(
                [e for e in template_events if e.event_type == EventType.SHARE]
            )
            m.favorites = len(
                [e for e in template_events if e.event_type == EventType.FAVORITE]
            )
            m.copies = len(
                [e for e in template_events if e.event_type == EventType.COPY]
            )

            metrics[template_id] = m

        return metrics

    def get_trending_templates(
        self,
        limit: int = 10,
        time_range: TimeRange = TimeRange.LAST_7D,
    ) -> List[Tuple[str, float]]:
        """Get trending templates sorted by trend score.

        Args:
            limit: Maximum templates to return
            time_range: Time range to analyze

        Returns:
            List of (template_id, trend_score) tuples
        """
        start_time = self._get_time_range_start(time_range)

        # Get recent events
        result = self.supabase.table("template_events").select("*").gte(
            "timestamp", start_time.isoformat()
        ).execute()

        if not result.data:
            return []

        events = [TemplateEvent(**e) for e in result.data]

        # Calculate trend scores
        template_scores = defaultdict(float)
        weights = {
            EventType.VIEW: 1,
            EventType.EXPORT: 3,
            EventType.SHARE: 4,
            EventType.FAVORITE: 5,
            EventType.COPY: 2,
        }

        now = datetime.utcnow()
        for event in events:
            days_old = (now - event.timestamp).days
            time_weight = np.exp(-days_old / 7)  # Faster decay for trending
            event_weight = weights.get(event.event_type, 1)
            template_scores[event.template_id] += time_weight * event_weight

        # Sort by score
        trending = sorted(
            template_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return trending[:limit]
