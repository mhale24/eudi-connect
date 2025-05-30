"""Template preview system for notification templates."""
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from .template_alerts import Alert, AlertType, AlertSeverity
from .template_notification_templates import TemplateManager, TemplateFormat


class TemplatePreview:
    """Preview system for notification templates."""

    def __init__(self, template_manager: TemplateManager):
        """Initialize template preview.

        Args:
            template_manager: Template manager instance
        """
        self.template_manager = template_manager

    def _generate_sample_alert(
        self,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        template_id: Optional[str] = None,
        tag: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
    ) -> Alert:
        """Generate a sample alert for preview.

        Args:
            alert_type: Optional alert type
            severity: Optional severity
            template_id: Optional template ID
            tag: Optional tag
            metric_value: Optional metric value
            threshold_value: Optional threshold value

        Returns:
            Sample alert
        """
        return Alert(
            id=str(uuid4()),
            title="Sample Alert Title",
            description="This is a sample alert description for preview purposes.",
            alert_type=alert_type or AlertType.USAGE_SPIKE,
            severity=severity or AlertSeverity.INFO,
            created_at=datetime.utcnow(),
            metric_value=metric_value or 150.0,
            threshold_value=threshold_value or 100.0,
            template_id=template_id,
            tag=tag,
            metadata={
                "sample": True,
                "preview": True,
            },
        )

    def preview_template(
        self,
        template_id: str,
        template_format: TemplateFormat,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        tag: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        custom_data: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """Preview a template with sample or custom data.

        Args:
            template_id: Template ID to preview
            template_format: Desired output format
            alert_type: Optional alert type for sample data
            severity: Optional severity for sample data
            tag: Optional tag for sample data
            metric_value: Optional metric value for sample data
            threshold_value: Optional threshold value for sample data
            custom_data: Optional custom data to use instead of sample

        Returns:
            Dict with preview info:
                - rendered: Rendered template content
                - format: Template format used
                - template_name: Name of template
                - sample_data: Data used for preview (if using sample)
                - custom_data: Data used for preview (if using custom)

        Raises:
            ValueError: If template not found or preview fails
        """
        # Get template
        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Generate preview data
        if custom_data:
            # Use custom data
            try:
                rendered = self.template_manager.render_template(
                    alert=Alert(**custom_data),
                    template_format=template_format,
                    template_id=template_id,
                )
            except Exception as e:
                raise ValueError(f"Failed to render with custom data: {e}")

            preview_data = {"custom_data": custom_data}
        else:
            # Generate sample alert
            sample_alert = self._generate_sample_alert(
                alert_type=alert_type,
                severity=severity,
                template_id=template_id,
                tag=tag,
                metric_value=metric_value,
                threshold_value=threshold_value,
            )

            try:
                rendered = self.template_manager.render_template(
                    alert=sample_alert,
                    template_format=template_format,
                    template_id=template_id,
                )
            except Exception as e:
                raise ValueError(f"Failed to render with sample data: {e}")

            preview_data = {"sample_data": sample_alert.dict()}

        return {
            "rendered": rendered,
            "format": template_format,
            "template_name": template.name,
            **preview_data,
        }

    def preview_all_formats(
        self,
        template_id: str,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        tag: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        custom_data: Optional[Dict] = None,
    ) -> Dict[str, Dict[str, str]]:
        """Preview a template in all available formats.

        Args:
            template_id: Template ID to preview
            alert_type: Optional alert type for sample data
            severity: Optional severity for sample data
            tag: Optional tag for sample data
            metric_value: Optional metric value for sample data
            threshold_value: Optional threshold value for sample data
            custom_data: Optional custom data to use instead of sample

        Returns:
            Dict mapping format names to preview results
        """
        previews = {}
        for template_format in TemplateFormat:
            try:
                preview = self.preview_template(
                    template_id=template_id,
                    template_format=template_format,
                    alert_type=alert_type,
                    severity=severity,
                    tag=tag,
                    metric_value=metric_value,
                    threshold_value=threshold_value,
                    custom_data=custom_data,
                )
                previews[template_format] = preview
            except Exception as e:
                previews[template_format] = {
                    "error": str(e),
                    "format": template_format,
                }

        return previews

    def validate_template(
        self,
        template_id: str,
        formats: Optional[list[TemplateFormat]] = None,
    ) -> Dict[str, bool]:
        """Validate a template renders correctly in specified formats.

        Args:
            template_id: Template ID to validate
            formats: Optional list of formats to validate, defaults to all

        Returns:
            Dict mapping format names to validation success
        """
        formats = formats or list(TemplateFormat)
        validation = {}

        for template_format in formats:
            try:
                self.preview_template(
                    template_id=template_id,
                    template_format=template_format,
                )
                validation[template_format] = True
            except Exception:
                validation[template_format] = False

        return validation
