"""Template usage alert system."""
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import json

from pydantic import BaseModel, Field

from .template_analytics import TemplateAnalytics, TimeRange, EventType


class AlertType(str, Enum):
    """Type of usage alert."""
    USAGE_SPIKE = "usage_spike"  # Sudden increase in usage
    USAGE_DROP = "usage_drop"    # Sudden decrease in usage
    ERROR_RATE = "error_rate"    # High error rate
    PERFORMANCE = "performance"   # Performance degradation
    TAG_TREND = "tag_trend"      # New trending tags
    POPULARITY = "popularity"     # Popularity changes
    VERSION = "version"          # Version-related alerts
    SECURITY = "security"        # Security-related alerts


class AlertSeverity(str, Enum):
    """Alert severity level."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertRule(BaseModel):
    """Alert rule configuration."""
    id: str
    merchant_id: str
    alert_type: AlertType
    severity: AlertSeverity
    threshold: float
    window_minutes: int
    cooldown_minutes: int
    enabled: bool = True
    templates: Optional[List[str]] = None  # Specific templates to monitor
    tags: Optional[List[str]] = None      # Specific tags to monitor
    last_triggered: Optional[datetime] = None
    metadata: Optional[Dict[str, str]] = None


class Alert(BaseModel):
    """Usage alert."""
    id: str
    rule_id: str
    merchant_id: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    title: str
    description: str
    template_id: Optional[str] = None
    tag: Optional[str] = None
    metric_value: float
    threshold_value: float
    metadata: Optional[Dict[str, str]] = None


class AlertManager:
    """Template usage alert manager."""

    def __init__(
        self,
        analytics: TemplateAnalytics,
        supabase_client,
        merchant_id: str,
        notification_manager=None,
    ):
        """Initialize alert manager.

        Args:
            analytics: Template analytics instance
            supabase_client: Initialized Supabase client
            merchant_id: Current merchant ID
        """
        self.analytics = analytics
        self.supabase = supabase_client
        self.merchant_id = merchant_id
        self.notification_manager = notification_manager

    def _get_alert_rules(self) -> List[AlertRule]:
        """Get alert rules for current merchant.

        Returns:
            List of alert rules
        """
        result = self.supabase.table("template_alert_rules").select("*").eq(
            "merchant_id", self.merchant_id
        ).execute()

        if not result.data:
            return []

        return [AlertRule(**rule) for rule in result.data]

    def _create_alert(
        self,
        rule: AlertRule,
        title: str,
        description: str,
        metric_value: float,
        template_id: Optional[str] = None,
        tag: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Alert:
        """Create a new alert.

        Args:
            rule: Triggered alert rule
            title: Alert title
            description: Alert description
            metric_value: Current metric value
            template_id: Optional template ID
            tag: Optional tag
            metadata: Optional metadata

        Returns:
            Created alert

        Raises:
            ValueError: If alert creation fails
        """
        alert = Alert(
            id=f"{rule.id}_{datetime.utcnow().isoformat()}",
            rule_id=rule.id,
            merchant_id=self.merchant_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            title=title,
            description=description,
            template_id=template_id,
            tag=tag,
            metric_value=metric_value,
            threshold_value=rule.threshold,
            metadata=metadata,
        )

        result = self.supabase.table("template_alerts").insert(
            alert.dict()
        ).execute()

        if "error" in result:
            raise ValueError(f"Failed to create alert: {result['error']}")

        return alert

    def _check_usage_spike(self, rule: AlertRule) -> Optional[Alert]:
        """Check for usage spikes.

        Args:
            rule: Alert rule to check

        Returns:
            Alert if triggered, None otherwise
        """
        # Get current and previous window metrics
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=rule.window_minutes)
        prev_start = window_start - timedelta(minutes=rule.window_minutes)

        # Skip if in cooldown
        if (
            rule.last_triggered
            and now - rule.last_triggered
            < timedelta(minutes=rule.cooldown_minutes)
        ):
            return None

        templates_to_check = rule.templates or []
        alerts = []

        for template_id in templates_to_check:
            # Current window
            current = self.analytics.get_metrics(
                template_id=template_id,
                time_range=TimeRange.LAST_24H,  # TODO: Make this configurable
            )

            # Previous window
            previous = self.analytics.get_metrics(
                template_id=template_id,
                time_range=TimeRange.LAST_7D,  # TODO: Make this configurable
            )

            # Calculate usage change
            if previous.total_views > 0:
                change = (
                    (current.total_views - previous.total_views)
                    / previous.total_views
                )

                if change > rule.threshold:
                    alerts.append(
                        self._create_alert(
                            rule=rule,
                            title=f"Usage spike detected for template {template_id}",
                            description=(
                                f"Usage increased by {change:.1%} in the last "
                                f"{rule.window_minutes} minutes"
                            ),
                            metric_value=change,
                            template_id=template_id,
                            metadata={
                                "current_views": str(current.total_views),
                                "previous_views": str(previous.total_views),
                                "window_minutes": str(rule.window_minutes),
                            },
                        )
                    )

        return alerts[0] if alerts else None

    def _check_usage_drop(self, rule: AlertRule) -> Optional[Alert]:
        """Check for usage drops.

        Args:
            rule: Alert rule to check

        Returns:
            Alert if triggered, None otherwise
        """
        # Similar to usage spike but for decreases
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=rule.window_minutes)
        prev_start = window_start - timedelta(minutes=rule.window_minutes)

        if (
            rule.last_triggered
            and now - rule.last_triggered
            < timedelta(minutes=rule.cooldown_minutes)
        ):
            return None

        templates_to_check = rule.templates or []
        alerts = []

        for template_id in templates_to_check:
            current = self.analytics.get_metrics(
                template_id=template_id,
                time_range=TimeRange.LAST_24H,
            )

            previous = self.analytics.get_metrics(
                template_id=template_id,
                time_range=TimeRange.LAST_7D,
            )

            if previous.total_views > 0:
                change = (
                    (previous.total_views - current.total_views)
                    / previous.total_views
                )

                if change > rule.threshold:
                    alerts.append(
                        self._create_alert(
                            rule=rule,
                            title=f"Usage drop detected for template {template_id}",
                            description=(
                                f"Usage decreased by {change:.1%} in the last "
                                f"{rule.window_minutes} minutes"
                            ),
                            metric_value=change,
                            template_id=template_id,
                            metadata={
                                "current_views": str(current.total_views),
                                "previous_views": str(previous.total_views),
                                "window_minutes": str(rule.window_minutes),
                            },
                        )
                    )

        return alerts[0] if alerts else None

    def _check_tag_trend(self, rule: AlertRule) -> Optional[Alert]:
        """Check for tag trends.

        Args:
            rule: Alert rule to check

        Returns:
            Alert if triggered, None otherwise
        """
        if not rule.tags:
            return None

        now = datetime.utcnow()
        if (
            rule.last_triggered
            and now - rule.last_triggered
            < timedelta(minutes=rule.cooldown_minutes)
        ):
            return None

        alerts = []
        for tag in rule.tags:
            # Get current and previous tag usage
            current = self.analytics.get_tag_metrics(
                tag=tag,
                time_range=TimeRange.LAST_24H,
            )

            previous = self.analytics.get_tag_metrics(
                tag=tag,
                time_range=TimeRange.LAST_7D,
            )

            if previous.usage_count > 0:
                change = (
                    (current.usage_count - previous.usage_count)
                    / previous.usage_count
                )

                if change > rule.threshold:
                    alerts.append(
                        self._create_alert(
                            rule=rule,
                            title=f"Tag trend detected: {tag}",
                            description=(
                                f"Tag usage increased by {change:.1%} in the last "
                                f"{rule.window_minutes} minutes"
                            ),
                            metric_value=change,
                            tag=tag,
                            metadata={
                                "current_usage": str(current.usage_count),
                                "previous_usage": str(previous.usage_count),
                                "window_minutes": str(rule.window_minutes),
                            },
                        )
                    )

        return alerts[0] if alerts else None

    async def check_alerts(self) -> List[Alert]:
        """Check all alert rules and generate alerts.

        Returns:
            List of triggered alerts
        """
        rules = self._get_alert_rules()
        alerts = []

        for rule in rules:
            if not rule.enabled:
                continue

            alert = None
            if rule.alert_type == AlertType.USAGE_SPIKE:
                alert = self._check_usage_spike(rule)
            elif rule.alert_type == AlertType.USAGE_DROP:
                alert = self._check_usage_drop(rule)
            elif rule.alert_type == AlertType.TAG_TREND:
                alert = self._check_tag_trend(rule)

            if alert:
                alerts.append(alert)
                # Update last triggered time
                self.supabase.table("template_alert_rules").update({
                    "last_triggered": datetime.utcnow().isoformat(),
                }).eq("id", rule.id).execute()
                
                # Send notifications if configured
                if self.notification_manager:
                    await self.notification_manager.notify(alert)

        return alerts

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
    ) -> List[Alert]:
        """Get active alerts.

        Args:
            severity: Optional severity filter
            alert_type: Optional alert type filter

        Returns:
            List of active alerts
        """
        query = self.supabase.table("template_alerts").select("*").eq(
            "merchant_id", self.merchant_id
        ).eq("status", AlertStatus.ACTIVE)

        if severity:
            query = query.eq("severity", severity)
        if alert_type:
            query = query.eq("alert_type", alert_type)

        result = query.execute()
        if not result.data:
            return []

        return [Alert(**alert) for alert in result.data]

    def update_alert_status(
        self,
        alert_id: str,
        status: AlertStatus,
    ) -> None:
        """Update alert status.

        Args:
            alert_id: Alert ID to update
            status: New status

        Raises:
            ValueError: If update fails
        """
        result = self.supabase.table("template_alerts").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", alert_id).execute()

        if "error" in result:
            raise ValueError(f"Failed to update alert: {result['error']}")

    def create_alert_rule(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        threshold: float,
        window_minutes: int,
        cooldown_minutes: int,
        templates: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> AlertRule:
        """Create a new alert rule.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            threshold: Alert threshold
            window_minutes: Time window in minutes
            cooldown_minutes: Cooldown period in minutes
            templates: Optional list of template IDs to monitor
            tags: Optional list of tags to monitor
            metadata: Optional metadata

        Returns:
            Created alert rule

        Raises:
            ValueError: If rule creation fails
        """
        rule = AlertRule(
            id=f"rule_{datetime.utcnow().isoformat()}",
            merchant_id=self.merchant_id,
            alert_type=alert_type,
            severity=severity,
            threshold=threshold,
            window_minutes=window_minutes,
            cooldown_minutes=cooldown_minutes,
            templates=templates,
            tags=tags,
            metadata=metadata,
        )

        result = self.supabase.table("template_alert_rules").insert(
            rule.dict()
        ).execute()

        if "error" in result:
            raise ValueError(f"Failed to create rule: {result['error']}")

        return rule

    def update_alert_rule(
        self,
        rule_id: str,
        enabled: Optional[bool] = None,
        threshold: Optional[float] = None,
        window_minutes: Optional[int] = None,
        cooldown_minutes: Optional[int] = None,
        templates: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Update an alert rule.

        Args:
            rule_id: Rule ID to update
            enabled: Optional new enabled state
            threshold: Optional new threshold
            window_minutes: Optional new window
            cooldown_minutes: Optional new cooldown
            templates: Optional new template list
            tags: Optional new tag list
            metadata: Optional new metadata

        Raises:
            ValueError: If update fails
        """
        updates = {}
        if enabled is not None:
            updates["enabled"] = enabled
        if threshold is not None:
            updates["threshold"] = threshold
        if window_minutes is not None:
            updates["window_minutes"] = window_minutes
        if cooldown_minutes is not None:
            updates["cooldown_minutes"] = cooldown_minutes
        if templates is not None:
            updates["templates"] = templates
        if tags is not None:
            updates["tags"] = tags
        if metadata is not None:
            updates["metadata"] = metadata

        if updates:
            result = self.supabase.table("template_alert_rules").update(
                updates
            ).eq("id", rule_id).execute()

            if "error" in result:
                raise ValueError(f"Failed to update rule: {result['error']}")

    def delete_alert_rule(self, rule_id: str) -> None:
        """Delete an alert rule.

        Args:
            rule_id: Rule ID to delete

        Raises:
            ValueError: If deletion fails
        """
        result = self.supabase.table("template_alert_rules").delete().eq(
            "id", rule_id
        ).execute()

        if "error" in result:
            raise ValueError(f"Failed to delete rule: {result['error']}")

    def get_alert_rules(
        self,
        alert_type: Optional[AlertType] = None,
        enabled_only: bool = True,
    ) -> List[AlertRule]:
        """Get alert rules.

        Args:
            alert_type: Optional alert type filter
            enabled_only: Whether to return only enabled rules

        Returns:
            List of alert rules
        """
        query = self.supabase.table("template_alert_rules").select("*").eq(
            "merchant_id", self.merchant_id
        )

        if alert_type:
            query = query.eq("alert_type", alert_type)
        if enabled_only:
            query = query.eq("enabled", True)

        result = query.execute()
        if not result.data:
            return []

        return [AlertRule(**rule) for rule in result.data]
