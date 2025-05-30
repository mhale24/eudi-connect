"""Notification template system for alerts."""
from datetime import datetime
from enum import Enum
import json
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, validator

from .template_alerts import Alert, AlertType, AlertSeverity


class TemplateFormat(str, Enum):
    """Template format types."""
    HTML = "html"
    PLAIN = "plain"
    SLACK = "slack"
    WEBHOOK_JSON = "webhook_json"


class NotificationTemplate(BaseModel):
    """Notification template configuration."""
    id: str
    merchant_id: str
    name: str
    description: Optional[str] = None
    alert_types: Optional[List[AlertType]] = None
    min_severity: Optional[AlertSeverity] = None
    
    # Template content
    subject_template: Optional[str] = None
    html_template: Optional[str] = None
    plain_template: Optional[str] = None
    slack_template: Optional[str] = None
    webhook_template: Optional[str] = None
    
    # Default templates
    default_subject: str = "[{severity}] {title}"
    default_html: str = """
    <html>
    <body>
        <h1>{title}</h1>
        <p><strong>Alert Details:</strong></p>
        <ul>
            <li><strong>Description:</strong> {description}</li>
            <li><strong>Type:</strong> {alert_type}</li>
            <li><strong>Severity:</strong> {severity}</li>
            <li><strong>Created:</strong> {created_at}</li>
        </ul>
        <p><strong>Metrics:</strong></p>
        <ul>
            <li>Current Value: {metric_value}</li>
            <li>Threshold: {threshold_value}</li>
        </ul>
        {template_info}
        {tag_info}
        <p>
            <a href="https://dashboard.eudi-connect.eu/alerts/{id}">
                View in Dashboard
            </a>
        </p>
    </body>
    </html>
    """
    default_plain: str = """
    Alert: {title}
    
    Description: {description}
    Type: {alert_type}
    Severity: {severity}
    Created: {created_at}
    
    Metrics:
    - Current Value: {metric_value}
    - Threshold: {threshold_value}
    
    {template_info}
    {tag_info}
    
    View in Dashboard: https://dashboard.eudi-connect.eu/alerts/{id}
    """
    default_slack: str = """
    *{title}*
    
    {description}
    
    *Type:* {alert_type}
    *Severity:* {severity}
    *Created:* {created_at}
    
    *Metrics:*
    • Current Value: {metric_value}
    • Threshold: {threshold_value}
    
    {template_info}
    {tag_info}
    
    <https://dashboard.eudi-connect.eu/alerts/{id}|View in Dashboard>
    """
    default_webhook: str = """
    {
        "alert": {
            "id": "{id}",
            "title": "{title}",
            "description": "{description}",
            "type": "{alert_type}",
            "severity": "{severity}",
            "created_at": "{created_at}",
            "metric_value": {metric_value},
            "threshold_value": {threshold_value},
            "template_id": "{template_id}",
            "tag": "{tag}",
            "dashboard_url": "https://dashboard.eudi-connect.eu/alerts/{id}"
        }
    }
    """

    @validator("html_template", "plain_template", "slack_template", "webhook_template", pre=True)
    def validate_templates(cls, v):
        """Validate template syntax."""
        if v is not None:
            try:
                # Test template with dummy data
                test_data = {
                    "id": "test",
                    "title": "Test Alert",
                    "description": "Test Description",
                    "alert_type": "test_type",
                    "severity": "info",
                    "created_at": "2025-01-01T00:00:00Z",
                    "metric_value": 1.0,
                    "threshold_value": 0.5,
                    "template_id": "test_template",
                    "tag": "test_tag",
                    "template_info": "",
                    "tag_info": "",
                }
                v.format(**test_data)
            except KeyError as e:
                raise ValueError(f"Invalid template variable: {e}")
            except Exception as e:
                raise ValueError(f"Invalid template syntax: {e}")
        return v


class TemplateManager:
    """Notification template manager."""

    def __init__(
        self,
        supabase_client,
        merchant_id: str,
    ):
        """Initialize template manager.

        Args:
            supabase_client: Initialized Supabase client
            merchant_id: Current merchant ID
        """
        self.supabase = supabase_client
        self.merchant_id = merchant_id

    def _get_template_info(self, alert: Alert) -> Dict[str, str]:
        """Get formatted template info strings.

        Args:
            alert: Alert to format info for

        Returns:
            Dict with formatted strings
        """
        template_info = {
            "template_info": "",
            "tag_info": "",
        }
        
        if alert.template_id:
            template_info["template_info"] = (
                f"Template ID: {alert.template_id}"
            )
            
        if alert.tag:
            template_info["tag_info"] = f"Tag: {alert.tag}"
            
        return template_info

    def get_templates(
        self,
        alert_type: Optional[AlertType] = None,
        min_severity: Optional[AlertSeverity] = None,
    ) -> List[NotificationTemplate]:
        """Get notification templates.

        Args:
            alert_type: Optional alert type filter
            min_severity: Optional minimum severity filter

        Returns:
            List of templates
        """
        query = self.supabase.table("template_notification_templates").select(
            "*"
        ).eq("merchant_id", self.merchant_id)
        
        if alert_type:
            query = query.contains("alert_types", [alert_type])
        if min_severity:
            query = query.eq("min_severity", min_severity)
            
        result = query.execute()
        if not result.data:
            return []
            
        return [NotificationTemplate(**template) for template in result.data]

    def get_template(
        self,
        template_id: str,
    ) -> Optional[NotificationTemplate]:
        """Get a specific template.

        Args:
            template_id: Template ID

        Returns:
            Template if found, None otherwise
        """
        result = self.supabase.table("template_notification_templates").select(
            "*"
        ).eq("id", template_id).execute()
        
        if not result.data:
            return None
            
        return NotificationTemplate(**result.data[0])

    def create_template(
        self,
        name: str,
        description: Optional[str] = None,
        alert_types: Optional[List[AlertType]] = None,
        min_severity: Optional[AlertSeverity] = None,
        subject_template: Optional[str] = None,
        html_template: Optional[str] = None,
        plain_template: Optional[str] = None,
        slack_template: Optional[str] = None,
        webhook_template: Optional[str] = None,
    ) -> NotificationTemplate:
        """Create a new notification template.

        Args:
            name: Template name
            description: Optional description
            alert_types: Optional alert type filter
            min_severity: Optional minimum severity
            subject_template: Optional subject template
            html_template: Optional HTML template
            plain_template: Optional plain text template
            slack_template: Optional Slack template
            webhook_template: Optional webhook template

        Returns:
            Created template

        Raises:
            ValueError: If template creation fails
        """
        template = NotificationTemplate(
            id=f"template_{datetime.utcnow().isoformat()}",
            merchant_id=self.merchant_id,
            name=name,
            description=description,
            alert_types=alert_types,
            min_severity=min_severity,
            subject_template=subject_template,
            html_template=html_template,
            plain_template=plain_template,
            slack_template=slack_template,
            webhook_template=webhook_template,
        )
        
        result = self.supabase.table("template_notification_templates").insert(
            template.dict()
        ).execute()
        
        if "error" in result:
            raise ValueError(f"Failed to create template: {result['error']}")
            
        return template

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        alert_types: Optional[List[AlertType]] = None,
        min_severity: Optional[AlertSeverity] = None,
        subject_template: Optional[str] = None,
        html_template: Optional[str] = None,
        plain_template: Optional[str] = None,
        slack_template: Optional[str] = None,
        webhook_template: Optional[str] = None,
    ) -> None:
        """Update a notification template.

        Args:
            template_id: Template ID to update
            name: Optional new name
            description: Optional new description
            alert_types: Optional new alert types
            min_severity: Optional new min severity
            subject_template: Optional new subject template
            html_template: Optional new HTML template
            plain_template: Optional new plain text template
            slack_template: Optional new Slack template
            webhook_template: Optional new webhook template

        Raises:
            ValueError: If update fails
        """
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if alert_types is not None:
            updates["alert_types"] = alert_types
        if min_severity is not None:
            updates["min_severity"] = min_severity
        if subject_template is not None:
            updates["subject_template"] = subject_template
        if html_template is not None:
            updates["html_template"] = html_template
        if plain_template is not None:
            updates["plain_template"] = plain_template
        if slack_template is not None:
            updates["slack_template"] = slack_template
        if webhook_template is not None:
            updates["webhook_template"] = webhook_template
            
        if updates:
            result = self.supabase.table("template_notification_templates").update(
                updates
            ).eq("id", template_id).execute()
            
            if "error" in result:
                raise ValueError(f"Failed to update template: {result['error']}")

    def delete_template(self, template_id: str) -> None:
        """Delete a notification template.

        Args:
            template_id: Template ID to delete

        Raises:
            ValueError: If deletion fails
        """
        result = self.supabase.table("template_notification_templates").delete().eq(
            "id", template_id
        ).execute()
        
        if "error" in result:
            raise ValueError(f"Failed to delete template: {result['error']}")

    def render_template(
        self,
        alert: Alert,
        template_format: TemplateFormat,
        template_id: Optional[str] = None,
    ) -> str:
        """Render a notification template.

        Args:
            alert: Alert to render template for
            template_format: Desired template format
            template_id: Optional specific template ID

        Returns:
            Rendered template string

        Raises:
            ValueError: If template rendering fails
        """
        # Get template if specified
        template = None
        if template_id:
            template = self.get_template(template_id)
            
        # Get matching templates
        if not template:
            templates = self.get_templates(
                alert_type=alert.alert_type,
                min_severity=alert.severity,
            )
            if templates:
                template = templates[0]
                
        # Use default template if none found
        if not template:
            template = NotificationTemplate(
                id="default",
                merchant_id=self.merchant_id,
                name="Default Template",
            )
            
        # Get template content
        template_content = None
        if template_format == TemplateFormat.HTML:
            template_content = template.html_template or template.default_html
        elif template_format == TemplateFormat.PLAIN:
            template_content = template.plain_template or template.default_plain
        elif template_format == TemplateFormat.SLACK:
            template_content = template.slack_template or template.default_slack
        elif template_format == TemplateFormat.WEBHOOK_JSON:
            template_content = template.webhook_template or template.default_webhook
            
        if not template_content:
            raise ValueError(f"No template content for format: {template_format}")
            
        # Get template info
        template_info = self._get_template_info(alert)
        
        # Render template
        try:
            return template_content.format(
                id=alert.id,
                title=alert.title,
                description=alert.description,
                alert_type=alert.alert_type,
                severity=alert.severity,
                created_at=alert.created_at.isoformat(),
                metric_value=alert.metric_value,
                threshold_value=alert.threshold_value,
                template_id=alert.template_id or "",
                tag=alert.tag or "",
                **template_info,
            )
        except Exception as e:
            raise ValueError(f"Failed to render template: {e}")
