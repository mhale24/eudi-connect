"""Performance metrics alerting system."""
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert notification channels."""
    CONSOLE = "console"
    SLACK = "slack"
    EMAIL = "email"


class AlertThreshold(BaseModel):
    """Performance metric threshold configuration."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "greater"  # "greater" or "less"
    duration: int = 1  # Number of consecutive violations before alerting
    cooldown: int = 300  # Seconds to wait before re-alerting for same metric


class AlertConfig(BaseSettings):
    """Alert configuration settings."""
    slack_token: Optional[str] = None
    slack_channel: str = "perf-alerts"
    email_recipients: List[str] = []
    thresholds: Dict[str, AlertThreshold] = {
        "p95_latency": AlertThreshold(
            metric_name="p95_latency",
            warning_threshold=700,  # 700ms
            critical_threshold=800,  # 800ms
            comparison="greater",
            duration=2,
            cooldown=300,
        ),
        "error_rate": AlertThreshold(
            metric_name="error_rate",
            warning_threshold=0.01,  # 1%
            critical_threshold=0.05,  # 5%
            comparison="greater",
            duration=1,
            cooldown=300,
        ),
        "cpu_usage": AlertThreshold(
            metric_name="cpu_usage",
            warning_threshold=70,  # 70%
            critical_threshold=85,  # 85%
            comparison="greater",
            duration=3,
            cooldown=300,
        ),
        "memory_usage": AlertThreshold(
            metric_name="memory_usage",
            warning_threshold=512,  # 512MB
            critical_threshold=768,  # 768MB
            comparison="greater",
            duration=3,
            cooldown=300,
        ),
        "throughput": AlertThreshold(
            metric_name="throughput",
            warning_threshold=10,  # 10 RPS
            critical_threshold=5,   # 5 RPS
            comparison="less",
            duration=2,
            cooldown=300,
        ),
    }

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_prefix = "PERF_ALERT_"


class Alert(BaseModel):
    """Performance alert details."""
    id: str
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertHistory:
    """Alert history manager."""

    def __init__(self, history_file: Path = Path("reports/alert_history.json")):
        """Initialize alert history."""
        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.alerts: Dict[str, Alert] = {}
        self._load_history()

    def _load_history(self):
        """Load alert history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    data = json.load(f)
                    self.alerts = {
                        k: Alert(**v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"Error loading alert history: {e}")

    def _save_history(self):
        """Save alert history to file."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(
                    {k: v.model_dump() for k, v in self.alerts.items()},
                    f,
                    default=str,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Error saving alert history: {e}")

    def add_alert(self, alert: Alert):
        """Add new alert to history."""
        self.alerts[alert.id] = alert
        self._save_history()

    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved."""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.utcnow()
            self._save_history()

    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        return [a for a in self.alerts.values() if not a.resolved]

    def get_recent_alerts(
        self,
        hours: int = 24,
        include_resolved: bool = True,
    ) -> List[Alert]:
        """Get alerts from the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            a for a in self.alerts.values()
            if a.timestamp >= cutoff
            and (include_resolved or not a.resolved)
        ]


class AlertManager:
    """Performance alert manager."""

    def __init__(
        self,
        config: Optional[AlertConfig] = None,
        channels: Optional[List[AlertChannel]] = None,
    ):
        """Initialize alert manager."""
        self.config = config or AlertConfig()
        self.channels = channels or [AlertChannel.CONSOLE]
        self.history = AlertHistory()
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Initialize notification channels
        self.slack_client = None
        if AlertChannel.SLACK in self.channels and self.config.slack_token:
            self.slack_client = WebClient(token=self.config.slack_token)

    def check_threshold(
        self,
        metric_name: str,
        current_value: float,
    ) -> Optional[Alert]:
        """Check if metric violates any thresholds."""
        if metric_name not in self.config.thresholds:
            return None

        threshold = self.config.thresholds[metric_name]
        last_alert = self.last_alert_times.get(metric_name)

        # Check cooldown period
        if last_alert and (datetime.utcnow() - last_alert).seconds < threshold.cooldown:
            return None

        # Check thresholds
        if threshold.comparison == "greater":
            if current_value >= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif current_value >= threshold.warning_threshold:
                severity = AlertSeverity.WARNING
                threshold_value = threshold.warning_threshold
            else:
                return None
        else:  # less
            if current_value <= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif current_value <= threshold.warning_threshold:
                severity = AlertSeverity.WARNING
                threshold_value = threshold.warning_threshold
            else:
                return None

        return Alert(
            id=f"{metric_name}_{datetime.utcnow().isoformat()}",
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=self._format_alert_message(
                metric_name,
                current_value,
                threshold_value,
                severity,
            ),
        )

    def _format_alert_message(
        self,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        severity: AlertSeverity,
    ) -> str:
        """Format alert message."""
        return (
            f"[{severity.upper()}] {metric_name} alert:\n"
            f"Current value: {current_value:.2f}\n"
            f"Threshold: {threshold_value:.2f}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    async def send_alert(self, alert: Alert):
        """Send alert through configured channels."""
        self.last_alert_times[alert.metric_name] = datetime.utcnow()
        self.history.add_alert(alert)

        for channel in self.channels:
            try:
                if channel == AlertChannel.CONSOLE:
                    logger.warning(alert.message)

                elif channel == AlertChannel.SLACK and self.slack_client:
                    color = {
                        AlertSeverity.INFO: "#36a64f",
                        AlertSeverity.WARNING: "#ff9900",
                        AlertSeverity.CRITICAL: "#dc3545",
                    }[alert.severity]

                    await self.slack_client.chat_postMessage(
                        channel=self.config.slack_channel,
                        attachments=[{
                            "color": color,
                            "title": f"Performance Alert: {alert.metric_name}",
                            "text": alert.message,
                            "fields": [
                                {
                                    "title": "Severity",
                                    "value": alert.severity,
                                    "short": True,
                                },
                                {
                                    "title": "Value",
                                    "value": f"{alert.current_value:.2f}",
                                    "short": True,
                                },
                            ],
                        }],
                    )

                elif channel == AlertChannel.EMAIL:
                    # Implement email notifications here
                    pass

            except Exception as e:
                logger.error(f"Error sending alert via {channel}: {e}")

    def check_metrics(self, metrics: Dict[str, float]):
        """Check multiple metrics against thresholds."""
        alerts = []
        for metric_name, value in metrics.items():
            if alert := self.check_threshold(metric_name, value):
                alerts.append(alert)
        return alerts
