"""Minimal test suite for notification templates."""
import json
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock

from tests.performance.template_notification_templates import (
    TemplateManager,
    TemplateFormat,
    NotificationTemplate,
)
from tests.performance.template_alerts import Alert, AlertType, AlertSeverity
from tests.performance.template_preview import TemplatePreview


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
    """Sample notification template."""
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
    """Sample alert for testing."""
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
    assert "custom_data" in preview
    assert "Custom Alert" in preview["rendered"]


def test_validate_template(
    template_preview,
    mock_supabase,
    sample_template,
):
    """Test template validation."""
    # Setup mock
    mock_supabase.table.return_value.select.return_value.execute.return_value = {
        "data": [sample_template.dict()]
    }

    # Test validation
    validation = template_preview.validate_template("test_template")

    assert validation[TemplateFormat.HTML] is True
    assert validation[TemplateFormat.PLAIN] is True
    assert validation[TemplateFormat.SLACK] is True
    assert validation[TemplateFormat.WEBHOOK_JSON] is True

    # Test validation with invalid template
    invalid_template = sample_template.copy()
    invalid_template.html_template = "<h1>{invalid_var}</h1>"
    mock_supabase.table.return_value.select.return_value.execute.return_value = {
        "data": [invalid_template.dict()]
    }

    validation = template_preview.validate_template("test_template")
    assert validation[TemplateFormat.HTML] is False
