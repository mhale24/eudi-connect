"""Run template tests directly."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock
from test_templates_standalone import (
    Alert,
    AlertType,
    AlertSeverity,
    TemplateFormat,
    NotificationTemplate,
    TemplateManager,
    TemplatePreview,
    TemplatePreviewOptions,
)


def create_mock_supabase():
    """Create a mock Supabase client."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "test_template",
        "merchant_id": "test_merchant",
        "name": "Test Template",
        "description": "Test template for unit tests",
        "alert_types": ["usage_spike"],
        "min_severity": "warning",
        "subject_template": "Test Alert: {title}",
        "html_template": "<html><body><h1>{title}</h1><p>{description}</p><p>Value: {metric_value}</p></body></html>",
        "plain_template": "{title}\n{description}\nValue: {metric_value}",
        "slack_template": "*{title}*\n{description}\nValue: {metric_value}",
        "webhook_template": '{"title": "{title}", "description": "{description}", "value": "{metric_value}"}'  # Fix quotes
    }]
    return mock_sb


def create_template_manager(mock_supabase):
    """Create template manager."""
    return TemplateManager(
        supabase_client=mock_supabase,
        merchant_id="test_merchant",
    )


def create_template_preview(template_manager):
    """Create template preview."""
    return TemplatePreview(template_manager)


def create_sample_template() -> NotificationTemplate:
    """Create a sample template for testing."""
    return NotificationTemplate(
        id="test_template",
        merchant_id="test_merchant",
        name="Test Template",
        description="Test template for unit tests",
        alert_types=[AlertType.USAGE_SPIKE],
        min_severity=AlertSeverity.WARNING,
        subject_template="Test Alert: {title}",
        html_template="""<html>
            <body>
                <h1>{title}</h1>
                <p>{description}</p>
                <p>Value: {metric_value}</p>
            </body>
        </html>""",
        plain_template="""{title}
        {description}
        Value: {metric_value}""",
        slack_template="""*{title}*
        {description}
        Value: {metric_value}""",
        webhook_template=json.dumps({
            "title": "{title}",
            "description": "{description}",
            "value": "{metric_value}"
        }, indent=4),
    )


def create_sample_alert():
    """Create sample alert."""
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
    # Create sample template
    sample_template = create_sample_template()

    # Setup mock response
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [sample_template.dict()]
    }

    # Create template - exclude id and merchant_id fields
    template_data = sample_template.dict()
    template_data.pop('id', None)
    template_data.pop('merchant_id', None)
    template = template_manager.create_template(**template_data)

    # Verify template
    assert template.id == "test_template"
    assert template.merchant_id == "test_merchant"
    assert template.name == "Test Template"
    assert template.description == "Test template for unit tests"
    assert template.alert_types == [AlertType.USAGE_SPIKE]
    assert template.min_severity == AlertSeverity.WARNING
    assert "<h1>{title}</h1>" in template.html_template
    assert "<p>{description}</p>" in template.html_template
    assert "<p>Value: {metric_value}</p>" in template.html_template

    print("✅ test_create_template passed")


def test_render_template(template_manager, mock_supabase, sample_template):
    """Test template rendering."""
    print("\nRunning test_render_template...")
    
    # Create test data
    print("Sample template data:", sample_template.dict())
    alert = Alert(
        id="test_alert",
        title="Test Alert",
        description="This is a test alert",
        alert_type=AlertType.USAGE_SPIKE,
        severity=AlertSeverity.WARNING,
        created_at=datetime.now(timezone.utc),
        metric_value=100.0,
        threshold_value=80.0,
        template_id="test_template",
        tag="test_tag",
        metadata={"test": True}
    )

    # Configure mock for get_template
    mock_execute = MagicMock()
    mock_execute.return_value = {
        "data": [sample_template.dict()]
    }
    mock_eq = MagicMock()
    mock_eq.execute = mock_execute
    mock_select = MagicMock()
    mock_select.eq = lambda *args: mock_eq
    mock_table = MagicMock()
    mock_table.select = lambda: mock_select
    mock_supabase.table = lambda *args: mock_table

    # Test HTML rendering
    html = template_manager.render_template(
        template_id="test_template",
        format=TemplateFormat.HTML,
        alert=alert
    )
    assert isinstance(html, str)
    assert "<h1>" in html
    assert "<p>" in html
    assert "100.0" in html
    
    # Test plain text rendering
    text = template_manager.render_template(
        template_id="test_template",
        format=TemplateFormat.PLAIN,
        alert=alert
    )
    assert isinstance(text, str)
    assert "Test Alert" in text
    assert "This is a test alert" in text
    assert "100.0" in text
    
    # Test Slack rendering
    slack = template_manager.render_template(
        template_id="test_template",
        format=TemplateFormat.SLACK,
        alert=alert
    )
    assert isinstance(slack, str)
    assert "Test Alert" in slack
    assert "This is a test alert" in slack
    assert "100.0" in slack
    
    # Test webhook JSON rendering
    webhook = template_manager.render_template(
        template_id="test_template",
        format=TemplateFormat.WEBHOOK_JSON,
        alert=alert
    )
    assert isinstance(webhook, str)
    webhook_data = json.loads(webhook)
    assert isinstance(webhook_data, dict)
    assert "title" in webhook_data
    assert "description" in webhook_data
    assert "value" in webhook_data
    
    print("✅ test_render_template passed")


def test_preview_template(template_manager, mock_supabase, sample_template):
    """Test template preview."""
    print("\nRunning test_preview_template...")

    # Create template preview
    template_preview = TemplatePreview(template_manager)

    # Configure mock for get_template
    mock_execute = MagicMock()
    mock_execute.return_value = {
        "data": [sample_template.dict()]
    }
    mock_eq = MagicMock()
    mock_eq.execute = mock_execute
    mock_select = MagicMock()
    mock_select.eq = lambda *args: mock_eq
    mock_table = MagicMock()
    mock_table.select = lambda: mock_select
    mock_supabase.table = lambda *args: mock_table

    # Test preview with default options
    preview = template_preview.preview_template(
        template_id="test_template",
        format=TemplateFormat.HTML,
        options=TemplatePreviewOptions(
            title="Custom Alert",
            description="Custom description",
            metric_value=200.0,
            threshold_value=150.0
        )
    )
    assert isinstance(preview["rendered"], str)
    assert "Custom Alert" in preview["rendered"]

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
        "metadata": {
            "source": "test",
            "correlation_id": "test_correlation_id",
            "context": {"test": True}
        }
    }

    preview = template_preview.preview_template(
        template_id="test_template",
        format=TemplateFormat.HTML,
        custom_data=custom_data
    )

    assert isinstance(preview["rendered"], str)
    assert preview["template_name"] == "Test Template"
    assert "sample_data" in preview
    assert "Custom Alert" in preview["rendered"]


def test_batch_render(template_manager, mock_supabase, sample_template):
    """Test batch template rendering."""
    print("\nRunning test_batch_render...")

    # Configure mock for get_template
    mock_execute = MagicMock()
    mock_execute.return_value = {
        "data": [sample_template.dict()]
    }
    mock_eq = MagicMock()
    mock_eq.execute = mock_execute
    mock_select = MagicMock()
    mock_select.eq = lambda *args: mock_eq
    mock_table = MagicMock()
    mock_table.select = lambda: mock_select
    mock_supabase.table = lambda *args: mock_table

    # Create multiple alerts
    alerts = [
        Alert(
            id="test_alert_1",
            title="Test Alert 1",
            description="First test alert",
            alert_type=AlertType.USAGE_SPIKE,
            severity=AlertSeverity.WARNING,
            created_at=datetime.now(timezone.utc),
            metric_value=150.0,
            threshold_value=100.0,
            template_id="test_template",
            tag="test_tag_1",
            metadata={"test": True}
        ),
        Alert(
            id="test_alert_2",
            title="Test Alert 2",
            description="Second test alert",
            alert_type=AlertType.USAGE_SPIKE,
            severity=AlertSeverity.ERROR,
            created_at=datetime.now(timezone.utc),
            metric_value=200.0,
            threshold_value=150.0,
            template_id="test_template",
            tag="test_tag_2",
            metadata={"test": True}
        ),
        Alert(
            id="test_alert_3",
            title="Test Alert 3",
            description="Third test alert",
            alert_type=AlertType.USAGE_DROP,
            severity=AlertSeverity.CRITICAL,
            created_at=datetime.now(timezone.utc),
            metric_value=50.0,
            threshold_value=100.0,
            template_id="test_template",
            tag="test_tag_3",
            metadata={"test": True}
        )
    ]

    # Test batch HTML rendering
    rendered = template_manager.render_batch(
        template_id="test_template",
        format=TemplateFormat.HTML,
        alerts=alerts
    )

    assert len(rendered) == 3
    assert isinstance(rendered[0], str)
    assert isinstance(rendered[1], str)
    assert isinstance(rendered[2], str)
    assert "Test Alert 1" in rendered[0]
    assert "Test Alert 2" in rendered[1]
    assert "Test Alert 3" in rendered[2]
    assert "150.0" in rendered[0]
    assert "200.0" in rendered[1]
    assert "50.0" in rendered[2]

    print("✅ test_batch_render passed")


def run_tests():
    """Run all template tests."""
    # Create mocks
    mock_sb = create_mock_supabase()
    tm = create_template_manager(mock_sb)
    
    # Create sample template
    sample_template = create_sample_template()

    # Run tests
    test_create_template(tm, mock_sb)
    print("✅ test_create_template passed")
    
    test_render_template(tm, mock_sb, sample_template)
    print("✅ test_render_template passed")
    
    test_preview_template(tm, mock_sb, sample_template)
    print("✅ test_preview_template passed")

    print("\nRunning test_batch_render...")
    test_batch_render(tm, mock_sb, sample_template)
    print("✅ test_batch_render passed")

    print("\n🎉 All tests passed!")


if __name__ == "__main__":
    run_tests()
