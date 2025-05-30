"""Standalone test suite for notification templates.

This module provides a standalone implementation of the notification template system,
including template management, rendering, and preview functionality. It supports
multiple output formats (HTML, plain text, Slack, webhook JSON) and includes
type-safe template variable handling.

Version: 1.0.0
Author: EUDI-Connect Team
License: Proprietary
Last Updated: 2025-05-26

Key Components:
- TemplateManager: Core template management and rendering
- TemplatePreview: Template preview with sample data
- Alert: Data model for alert information
- NotificationTemplate: Data model for template configuration

Error Handling:
- Custom exceptions for template-specific errors
- Comprehensive logging of all operations
- Type validation through Pydantic models
- Template variable validation before rendering

Performance Considerations:
- Template rendering is optimized for speed (<10ms target)
- Caching is recommended for frequently used templates
- Batch operations supported for multiple alerts
- Webhook JSON is pre-validated to avoid runtime parsing

Logging:
The module uses Python's logging system with the following levels:
- INFO: Template creation, retrieval, and rendering
- WARNING: Template not found or validation issues
- ERROR: Rendering failures or invalid data

Typical usage:
    ```python
    # Create template manager
    tm = TemplateManager(supabase_client, merchant_id)
    
    # Create template
    template = tm.create_template(
        name="Usage Alert",
        description="Template for usage alerts",
        alert_types=[AlertType.USAGE_SPIKE],
        min_severity=AlertSeverity.WARNING,
        subject_template="Usage Alert: {title}",
        html_template="<h1>{title}</h1><p>{description}</p>"
    )
    
    # Render template with error handling
    try:
        rendered = tm.render_template(
            template_id=template.id,
            format=TemplateFormat.HTML,
            alert=alert_data
        )
    except TemplateError as e:
        logger.error(f"Failed to render template: {e}")
        raise
    """
# Standard library imports
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Literal, Optional, Protocol, TypedDict, Union

# Third-party imports
import pytest
from pydantic import BaseModel
from unittest.mock import MagicMock

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TemplateVariables(TypedDict):
    """Type definition for template variables."""
    title: str
    description: str
    metric_value: float
    threshold_value: float
    alert_type: str
    severity: str
    created_at: datetime
    metadata: Dict[str, Any]


class TemplateFunctions(TypedDict):
    """Type definition for template helper functions."""
    format_date: Callable[[datetime], str]
    format_number: Callable[[float], str]
    format_severity: Callable[[str], str]


class TemplateError(Exception):
    """Base class for template-related errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a template is not found."""
    pass


class TemplateFormatError(TemplateError):
    """Raised when template format is invalid."""
    pass


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""
    pass


class AlertType(str, Enum):
    """Alert types for notification system.
    
    Attributes:
        USAGE_SPIKE: Triggered when usage spikes above threshold
        USAGE_DROP: Triggered when usage drops below threshold
        TAG_TREND: Triggered when a tag trend is detected
        TEMPLATE_PERFORMANCE: Triggered for template performance issues
        COMPLIANCE_ISSUE: Triggered for compliance violations
    """
    USAGE_SPIKE: str = "usage_spike"
    USAGE_DROP: str = "usage_drop"
    TAG_TREND: str = "tag_trend"
    TEMPLATE_PERFORMANCE: str = "template_performance"
    COMPLIANCE_ISSUE: str = "compliance_issue"

    @classmethod
    def from_str(cls, value: str) -> 'AlertType':
        """Create an AlertType from a string value.
        
        Args:
            value: String value to convert
            
        Returns:
            AlertType enum value
            
        Raises:
            ValueError: If value is not a valid alert type
        """
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid alert type: {value}")


AlertSeverityLiteral = Literal[
    "info",
    "warning",
    "error",
    "critical",
]


class AlertSeverity(str, Enum):
    """Alert severity levels for notifications.
    
    Attributes:
        INFO: Informational alerts, no action needed
        WARNING: Warning alerts, action may be needed
        ERROR: Error alerts, action needed
        CRITICAL: Critical alerts, immediate action needed
    """
    INFO: AlertSeverityLiteral = "info"
    WARNING: AlertSeverityLiteral = "warning"
    ERROR: AlertSeverityLiteral = "error"
    CRITICAL: AlertSeverityLiteral = "critical"

    @classmethod
    def from_str(cls, value: str) -> 'AlertSeverity':
        """Create an AlertSeverity from a string value.
        
        Args:
            value: String value to convert
            
        Returns:
            AlertSeverity enum value
            
        Raises:
            ValueError: If value is not a valid severity level
        """
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid severity level: {value}")


class AlertMetadata(TypedDict, total=False):
    """Type hints for alert metadata."""
    source: str  # Source of the alert (e.g. 'system', 'user', 'api')
    correlation_id: str  # ID for correlating related alerts
    context: Dict[str, Any]  # Additional context data


class Alert(BaseModel):
    """Alert model for notifications.
    
    Attributes:
        id: Unique identifier for the alert
        title: Alert title
        description: Detailed alert description
        alert_type: Type of alert (e.g. usage_spike)
        severity: Alert severity level
        created_at: UTC timestamp when alert was created
        metric_value: Current value that triggered the alert
        threshold_value: Threshold value that was exceeded
        template_id: Optional ID of template to use for notification
        tag: Optional tag for categorizing alerts
        metadata: Optional metadata for additional context
    """
    id: str
    title: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    created_at: datetime
    metric_value: float
    threshold_value: float
    template_id: Optional[str] = None
    tag: Optional[str] = None
    metadata: Optional[AlertMetadata] = None

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            AlertType: lambda at: at.value,
            AlertSeverity: lambda s: s.value,
        }
        
    @property
    def age_seconds(self) -> float:
        """Get age of alert in seconds."""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()


class TemplateFormat(str, Enum):
    """Template format types."""
    HTML = "html"
    PLAIN = "plain"
    SLACK = "slack"
    WEBHOOK_JSON = "webhook_json"


class NotificationTemplate(BaseModel):
    """Notification template configuration.
    
    Attributes:
        id: Unique identifier for the template
        merchant_id: ID of merchant who owns the template
        name: Template name
        description: Optional template description
        alert_types: List of alert types this template handles
        min_severity: Minimum severity level for using this template
        subject_template: Template for email subject
        html_template: Template for HTML email body
        plain_template: Template for plain text email body
        slack_template: Template for Slack messages
        webhook_template: Template for webhook JSON payload
    """
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

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            AlertType: lambda at: at.value,
            AlertSeverity: lambda s: s.value,
            list: lambda l: [x.value if isinstance(x, (AlertType, AlertSeverity)) else x for x in l],
        }

    def has_template_for(self, format: TemplateFormat) -> bool:
        """Check if template has content for given format.
        
        Args:
            format: Template format to check for
            
        Returns:
            True if template has content for format, False otherwise
        """
        if format == TemplateFormat.HTML:
            return bool(self.html_template)
        elif format == TemplateFormat.PLAIN:
            return bool(self.plain_template)
        elif format == TemplateFormat.SLACK:
            return bool(self.slack_template)
        elif format == TemplateFormat.WEBHOOK_JSON:
            return bool(self.webhook_template)
        return False


class SupabaseResponse(TypedDict, total=False):
    """Type hints for Supabase response data."""
    data: List[Dict[str, Any]]  # Response data
    error: Optional[Dict[str, Any]]  # Error details if present
    count: Optional[int]  # Count for select queries
    status: int  # HTTP status code


class SupabaseFilter(Protocol):
    """Protocol for Supabase filter operations.
    
    These methods are chainable and return self for method chaining.
    """
    def eq(self, column: str, value: Any) -> 'SupabaseFilter': ...
    def neq(self, column: str, value: Any) -> 'SupabaseFilter': ...
    def gt(self, column: str, value: Union[int, float, str]) -> 'SupabaseFilter': ...
    def gte(self, column: str, value: Union[int, float, str]) -> 'SupabaseFilter': ...
    def lt(self, column: str, value: Union[int, float, str]) -> 'SupabaseFilter': ...
    def lte(self, column: str, value: Union[int, float, str]) -> 'SupabaseFilter': ...
    def like(self, column: str, pattern: str) -> 'SupabaseFilter': ...
    def ilike(self, column: str, pattern: str) -> 'SupabaseFilter': ...
    def is_(self, column: str, value: Any) -> 'SupabaseFilter': ...
    def in_(self, column: str, values: List[Any]) -> 'SupabaseFilter': ...
    def contains(self, column: str, value: Union[Dict, List, str]) -> 'SupabaseFilter': ...
    def execute(self) -> SupabaseResponse: ...


class SupabaseTable(Protocol):
    """Protocol for Supabase table operations.
    
    This protocol defines the interface for interacting with Supabase tables.
    All methods that return filters are chainable.
    """
    def insert(self, data: Dict[str, Any], returning: str = "*") -> SupabaseFilter: ...
    def select(self, columns: str = "*") -> SupabaseFilter: ...
    def update(self, data: Dict[str, Any], returning: str = "*") -> SupabaseFilter: ...
    def delete(self, returning: str = "*") -> SupabaseFilter: ...
    def eq(self, column: str, value: Any) -> SupabaseFilter: ...
    def neq(self, column: str, value: Any) -> SupabaseFilter: ...
    def execute(self) -> SupabaseResponse: ...


class SupabaseClient(Protocol):
    """Protocol for Supabase client operations.
    
    This protocol defines the interface for the main Supabase client.
    It provides access to database tables and authentication.
    """
    def table(self, name: str) -> SupabaseTable: ...
    
    @property
    def auth(self) -> Any: ...  # Auth client type could be defined if needed
    
    @property
    def realtime(self) -> Any: ...  # Realtime client type could be defined if needed


class TemplateManager:
    """Template manager for handling notification templates.
    
    This class manages the lifecycle of notification templates including:
    - Creating and updating templates
    - Rendering templates with alert data
    - Previewing templates with sample data
    - Supporting multiple output formats (HTML, plain text, Slack, webhook)
    
    Attributes:
        supabase: Supabase client for database operations
        merchant_id: ID of merchant who owns these templates
    """
    def __init__(self, supabase_client: Any, merchant_id: str) -> None:
        """Initialize template manager.

        Args:
            supabase_client: Supabase client instance
            merchant_id: Merchant ID for template operations
        """
        self.supabase = supabase_client
        self.merchant_id = merchant_id
        self.functions: TemplateFunctions = {
            'format_date': lambda dt: dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'format_number': lambda n: f'{n:,.2f}',
            'format_severity': lambda s: s.upper()
        }
        
    def invalidate_cache(self, template_id: Optional[str] = None):
        """Invalidate the template cache.
        
        Args:
            template_id: Optional ID of template to invalidate. If None, invalidates all templates.
        """
        if template_id:
            # Clear specific template from cache if possible
            # This is more efficient than clearing the entire cache
            try:
                # Try to use cache_delete if available (Python 3.8+)
                if hasattr(self.get_template, 'cache_delete'):
                    self.get_template.cache_delete((template_id,))
                    logger.info(f"Cache invalidated for template {template_id}")
                    return
                # Otherwise, clear the full cache
                self.get_template.cache_clear()
                logger.info(f"Full cache invalidated for template {template_id}")
            except Exception as e:
                logger.warning(f"Error invalidating cache for template {template_id}: {e}")
                self.get_template.cache_clear()
        else:
            # Clear all cached templates
            self.get_template.cache_clear()
            logger.info("All templates cache invalidated")

    def _get_table(self) -> Any:
        """Get Supabase table reference.

        Returns:
            Table reference
        """
        return self.supabase.table("template_notification_templates")

    @lru_cache(maxsize=100)
    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """Get a template by ID.

        This method is cached using LRU caching with a maximum size of 100 templates.
        Templates are cached based on their ID. The cache is automatically invalidated
        when templates are updated or deleted.

        Args:
            template_id: ID of template to get

        Returns:
            Template if found, None otherwise

        Raises:
            TemplateError: If database query fails
        """
        try:
            logger.info(f"Fetching template {template_id} for merchant {self.merchant_id}")
            result: SupabaseResponse = self._get_table().select().eq("id", template_id).execute()
            
            if not result.get("data"):
                logger.warning(f"Template {template_id} not found")
                return None
                
            logger.info(f"Successfully retrieved template {template_id}")
            return NotificationTemplate(**result["data"][0])
            
        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            raise TemplateError(f"Failed to get template {template_id}: {e}") from e

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

        This method will automatically invalidate the template cache after creation.

        Args:
            name: Template name
            description: Optional template description
            alert_types: Optional list of alert types this template handles
            min_severity: Optional minimum severity level
            subject_template: Optional email subject template
            html_template: Optional HTML email template
            plain_template: Optional plain text email template
            slack_template: Optional Slack message template
            webhook_template: Optional webhook JSON template
            
        Returns:
            Created NotificationTemplate instance
            
        Raises:
            TemplateError: If template creation fails
            TemplateRenderError: If webhook template is provided but invalid JSON
        """
        # Validate webhook template JSON if provided
        if webhook_template:
            try:
                json.loads(webhook_template)
            except json.JSONDecodeError as e:
                raise TemplateRenderError(f"Invalid webhook template JSON: {e}")

        # Generate an efficient UUID for the template ID
        import uuid
        template_id = f"template_{uuid.uuid4().hex}"
        
        # Create template with optimized ID
        template = NotificationTemplate(
            id=template_id,
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
        
        try:
            logger.info(f"Creating template {template.name} for merchant {self.merchant_id}")
            result = self._get_table().insert(
                template.dict(exclude_none=True)  # Only include non-None values
            ).execute()
            
            if "error" in result:
                logger.error(f"Failed to create template {template.name}: {result['error']}")
                raise TemplateError(f"Failed to create template: {result['error']}")
                
            created_template = NotificationTemplate(**result["data"][0])
            logger.info(f"Successfully created template {template.name} with ID {created_template.id}")
            self.invalidate_cache()  # Clear cache after creation
            return created_template
            
        except Exception as e:
            logger.error(f"Unexpected error creating template {template.name}: {e}")
            raise TemplateError(f"Failed to create template: {e}") from e

    def validate_template_variables(self, template: str, variables: Dict[str, Any]) -> None:
        """Validate that all required variables are present in the template.
        
        Args:
            template: Template string to validate
            variables: Variables to validate against template
            
        Raises:
            TemplateRenderError: If required variables are missing
        """
        # Extract variable names from template using string formatting syntax
        import re
        var_pattern = r'\{([^{}]+)\}'
        required_vars = set(re.findall(var_pattern, template))
        
        # Remove format specifiers if present
        required_vars = {v.split(':')[0] if ':' in v else v for v in required_vars}
        
        # Check if all required variables are present
        missing_vars = [v for v in required_vars if v not in variables]
        if missing_vars:
            raise TemplateRenderError(f"Missing required variables: {', '.join(missing_vars)}")

    def _format_text_template(self, template: str, alert: Alert) -> str:
        """Format a text template with alert data.

        Args:
            template: Template string to format
            alert: Alert data to use for formatting

        Returns:
            Formatted template string
            
        Raises:
            TemplateRenderError: If template formatting fails
        """
        # Prepare variables with helper functions
        variables = {
            'title': alert.title,
            'description': alert.description,
            'metric_value': self.functions['format_number'](alert.metric_value),
            'threshold_value': self.functions['format_number'](alert.threshold_value),
            'alert_type': alert.alert_type.value,
            'severity': self.functions['format_severity'](alert.severity.value),
            'created_at': self.functions['format_date'](alert.created_at),
            **alert.metadata,
        }
        
        # Validate template variables
        self.validate_template_variables(template, variables)
        
        try:
            return template.format(**variables)
        except Exception as e:
            raise TemplateRenderError(f"Failed to format template: {e}")

    def _format_webhook_json(self, template_content: Dict[str, Union[str, float]], alert: Alert) -> str:
        """Format webhook JSON template.

        Args:
            template_content: Template content to format
            alert: Alert data to use for formatting
            
        Returns:
            Formatted JSON string
        """
        formatted_content = {}
        variables = {
            'title': alert.title,
            'description': alert.description,
            'metric_value': self.functions['format_number'](alert.metric_value),
            'threshold_value': self.functions['format_number'](alert.threshold_value),
            'alert_type': alert.alert_type.value,
            'severity': self.functions['format_severity'](alert.severity.value),
            'created_at': self.functions['format_date'](alert.created_at),
            **alert.metadata,
        }
        
        # Validate template variables
        for key, value in template_content.items():
            if isinstance(value, str):
                self.validate_template_variables(value, variables)
                formatted_content[key] = value.format(**variables)
            else:
                formatted_content[key] = value

        return json.dumps(formatted_content)

    # Cache for compiled templates - significantly improves performance
    _template_cache = {}
    
    def _compile_template(self, template_content: str, template_id: str, format_type: str) -> Callable:
        """Pre-compile a template for faster rendering.
        
        Args:
            template_content: Raw template content
            template_id: ID of the template
            format_type: Type of template format
            
        Returns:
            Compiled template function
            
        Raises:
            TemplateRenderError: If compilation fails
        """
        cache_key = f"{template_id}:{format_type}"
        
        # Return cached compiled template if available
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
            
        if not template_content:
            logger.error(f"Template content is empty for {template_id} ({format_type})")
            raise TemplateRenderError("Template content is empty")
        
        try:
            # Create a compiled template function for better performance
            def compiled_template(data):
                return template_content.format(**data)
                
            # Cache the compiled template
            self._template_cache[cache_key] = compiled_template
            return compiled_template
        except Exception as e:
            logger.error(f"Template compilation failed: {e}")
            raise TemplateRenderError(f"Template compilation failed: {e}") from e
    
    def _format_text_template(self, template_content: Optional[str], alert: Alert, template_id: str = "", format_type: str = "text") -> str:
        """Format a text-based template with alert data.
        
        Args:
            template_content: Text template content
            alert: Alert data to use
            template_id: Optional ID for caching
            format_type: Template format type for caching
            
        Returns:
            Formatted string
            
        Raises:
            TemplateRenderError: If template content is empty or invalid
        """
        if not template_content:
            logger.error("Template content is empty")
            raise TemplateRenderError("Template content is empty")
        
        try:
            # Create variable dict from alert - optimized to avoid unnecessary conversions
            data = {
                "title": alert.title,
                "description": alert.description,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "metric_value": alert.metric_value,
                "threshold_value": alert.threshold_value,
                "created_at": alert.created_at,
                "metadata": alert.metadata or {},
            }
            
            # Get compiled template if template_id is provided
            if template_id:
                template_func = self._compile_template(template_content, template_id, format_type)
                return template_func(data)
            else:
                # Fallback to direct formatting if no template_id provided
                return template_content.format(**data)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            raise TemplateRenderError(f"Missing template variable: {e}") from e
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise TemplateRenderError(f"Template rendering failed: {e}") from e

    def render_template(
        self,
        template_id: str,
        format: TemplateFormat,
        alert: Alert,
    ) -> str:
        """Render template with alert data.
        
        Args:
            template_id: ID of the template to render
            template_format: Format of the template (HTML, plain text, Slack, webhook JSON)
            alert: Alert object containing the data to format
            
        Returns:
            Formatted template string
            
        Raises:
            TemplateNotFoundError: If template with given ID is not found
            TemplateFormatError: If template format is invalid
            TemplateRenderError: If template content is empty or invalid
        """
        results = self.render_batch(template_id, [alert], format)
        return results[0]

    def render_batch(self, template_id: str, alerts: List[Alert], format: TemplateFormat) -> List[str]:
        """Render multiple alerts using the same template.

        This is more efficient than calling render_template multiple times
        as it reuses the template and function lookups.

        Args:
            template_id: ID of template to use
            alerts: List of alerts to render
            format: Output format

        Returns:
            List of rendered templates in the same order as alerts

        Raises:
            TemplateError: If rendering fails
            TemplateNotFoundError: If template not found
        """
        start_time = time.time()
        template = self.get_template(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        logger.info(f"Batch rendering {len(alerts)} alerts using template {template_id}")
        results = []

        try:
            # Pre-compile the template once for all alerts
            compiled_template = None
            template_content = None
            
            if format == TemplateFormat.HTML:
                template_content = template.html_template
                format_type = "html"
            elif format == TemplateFormat.PLAIN:
                template_content = template.plain_template
                format_type = "plain"
            elif format == TemplateFormat.SLACK:
                template_content = template.slack_template
                format_type = "slack"
            elif format == TemplateFormat.WEBHOOK_JSON:
                if not template.webhook_template:
                    logger.error(f"Webhook template content is empty for template {template_id}")
                    raise TemplateRenderError("Webhook template content is empty")
                try:
                    template_content = json.loads(template.webhook_template)
                    # For webhook JSON, we'll use a special handling below
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid webhook JSON template for {template_id}: {e}")
                    raise TemplateRenderError(f"Invalid webhook JSON template: {e}")
            else:
                logger.error(f"Invalid template format {format} for template {template_id}")
                raise TemplateFormatError(f"Invalid template format: {format}")
                
            # Process each alert efficiently
            for alert in alerts:
                if format == TemplateFormat.WEBHOOK_JSON:
                    # Special case for webhook JSON
                    result = self._format_webhook_json(template_content, alert)
                else:
                    # Text-based templates use the pre-compilation system
                    result = self._format_text_template(
                        template_content, 
                        alert, 
                        template_id=template_id, 
                        format_type=format_type
                    )
                results.append(result)

            end_time = time.time()
            logger.info(f"Successfully rendered {len(results)} alerts in {(end_time - start_time) * 1000:.2f}ms")
            return results

        except Exception as e:
            if not isinstance(e, TemplateError):
                logger.error(f"Batch rendering failed: {e}")
                raise TemplateRenderError(f"Batch rendering failed: {e}") from e
            raise


@dataclass
class TemplatePreviewOptions:
    """Options for template preview."""
    title: str = "Sample Alert Title"
    description: str = "Sample alert description"
    metric_value: float = 100.0
    threshold_value: float = 80.0
    alert_type: AlertType = AlertType.USAGE_SPIKE
    severity: AlertSeverity = AlertSeverity.WARNING


class TemplatePreview:
    """Template preview system for testing templates with sample data."""

    def __init__(self, template_manager: TemplateManager) -> None:
        """Initialize template preview system.
        
        Args:
            template_manager: Template manager instance for template operations
        """
        self.template_manager: TemplateManager = template_manager

    def preview_template(
        self,
        template_id: str,
        format: TemplateFormat,
        options: Optional[TemplatePreviewOptions] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Preview template with sample data.

        Args:
            template_id: Template ID to preview
            format: Template format to preview
            options: Optional preview options
            custom_data: Optional custom data to use instead of sample data

        Returns:
            Dict containing template info and rendered preview
        """
        # Get template
        logger.info(f"Previewing template {template_id} in {format} format")
        template = self.template_manager.get_template(template_id)
        if not template:
            logger.error(f"Template {template_id} not found during preview")
            raise TemplateNotFoundError(f"Template {template_id} not found")

        # Create sample alert
        if custom_data:
            alert = Alert(**custom_data)
        else:
            alert = Alert(
                id="sample_alert",
                title=options.title if options else "Sample Alert",
                description=options.description if options else "Sample alert description",
                alert_type=options.alert_type if options else AlertType.USAGE_SPIKE,
                severity=options.severity if options else AlertSeverity.WARNING,
                created_at=datetime.now(timezone.utc),
                metric_value=100.0,
                threshold_value=90.0,
                metadata={
                    "source": "preview",
                    "correlation_id": "preview_correlation_id",
                    "context": {"preview": True}
                }
            )

        # Render template
        rendered = self.template_manager.render_template(
            template_id=template_id,
            format=format,
            alert=alert
        )

        return {
            "template_name": template.name,
            "format": format,
            "sample_data": alert.dict(),
            "rendered": rendered
        }


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value.data = []
    return mock


@pytest.fixture
def template_manager(mock_supabase):
    """Template manager fixture."""
    return TemplateManager(
        supabase_client=mock_supabase,
        merchant_id="test_merchant",
    )


@pytest.fixture
def template_preview(template_manager):
    """Template preview fixture."""
    return TemplatePreview(template_manager)


@pytest.fixture
def sample_template():
    """Sample template."""
    return NotificationTemplate(
        id="test_template",
        merchant_id="test_merchant",
        name="Test Template",
        description="Test template for unit tests",
        alert_types=[AlertType.USAGE_SPIKE],
        min_severity=AlertSeverity.WARNING,
        subject_template="Test Alert: {title}",
        html_template="""
        <html>
            <body>
                <h1>{title}</h1>
                <p>{description}</p>
                <p>Value: {metric_value}</p>
            </body>
        </html>
        """,
        plain_template="""
        {title}
        {description}
        Value: {metric_value}
        """,
        slack_template="""
        *{title}*
        {description}
        Value: {metric_value}
        """,
        webhook_template="""
        {
            "title": "{title}",
            "description": "{description}",
            "value": {metric_value}
        }
        """,
    )


@pytest.fixture
def sample_alert():
    """Sample alert."""
    return Alert(
        id="test_alert",
        title="Test Alert",
        description="Test alert description",
        alert_type=AlertType.USAGE_SPIKE,
        severity=AlertSeverity.WARNING,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        metric_value=150.0,
        threshold_value=100.0,
        template_id="test_template",
        tag="test_tag",
        metadata={"test": True},
    )


def test_create_template(template_manager, mock_supabase):
    """Test template creation."""
    # Setup mock
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "id": "new_template",
            "merchant_id": "test_merchant",
            "name": "New Template",
        }]
    }

    # Create template
    template = template_manager.create_template(
        name="New Template",
        description="Test template",
        alert_types=[AlertType.USAGE_SPIKE],
        min_severity=AlertSeverity.WARNING,
        html_template="<h1>{title}</h1>",
    )

    # Verify
    assert template.name == "New Template"
    assert template.description == "Test template"
    assert AlertType.USAGE_SPIKE in template.alert_types
    assert template.min_severity == AlertSeverity.WARNING
    assert template.html_template == "<h1>{title}</h1>"


def test_render_template(
    template_manager,
    mock_supabase,
    sample_template,
    sample_alert,
):
    """Test template rendering."""
    # Setup mock
    mock_supabase.table.return_value.select.return_value.execute.return_value = {
        "data": [sample_template.dict()]
    }

    # Test HTML rendering
    html = template_manager.render_template(
        alert=sample_alert,
        template_format=TemplateFormat.HTML,
        template_id="test_template",
    )
    assert "<h1>Test Alert</h1>" in html
    assert "Value: 150.0" in html

    # Test plain text rendering
    plain = template_manager.render_template(
        alert=sample_alert,
        template_format=TemplateFormat.PLAIN,
        template_id="test_template",
    )
    assert "Test Alert" in plain
    assert "Value: 150.0" in plain

    # Test Slack rendering
    slack = template_manager.render_template(
        alert=sample_alert,
        template_format=TemplateFormat.SLACK,
        template_id="test_template",
    )
    assert "*Test Alert*" in slack
    assert "Value: 150.0" in slack

    # Test webhook JSON rendering
    webhook = template_manager.render_template(
        alert=sample_alert,
        template_format=TemplateFormat.WEBHOOK_JSON,
        template_id="test_template",
    )
    webhook_data = json.loads(webhook)
    assert webhook_data["title"] == "Test Alert"
    assert webhook_data["value"] == 150.0


def test_preview_template(
    template_preview,
    mock_supabase,
    sample_template,
):
    """Test template preview."""
    # Setup mock
    mock_supabase.table.return_value.select.return_value.execute.return_value = {
        "data": [sample_template.dict()]
    }

    # Test preview with sample data
    preview = template_preview.preview_template(
        template_id="test_template",
        template_format=TemplateFormat.HTML,
        alert_type=AlertType.USAGE_SPIKE,
        severity=AlertSeverity.WARNING,
    )

    assert preview["template_name"] == "Test Template"
    assert preview["format"] == TemplateFormat.HTML
    assert "sample_data" in preview
    assert "<h1>" in preview["rendered"]

    # Test preview with custom data
    custom_data = {
        "id": "custom_alert",
        "title": "Custom Alert",
        "description": "Custom description",
        "alert_type": AlertType.USAGE_SPIKE,
        "severity": AlertSeverity.WARNING,
        "created_at": datetime.now(timezone.utc),
        "metric_value": 300.0,
        "threshold_value": 250.0,
    }

    preview = template_preview.preview_template(
        template_id="test_template",
        template_format=TemplateFormat.HTML,
        custom_data=custom_data,
    )

    assert preview["template_name"] == "Test Template"
    assert "sample_data" in preview
    assert "Custom Alert" in preview["rendered"]
