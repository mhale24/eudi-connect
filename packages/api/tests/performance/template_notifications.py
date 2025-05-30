"""Template alert notification system."""
import asyncio
from datetime import datetime
from enum import Enum
import json
from typing import Dict, List, Optional, Set, Union
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel, EmailStr, HttpUrl

from .template_alerts import Alert, AlertType, AlertSeverity, AlertStatus
from .template_notification_templates import TemplateManager, TemplateFormat


class NotificationChannel(str, Enum):
    """Notification channel type."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"


class NotificationConfig(BaseModel):
    """Notification channel configuration."""
    id: str
    merchant_id: str
    channel: NotificationChannel
    enabled: bool = True
    name: str
    description: Optional[str] = None
    
    # Email specific
    email_recipients: Optional[List[EmailStr]] = None
    email_subject_template: Optional[str] = None
    
    # Webhook specific
    webhook_url: Optional[HttpUrl] = None
    webhook_headers: Optional[Dict[str, str]] = None
    webhook_template: Optional[str] = None
    
    # Slack specific
    slack_webhook_url: Optional[HttpUrl] = None
    slack_channel: Optional[str] = None
    slack_template: Optional[str] = None
    
    # Alert filters
    alert_types: Optional[List[AlertType]] = None
    min_severity: Optional[AlertSeverity] = None
    templates: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class NotificationDeliveryStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class NotificationLog(BaseModel):
    """Notification delivery log."""
    id: str
    merchant_id: str
    channel_id: str
    alert_id: str
    created_at: datetime
    status: NotificationDeliveryStatus
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class NotificationManager:
    """Template alert notification manager."""

    def __init__(
        self,
        supabase_client,
        merchant_id: str,
        smtp_config: Optional[Dict[str, str]] = None,
        template_manager: Optional[TemplateManager] = None,
    ):
        """Initialize notification manager.

        Args:
            supabase_client: Initialized Supabase client
            merchant_id: Current merchant ID
            smtp_config: Optional SMTP configuration
        """
        self.supabase = supabase_client
        self.merchant_id = merchant_id
        self.smtp_config = smtp_config or {}
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize or use provided template manager
        self.template_manager = template_manager or TemplateManager(
            supabase_client=supabase_client,
            merchant_id=merchant_id,
        )

    async def _send_email(
        self,
        config: NotificationConfig,
        alert: Alert,
    ) -> NotificationLog:
        """Send email notification.

        Args:
            config: Notification config
            alert: Alert to notify about

        Returns:
            Notification log entry
        """
        if not config.email_recipients:
            raise ValueError("No email recipients configured")

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg["From"] = self.smtp_config.get("from_email", "alerts@eudi-connect.eu")
            msg["To"] = ", ".join(config.email_recipients)
            
            # Render subject
            subject = self.template_manager.render_template(
                alert=alert,
                template_format=TemplateFormat.PLAIN,
                template_id=config.template_id if hasattr(config, 'template_id') else None,
            )
            msg["Subject"] = subject
            
            # Render plain text and HTML bodies
            plain_body = self.template_manager.render_template(
                alert=alert,
                template_format=TemplateFormat.PLAIN,
                template_id=config.template_id if hasattr(config, 'template_id') else None,
            )
            html_body = self.template_manager.render_template(
                alert=alert,
                template_format=TemplateFormat.HTML,
                template_id=config.template_id if hasattr(config, 'template_id') else None,
            )
            
            # Attach both versions
            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(
                self.smtp_config.get("host", "localhost"),
                self.smtp_config.get("port", 25),
            ) as server:
                if self.smtp_config.get("username"):
                    server.login(
                        self.smtp_config["username"],
                        self.smtp_config["password"],
                    )
                server.send_message(msg)
            
            return NotificationLog(
                id=f"email_{alert.id}_{datetime.utcnow().isoformat()}",
                merchant_id=self.merchant_id,
                channel_id=config.id,
                alert_id=alert.id,
                created_at=datetime.utcnow(),
                status=NotificationDeliveryStatus.DELIVERED,
            )
            
        except Exception as e:
            return NotificationLog(
                id=f"email_{alert.id}_{datetime.utcnow().isoformat()}",
                merchant_id=self.merchant_id,
                channel_id=config.id,
                alert_id=alert.id,
                created_at=datetime.utcnow(),
                status=NotificationDeliveryStatus.FAILED,
                error_message=str(e),
            )

    async def _send_webhook(
        self,
        config: NotificationConfig,
        alert: Alert,
    ) -> NotificationLog:
        """Send webhook notification.

        Args:
            config: Notification config
            alert: Alert to notify about

        Returns:
            Notification log entry
        """
        if not config.webhook_url:
            raise ValueError("No webhook URL configured")

        try:
            # Render webhook payload
            payload = self.template_manager.render_template(
                alert=alert,
                template_format=TemplateFormat.WEBHOOK_JSON,
                template_id=config.template_id if hasattr(config, 'template_id') else None,
            )
            
            # Parse JSON payload
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid webhook template JSON: {e}")
            
            # Send webhook
            headers = config.webhook_headers or {}
            headers["Content-Type"] = "application/json"
            
            async with self.http_client as client:
                response = await client.post(
                    str(config.webhook_url),
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
            
            return NotificationLog(
                id=f"webhook_{alert.id}_{datetime.utcnow().isoformat()}",
                merchant_id=self.merchant_id,
                channel_id=config.id,
                alert_id=alert.id,
                created_at=datetime.utcnow(),
                status=NotificationDeliveryStatus.DELIVERED,
                metadata={"status_code": str(response.status_code)},
            )
            
        except Exception as e:
            return NotificationLog(
                id=f"webhook_{alert.id}_{datetime.utcnow().isoformat()}",
                merchant_id=self.merchant_id,
                channel_id=config.id,
                alert_id=alert.id,
                created_at=datetime.utcnow(),
                status=NotificationDeliveryStatus.FAILED,
                error_message=str(e),
            )

    async def _send_slack(
        self,
        config: NotificationConfig,
        alert: Alert,
    ) -> NotificationLog:
        """Send Slack notification.

        Args:
            config: Notification config
            alert: Alert to notify about

        Returns:
            Notification log entry
        """
        if not config.slack_webhook_url:
            raise ValueError("No Slack webhook URL configured")

        try:
            # Render Slack message
            slack_message = self.template_manager.render_template(
                alert=alert,
                template_format=TemplateFormat.SLACK,
                template_id=config.template_id if hasattr(config, 'template_id') else None,
            )
            
            # Set color based on severity
            color = {
                AlertSeverity.INFO: "#36a64f",  # Green
                AlertSeverity.WARNING: "#ffcc00",  # Yellow
                AlertSeverity.ERROR: "#ff9900",  # Orange
                AlertSeverity.CRITICAL: "#ff0000",  # Red
            }.get(alert.severity, "#cccccc")
            
            # Build message payload
            message = {
                "attachments": [{
                    "color": color,
                    "text": slack_message,
                    "ts": int(alert.created_at.timestamp()),
                }]
            }
            
            # Add channel if specified
            if config.slack_channel:
                message["channel"] = config.slack_channel
            
            # Send to Slack
            async with self.http_client as client:
                response = await client.post(
                    str(config.slack_webhook_url),
                    json=message,
                )
                response.raise_for_status()
            
            return NotificationLog(
                id=f"slack_{alert.id}_{datetime.utcnow().isoformat()}",
                merchant_id=self.merchant_id,
                channel_id=config.id,
                alert_id=alert.id,
                created_at=datetime.utcnow(),
                status=NotificationDeliveryStatus.DELIVERED,
                metadata={"status_code": str(response.status_code)},
            )
            
        except Exception as e:
            return NotificationLog(
                id=f"slack_{alert.id}_{datetime.utcnow().isoformat()}",
                merchant_id=self.merchant_id,
                channel_id=config.id,
                alert_id=alert.id,
                created_at=datetime.utcnow(),
                status=NotificationDeliveryStatus.FAILED,
                error_message=str(e),
            )

    def _should_notify(
        self,
        config: NotificationConfig,
        alert: Alert,
    ) -> bool:
        """Check if notification should be sent.

        Args:
            config: Notification config
            alert: Alert to check

        Returns:
            True if notification should be sent
        """
        if not config.enabled:
            return False
            
        # Check alert type
        if config.alert_types and alert.alert_type not in config.alert_types:
            return False
            
        # Check severity
        if (
            config.min_severity
            and AlertSeverity[alert.severity].value
            < AlertSeverity[config.min_severity].value
        ):
            return False
            
        # Check template
        if (
            config.templates
            and alert.template_id
            and alert.template_id not in config.templates
        ):
            return False
            
        # Check tag
        if config.tags and alert.tag and alert.tag not in config.tags:
            return False
            
        return True

    def get_notification_configs(self) -> List[NotificationConfig]:
        """Get notification configurations.

        Returns:
            List of notification configs
        """
        result = self.supabase.table("template_notification_configs").select(
            "*"
        ).eq("merchant_id", self.merchant_id).execute()
        
        if not result.data:
            return []
            
        return [NotificationConfig(**config) for config in result.data]

    def create_notification_config(
        self,
        channel: NotificationChannel,
        name: str,
        description: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        webhook_headers: Optional[Dict[str, str]] = None,
        slack_webhook_url: Optional[str] = None,
        slack_channel: Optional[str] = None,
        alert_types: Optional[List[AlertType]] = None,
        min_severity: Optional[AlertSeverity] = None,
        templates: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> NotificationConfig:
        """Create notification configuration.

        Args:
            channel: Notification channel
            name: Config name
            description: Optional description
            email_recipients: Email recipients if channel is EMAIL
            webhook_url: Webhook URL if channel is WEBHOOK
            webhook_headers: Optional webhook headers
            slack_webhook_url: Slack webhook URL if channel is SLACK
            slack_channel: Optional Slack channel
            alert_types: Optional alert type filter
            min_severity: Optional minimum severity
            templates: Optional template filter
            tags: Optional tag filter

        Returns:
            Created notification config

        Raises:
            ValueError: If config creation fails
        """
        config = NotificationConfig(
            id=f"notify_{datetime.utcnow().isoformat()}",
            merchant_id=self.merchant_id,
            channel=channel,
            name=name,
            description=description,
            email_recipients=email_recipients,
            webhook_url=webhook_url,
            webhook_headers=webhook_headers,
            slack_webhook_url=slack_webhook_url,
            slack_channel=slack_channel,
            alert_types=alert_types,
            min_severity=min_severity,
            templates=templates,
            tags=tags,
        )
        
        result = self.supabase.table("template_notification_configs").insert(
            config.dict()
        ).execute()
        
        if "error" in result:
            raise ValueError(f"Failed to create config: {result['error']}")
            
        return config

    def update_notification_config(
        self,
        config_id: str,
        enabled: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        webhook_headers: Optional[Dict[str, str]] = None,
        slack_webhook_url: Optional[str] = None,
        slack_channel: Optional[str] = None,
        alert_types: Optional[List[AlertType]] = None,
        min_severity: Optional[AlertSeverity] = None,
        templates: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Update notification configuration.

        Args:
            config_id: Config ID to update
            enabled: Optional enabled state
            name: Optional new name
            description: Optional new description
            email_recipients: Optional new recipients
            webhook_url: Optional new webhook URL
            webhook_headers: Optional new headers
            slack_webhook_url: Optional new Slack webhook
            slack_channel: Optional new Slack channel
            alert_types: Optional new alert types
            min_severity: Optional new min severity
            templates: Optional new templates
            tags: Optional new tags

        Raises:
            ValueError: If update fails
        """
        updates = {}
        if enabled is not None:
            updates["enabled"] = enabled
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if email_recipients is not None:
            updates["email_recipients"] = email_recipients
        if webhook_url is not None:
            updates["webhook_url"] = webhook_url
        if webhook_headers is not None:
            updates["webhook_headers"] = webhook_headers
        if slack_webhook_url is not None:
            updates["slack_webhook_url"] = slack_webhook_url
        if slack_channel is not None:
            updates["slack_channel"] = slack_channel
        if alert_types is not None:
            updates["alert_types"] = alert_types
        if min_severity is not None:
            updates["min_severity"] = min_severity
        if templates is not None:
            updates["templates"] = templates
        if tags is not None:
            updates["tags"] = tags
            
        if updates:
            result = self.supabase.table("template_notification_configs").update(
                updates
            ).eq("id", config_id).execute()
            
            if "error" in result:
                raise ValueError(f"Failed to update config: {result['error']}")

    def delete_notification_config(self, config_id: str) -> None:
        """Delete notification configuration.

        Args:
            config_id: Config ID to delete

        Raises:
            ValueError: If deletion fails
        """
        result = self.supabase.table("template_notification_configs").delete().eq(
            "id", config_id
        ).execute()
        
        if "error" in result:
            raise ValueError(f"Failed to delete config: {result['error']}")

    async def notify(self, alert: Alert) -> List[NotificationLog]:
        """Send notifications for an alert.

        Args:
            alert: Alert to notify about

        Returns:
            List of notification logs
        """
        configs = self.get_notification_configs()
        logs = []
        
        for config in configs:
            if not self._should_notify(config, alert):
                continue
                
            log = None
            if config.channel == NotificationChannel.EMAIL:
                log = await self._send_email(config, alert)
            elif config.channel == NotificationChannel.WEBHOOK:
                log = await self._send_webhook(config, alert)
            elif config.channel == NotificationChannel.SLACK:
                log = await self._send_slack(config, alert)
                
            if log:
                # Save log
                result = self.supabase.table("template_notification_logs").insert(
                    log.dict()
                ).execute()
                
                if "error" not in result:
                    logs.append(log)
                    
        return logs

    def get_notification_logs(
        self,
        alert_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        status: Optional[NotificationDeliveryStatus] = None,
        limit: int = 100,
    ) -> List[NotificationLog]:
        """Get notification delivery logs.

        Args:
            alert_id: Optional alert ID filter
            channel_id: Optional channel ID filter
            status: Optional status filter
            limit: Maximum logs to return

        Returns:
            List of notification logs
        """
        query = self.supabase.table("template_notification_logs").select(
            "*"
        ).eq("merchant_id", self.merchant_id)
        
        if alert_id:
            query = query.eq("alert_id", alert_id)
        if channel_id:
            query = query.eq("channel_id", channel_id)
        if status:
            query = query.eq("status", status)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        if not result.data:
            return []
            
        return [NotificationLog(**log) for log in result.data]
