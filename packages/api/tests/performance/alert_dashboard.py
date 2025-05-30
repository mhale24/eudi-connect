"""Alert management dashboard."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import pandas as pd
import plotly.express as px
import streamlit as st
from plotly import graph_objects as go

import os
from datetime import datetime

from tests.performance.alerts import AlertChannel, AlertManager, AlertSeverity
from tests.performance.alert_rules import (
    AlertAction,
    AlertRule,
    ComparisonOperator,
    MetricCategory,
    RuleManager,
    RuleTemplate,
)
from tests.performance.alert_testing import RuleTester
from tests.performance.batch_testing import BatchTestConfig, BatchTester
from tests.performance.result_export import ExportFormat, HtmlTemplate, ResultExporter
from tests.performance.template_config import (
    ChartTheme,
    ColorScheme,
    TableStyle,
    TemplateConfig,
    FontConfig,
    ColorConfig,
    ChartConfig,
    MetricsConfig,
)
from tests.performance.template_presets import TEMPLATE_PRESETS
from tests.performance.template_sharing import TemplateLibrary, TemplateShare
from tests.performance.template_cloud import TemplateCloud, CloudTemplate
from tests.performance.template_search import TemplateSearch, SearchResult
from tests.performance.template_recommendations import (
    RecommendationEngine,
    TemplateUsage,
    TemplateRecommendation,
)
from tests.performance.template_version_control import (
    VersionControl,
    TemplateVersion,
    TemplateChange,
    ChangeType,
)
from tests.performance.template_analytics import (
    TemplateAnalytics,
    EventType,
    TimeRange,
)
from .template_analytics import TemplateAnalytics
from .template_cloud import CloudSync
from .template_recommendations import RecommendationEngine
from .template_alerts import AlertManager, AlertType, AlertSeverity
from .template_notifications import NotificationManager, NotificationChannel
from .template_notification_templates import TemplateManager, TemplateFormat, NotificationTemplate
from .template_preview import TemplatePreview

# Set page config
st.set_page_config(
    page_title="EUDI-Connect Alert Dashboard",
    page_icon="🚨",
    layout="wide",
)


class AlertDashboard:
    """Alert management dashboard."""

    def __init__(self):
        """Initialize dashboard."""
        self.alert_manager = AlertManager(
            channels=[AlertChannel.CONSOLE, AlertChannel.SLACK],
        )
        self.rule_manager = RuleManager()
        self.rule_tester = RuleTester(
            rule_manager=self.rule_manager,
            alert_manager=self.alert_manager,
        )
        self.batch_tester = BatchTester(
            rule_manager=self.rule_manager,
            alert_manager=self.alert_manager,
        )
        self.result_exporter = ResultExporter(
            rule_manager=self.rule_manager,
        )
        self.template_library = TemplateLibrary(
            library_dir="templates/shared",
        )
        
        # Initialize recommendation engine with analytics
        self.recommendation_engine = RecommendationEngine(analytics=self.analytics)
        
        # Initialize template manager and preview
        self.template_manager = TemplateManager(
            supabase_client=self.supabase,
            merchant_id=self.merchant_id,
        )
        self.template_preview = TemplatePreview(self.template_manager)
        
        # Initialize notification manager
        smtp_config = {
            "host": os.getenv("SMTP_HOST", "localhost"),
            "port": int(os.getenv("SMTP_PORT", "25")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from_email": os.getenv("SMTP_FROM", "alerts@eudi-connect.eu"),
        }
        
        self.notification_manager = NotificationManager(
            supabase_client=self.supabase,
            merchant_id=self.merchant_id,
            smtp_config=smtp_config,
            template_manager=self.template_manager,
        )
        
        # Initialize alert manager with notifications
        self.alert_manager = AlertManager(
            analytics=self.analytics,
            supabase_client=self.supabase,
            merchant_id=self.merchant_id,
            notification_manager=self.notification_manager,
        )
        
        # Set up default alert rules
        self._setup_default_alerts()
        
        # Initialize cloud sync if credentials available
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        merchant_id = os.getenv("MERCHANT_ID")
        
        self.template_cloud = None
        self.version_control = None
        self.analytics = None
        self.merchant_id = merchant_id
        if all([supabase_url, supabase_key, merchant_id]):
            self.template_cloud = TemplateCloud(
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                merchant_id=merchant_id,
            )
            self.version_control = VersionControl(
                supabase_client=self.template_cloud.supabase,
            )
            self.analytics = TemplateAnalytics(
                supabase_client=self.template_cloud.supabase,
            )

    def _setup_default_alerts(self):
        """Set up default alert rules, notifications, and templates."""
        # Set up default templates if none exist
        if not self.template_manager.get_templates():
            # Email template
            self.template_manager.create_template(
                name="Default Email Template",
                description="Standard email template for alerts",
                subject_template="[{severity}] {title}",
                html_template="""<html>
                    <body style='font-family: Arial, sans-serif;'>
                        <div style='max-width: 600px; margin: 0 auto; padding: 20px;'>
                            <h1 style='color: #333;'>{title}</h1>
                            <p style='color: #666;'>{description}</p>
                            
                            <div style='background: #f5f5f5; padding: 15px; border-radius: 5px;'>
                                <h3 style='margin-top: 0;'>Alert Details</h3>
                                <p><strong>Type:</strong> {alert_type}</p>
                                <p><strong>Severity:</strong> {severity}</p>
                                <p><strong>Created:</strong> {created_at}</p>
                            </div>
                            
                            <div style='margin-top: 20px;'>
                                <h3>Metrics</h3>
                                <p><strong>Current Value:</strong> {metric_value}</p>
                                <p><strong>Threshold:</strong> {threshold_value}</p>
                            </div>
                            
                            {template_info}
                            {tag_info}
                            
                            <div style='margin-top: 30px;'>
                                <a href='https://dashboard.eudi-connect.eu/alerts/{id}' 
                                   style='background: #007bff; color: white; padding: 10px 20px; 
                                          text-decoration: none; border-radius: 5px;'>
                                    View in Dashboard
                                </a>
                            </div>
                        </div>
                    </body>
                </html>""",
            )
            
            # Slack template
            self.template_manager.create_template(
                name="Default Slack Template",
                description="Standard Slack template for alerts",
                slack_template="""🚨 *{title}*
                
                {description}
                
                *Alert Details*
                • Type: {alert_type}
                • Severity: {severity}
                • Created: {created_at}
                
                *Metrics*
                • Current Value: {metric_value}
                • Threshold: {threshold_value}
                
                {template_info}
                {tag_info}
                
                <https://dashboard.eudi-connect.eu/alerts/{id}|View in Dashboard>""",
            )
        
        # Set up default notification channels if none exist
        if not self.notification_manager.get_notification_configs():
            # Email notifications
            self.notification_manager.create_notification_config(
                channel=NotificationChannel.EMAIL,
                name="Default Email Alerts",
                description="High priority template alerts",
                email_recipients=[os.getenv("DEFAULT_ALERT_EMAIL")],
                min_severity=AlertSeverity.WARNING,
            )
            
            # Slack notifications
            slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
            if slack_webhook:
                self.notification_manager.create_notification_config(
                    channel=NotificationChannel.SLACK,
                    name="Default Slack Alerts",
                    description="All template alerts",
                    slack_webhook_url=slack_webhook,
                    slack_channel="#template-alerts",
                )
        
        # Set up default alert rules if none exist
        if not self.alert_manager.get_alert_rules():
            self.alert_manager.create_alert_rule(
                name="Default Alert Rule",
                description="Default alert rule for all templates",
                metric="template_performance",
                operator=ComparisonOperator.GREATER_THAN,
                warning_threshold=0.5,
                critical_threshold=0.8,
                duration=3,
                cooldown=5,
                actions=[AlertAction.EMAIL, AlertAction.SLACK],
            )

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data.

        Returns:
            Dashboard data dictionary
        """
        # Check for new alerts
        new_alerts = await self.alert_manager.check_alerts()
        dashboard_data = {
            "alerts": {
                "active": self.alert_manager.get_active_alerts(),
                "new": new_alerts,
                "notifications": {
                    "configs": self.notification_manager.get_notification_configs(),
                    "recent_logs": self.notification_manager.get_notification_logs(limit=10),
                    "templates": self.template_manager.get_templates(),
                    "template_previews": {
                        template.id: self.template_preview.preview_all_formats(
                            template_id=template.id,
                            alert_type=AlertType.USAGE_SPIKE,
                            severity=AlertSeverity.WARNING,
                        ) for template in self.template_manager.get_templates()
                    },
                },
            },
        }
        return dashboard_data

    def render_alert_stats(self):
        """Render alert statistics."""
        active_alerts = self.alert_manager.history.get_active_alerts()
        recent_alerts = self.alert_manager.history.get_recent_alerts(hours=24)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Active Alerts",
                len(active_alerts),
                delta=f"{len(active_alerts) - len(recent_alerts)}",
                delta_color="inverse",
            )
        with col2:
            critical = sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL)
            st.metric(
                "Critical Alerts",
                critical,
                delta=critical,
                delta_color="inverse",
            )
        with col3:
            warning = sum(1 for a in active_alerts if a.severity == AlertSeverity.WARNING)
            st.metric(
                "Warning Alerts",
                warning,
                delta=warning,
                delta_color="inverse",
            )
        with col4:
            info = sum(1 for a in active_alerts if a.severity == AlertSeverity.INFO)
            st.metric(
                "Info Alerts",
                info,
                delta=info,
                delta_color="inverse",
            )

    def create_alert_timeline(self):
        """Create alert timeline visualization."""
        alerts = self.alert_manager.history.get_recent_alerts(hours=24)
        if not alerts:
            return None

        df = pd.DataFrame([
            {
                "Alert": a.metric_name,
                "Severity": a.severity,
                "Value": a.current_value,
                "Threshold": a.threshold_value,
                "Time": a.timestamp,
                "Status": "Resolved" if a.resolved else "Active",
            }
            for a in alerts
        ])

        fig = go.Figure()

        # Add scatter plot for each severity level
        colors = {
            AlertSeverity.CRITICAL: "#dc3545",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.INFO: "#0dcaf0",
        }

        for severity in AlertSeverity:
            mask = df["Severity"] == severity
            if not mask.any():
                continue

            fig.add_trace(go.Scatter(
                x=df[mask]["Time"],
                y=df[mask]["Value"],
                name=severity,
                mode="markers",
                marker=dict(
                    size=12,
                    color=colors[severity],
                    symbol="circle",
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Value: %{y:.2f}<br>"
                    "Time: %{x}<br>"
                    "<extra></extra>"
                ),
                text=df[mask]["Alert"],
            ))

        fig.update_layout(
            title="Alert Timeline",
            xaxis_title="Time",
            yaxis_title="Value",
            showlegend=True,
            hovermode="closest",
        )

        return fig

    def create_alert_heatmap(self):
        """Create alert heatmap by metric and hour."""
        alerts = self.alert_manager.history.get_recent_alerts(hours=24)
        if not alerts:
            return None

        # Create hourly bins
        hours = pd.date_range(
            start=datetime.now() - timedelta(hours=24),
            end=datetime.now(),
            freq="H",
        )

        # Create alert counts by metric and hour
        data = []
        for alert in alerts:
            hour = alert.timestamp.replace(minute=0, second=0, microsecond=0)
            data.append({
                "Metric": alert.metric_name,
                "Hour": hour,
                "Count": 1,
                "Severity": alert.severity,
            })

        df = pd.DataFrame(data)
        df_pivot = df.pivot_table(
            values="Count",
            index="Metric",
            columns="Hour",
            aggfunc="sum",
            fill_value=0,
        )

        fig = go.Figure(data=go.Heatmap(
            z=df_pivot.values,
            x=df_pivot.columns,
            y=df_pivot.index,
            colorscale=[
                [0, "#ffffff"],
                [0.33, "#ffc107"],
                [0.66, "#fd7e14"],
                [1, "#dc3545"],
            ],
        ))

        fig.update_layout(
            title="Alert Frequency Heatmap",
            xaxis_title="Hour",
            yaxis_title="Metric",
        )

        return fig

    def render_rules_editor(self):
        """Render the alert rules editor."""
        st.header("Alert Rules")

        # Rule management tabs
        tab1, tab2 = st.tabs(["Existing Rules", "Create New Rule"])

        with tab1:
            # Display existing rules
            rules = self.rule_manager.get_rules()
            if not rules:
                st.info("No alert rules configured")
                return

            # Filter rules by category
            category = st.selectbox(
                "Filter by category",
                options=[None] + list(MetricCategory),
                format_func=lambda x: "All" if x is None else x.value.title(),
            )

            filtered_rules = self.rule_manager.get_rules(category)
            for rule in filtered_rules:
                with st.expander(f"{rule.name} ({rule.metric})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Rule Details**")
                        st.write(f"Description: {rule.description}")
                        st.write(f"Category: {rule.category}")
                        st.write(f"Metric: {rule.metric}")
                        st.write(f"Operator: {rule.operator}")

                    with col2:
                        st.write("**Thresholds**")
                        warning = st.number_input(
                            "Warning threshold",
                            value=rule.warning_threshold,
                            key=f"warning_{rule.id}",
                        )
                        critical = st.number_input(
                            "Critical threshold",
                            value=rule.critical_threshold,
                            key=f"critical_{rule.id}",
                        )
                        duration = st.number_input(
                            "Duration (consecutive violations)",
                            value=rule.duration,
                            min_value=1,
                            key=f"duration_{rule.id}",
                        )
                        cooldown = st.number_input(
                            "Cooldown (seconds)",
                            value=rule.cooldown,
                            min_value=0,
                            key=f"cooldown_{rule.id}",
                        )

                    # Actions
                    st.write("**Actions**")
                    actions = st.multiselect(
                        "Alert actions",
                        options=list(AlertAction),
                        default=rule.actions,
                        format_func=lambda x: x.value.title(),
                        key=f"actions_{rule.id}",
                    )

                    if AlertAction.CUSTOM in actions:
                        custom_action = st.text_input(
                            "Custom action command",
                            value=rule.custom_action or "",
                            key=f"custom_{rule.id}",
                        )
                    else:
                        custom_action = None

                    # Save changes
                    if st.button("Save Changes", key=f"save_{rule.id}"):
                        updates = {
                            "warning_threshold": warning,
                            "critical_threshold": critical,
                            "duration": duration,
                            "cooldown": cooldown,
                            "actions": actions,
                            "custom_action": custom_action,
                        }
                        self.rule_manager.update_rule(rule.id, updates)
                        st.success("Rule updated successfully!")

                    # Delete rule
                    if st.button("Delete Rule", key=f"delete_{rule.id}"):
                        if self.rule_manager.delete_rule(rule.id):
                            st.success("Rule deleted successfully!")
                            st.rerun()

        with tab2:
            # Create new rule
            st.subheader("Create New Rule")

            # Select template
            category = st.selectbox(
                "Category",
                options=list(MetricCategory),
                format_func=lambda x: x.value.title(),
            )

            templates = self.rule_manager.get_templates(category)
            template = st.selectbox(
                "Template",
                options=templates,
                format_func=lambda x: x.name,
            )

            if template:
                st.write(f"**Description**: {template.description}")
                metric = st.text_input("Metric name")
                warning = st.number_input(
                    "Warning threshold",
                    value=float(template.suggested_warning),
                )
                critical = st.number_input(
                    "Critical threshold",
                    value=float(template.suggested_critical),
                )

                if st.button("Create Rule"):
                    try:
                        rule = self.rule_manager.create_rule_from_template(
                            template,
                            metric,
                            warning,
                            critical,
                        )
                        self.rule_manager.add_rule(rule)
                        st.success("Rule created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating rule: {e}")

    def render_rule_testing(self):
        """Render the rule testing interface."""
        st.header("Rule Testing")

        # Select rule to test
        rules = self.rule_manager.get_rules()
        if not rules:
            st.warning("No rules available for testing")
            return

        rule = st.selectbox(
            "Select rule to test",
            options=rules,
            format_func=lambda x: f"{x.name} ({x.metric})",
        )

        if not rule:
            return

        # Display rule details
        st.subheader("Rule Details")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Description**: {rule.description}")
            st.write(f"**Metric**: {rule.metric}")
            st.write(f"**Category**: {rule.category}")
        with col2:
            st.write(f"**Warning Threshold**: {rule.warning_threshold}")
            st.write(f"**Critical Threshold**: {rule.critical_threshold}")
            st.write(f"**Duration**: {rule.duration} violations")

        # Select test scenario
        st.subheader("Test Scenario")
        scenarios = self.rule_tester.get_test_scenarios()
        scenario = st.selectbox(
            "Select test scenario",
            options=scenarios,
            format_func=lambda x: x.name,
        )

        if not scenario:
            return

        st.write(f"**Description**: {scenario.description}")
        st.write(f"**Duration**: {scenario.duration_minutes} minutes")
        st.write(f"**Pattern**: {scenario.metric_pattern}")

        # Run test
        if st.button("Run Test"):
            with st.spinner("Running test..."):
                # Run test and get results
                df, alerts = self.rule_tester.test_rule(rule, scenario)
                results = self.rule_tester.analyze_results(
                    df, alerts, rule, scenario
                )

                # Save results
                results_file = self.rule_tester.save_results(
                    results, scenario, rule
                )

                # Display results
                st.subheader("Test Results")

                # Metric timeline
                fig = go.Figure()

                # Add metric line
                fig.add_trace(go.Scatter(
                    x=df["timestamp"],
                    y=df["value"],
                    name="Metric Value",
                    line=dict(color="#0d6efd"),
                ))

                # Add threshold lines
                fig.add_hline(
                    y=rule.warning_threshold,
                    line_dash="dash",
                    line_color="#ffc107",
                    name="Warning Threshold",
                )
                fig.add_hline(
                    y=rule.critical_threshold,
                    line_dash="dash",
                    line_color="#dc3545",
                    name="Critical Threshold",
                )

                # Add alert points
                if alerts:
                    alert_times = [a.timestamp for a in alerts]
                    alert_values = [a.current_value for a in alerts]
                    alert_colors = [
                        "#ffc107" if a.severity == AlertSeverity.WARNING else "#dc3545"
                        for a in alerts
                    ]

                    fig.add_trace(go.Scatter(
                        x=alert_times,
                        y=alert_values,
                        mode="markers",
                        name="Alerts",
                        marker=dict(
                            size=10,
                            color=alert_colors,
                            symbol="star",
                        ),
                    ))

                fig.update_layout(
                    title="Metric Timeline with Alerts",
                    xaxis_title="Time",
                    yaxis_title=rule.metric,
                    showlegend=True,
                )

                st.plotly_chart(fig, use_container_width=True)

                # Test metrics
                metrics = results["metrics"]
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Total Alerts",
                        metrics["total_alerts"],
                        f"{metrics['alert_frequency']:.2f}/min",
                    )
                with col2:
                    st.metric(
                        "Points Above Warning",
                        metrics["points_above_warning"],
                        f"{metrics['points_above_warning']/metrics['total_points']*100:.1f}%",
                    )
                with col3:
                    st.metric(
                        "Points Above Critical",
                        metrics["points_above_critical"],
                        f"{metrics['points_above_critical']/metrics['total_points']*100:.1f}%",
                    )

                # Alert details
                if alerts:
                    st.subheader("Alert Details")
                    alert_df = pd.DataFrame([
                        {
                            "Time": a.timestamp.strftime("%H:%M:%S"),
                            "Severity": a.severity,
                            "Value": f"{a.current_value:.2f}",
                            "Threshold": f"{a.threshold_value:.2f}",
                        }
                        for a in alerts
                    ])
                    st.dataframe(
                        alert_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                # Save results
                st.success(
                    f"Test results saved to {results_file.name}"
                )

    def render_batch_testing(self):
        """Render the batch testing interface."""
        st.header("Batch Testing")

        # Test configuration
        st.subheader("Test Configuration")

        # Basic settings
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                "Test Name",
                value=f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            )
            description = st.text_area(
                "Description",
                value="Batch test of alert rules",
            )

        with col2:
            parallel_tests = st.number_input(
                "Parallel Tests",
                min_value=1,
                max_value=8,
                value=4,
            )
            save_results = st.checkbox(
                "Save Results",
                value=True,
            )

        # Rule selection
        st.write("**Rule Selection**")
        selection_type = st.radio(
            "Select rules by",
            options=["All Rules", "Categories", "Individual Rules"],
            horizontal=True,
        )

        rule_ids: Set[str] = set()
        rule_categories: Set[MetricCategory] = set()

        if selection_type == "Categories":
            categories = st.multiselect(
                "Categories",
                options=list(MetricCategory),
                format_func=lambda x: x.value.title(),
            )
            rule_categories = set(categories)

        elif selection_type == "Individual Rules":
            rules = st.multiselect(
                "Rules",
                options=self.rule_manager.get_rules(),
                format_func=lambda x: f"{x.name} ({x.metric})",
            )
            rule_ids = {r.id for r in rules}

        # Scenario selection
        st.write("**Scenario Selection**")
        scenario_selection = st.radio(
            "Select scenarios",
            options=["All Scenarios", "Selected Scenarios"],
            horizontal=True,
        )

        scenario_names: Set[str] = set()
        if scenario_selection == "Selected Scenarios":
            scenarios = st.multiselect(
                "Scenarios",
                options=self.rule_tester.get_test_scenarios(),
                format_func=lambda x: x.name,
            )
            scenario_names = {s.name for s in scenarios}

        # Run batch test
        if st.button("Run Batch Test"):
            config = BatchTestConfig(
                name=name,
                description=description,
                rule_ids=rule_ids,
                rule_categories=rule_categories,
                scenario_names=scenario_names,
                parallel_tests=parallel_tests,
                save_results=save_results,
            )

            with st.spinner("Running batch tests..."):
                # Run tests
                result = asyncio.run(
                    self.batch_tester.run_batch_test(config)
                )

                # Analyze results
                rule_metrics, scenario_metrics = (
                    self.batch_tester.analyze_batch_results(result)
                )

                # Display results
                st.subheader("Test Results")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"Total Tests: {result.total_tests}")
                    st.write(f"Successful Tests: {result.successful_tests}")
                    st.write(f"Failed Tests: {result.failed_tests}")
                    st.write(f"Total Alerts: {result.total_alerts}")
                with col2:
                    st.subheader("Export Results")
                    export_format = st.selectbox(
                        "Format",
                        options=list(ExportFormat),
                        format_func=lambda x: x.value.upper(),
                    )

                    # Show template selection for HTML format
                    html_template = HtmlTemplate.DEFAULT
                    template_config = None
                    if export_format == ExportFormat.HTML:
                        col1, col2 = st.columns([2, 3])
                        with col1:
                            html_template = st.selectbox(
                                "Template",
                                options=list(HtmlTemplate),
                                format_func=lambda x: x.value.title(),
                                help="Choose a template for the HTML report",
                            )

                            export_name = st.text_input(
                                "Filename",
                                value=result.config.name,
                            )

                            template_descriptions = {
                                HtmlTemplate.DEFAULT: "Standard report with clean, modern design",
                                HtmlTemplate.MINIMAL: "Simple, lightweight report format",
                                HtmlTemplate.DETAILED: "Comprehensive report with extended metrics",
                            }
                            st.markdown(
                                f"*{template_descriptions[html_template]}*",
                                help="Template description",
                            )

                        # Template customization
                        with col2:
                            # Template source selection
                            template_source = st.radio(
                                "Template Source",
                                options=["presets", "shared", "custom"],
                                format_func=lambda x: x.title(),
                                horizontal=True,
                            )

                            if template_source == "presets":
                                # Built-in presets
                                preset_key = st.selectbox(
                                    "Template Preset",
                                    options=list(TEMPLATE_PRESETS.keys()),
                                    format_func=lambda x: TEMPLATE_PRESETS[x].name,
                                    help="Choose a predefined template preset",
                                )
                                template_config = TEMPLATE_PRESETS[preset_key].config

                                # Show preset info
                                st.markdown(
                                    f"*{TEMPLATE_PRESETS[preset_key].description}*",
                                    help="Preset description",
                                )
                                if TEMPLATE_PRESETS[preset_key].preview_image:
                                    st.image(
                                        TEMPLATE_PRESETS[preset_key].preview_image,
                                        caption="Template Preview",
                                        use_column_width=True,
                                    )

                            elif template_source == "shared":
                                # Template source tabs
                                source_tab = st.radio(
                                    "Source",
                                    options=["Local", "Cloud"],
                                    horizontal=True,
                                )

                                if source_tab == "Local":
                                    # Local shared templates
                                    shared_templates = self.template_library.list_templates()
                                    if not shared_templates:
                                        st.info("No local templates found. Import one below or sync from cloud.")
                                        template_config = None
                                    else:
                                        template_name = st.selectbox(
                                            "Local Template",
                                            options=list(shared_templates.keys()),
                                            help="Choose a local template",
                                        )
                                        template_config = self.template_library.load_template(template_name)

                                    # Template sharing
                                    with st.expander("Share Templates"):
                                        # Export current template
                                        if template_config:
                                            share_string = TemplateShare.export_template(template_config)
                                            st.text_area(
                                                "Share String",
                                                value=share_string,
                                                help="Copy this string to share the template",
                                            )
                                            if st.button("Delete Template"):
                                                self.template_library.delete_template(template_name)
                                                st.success(f"Deleted template: {template_name}")
                                                st.rerun()

                                        # Import new template
                                        share_input = st.text_area(
                                            "Import Template",
                                            help="Paste a share string to import a template",
                                        )
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            import_name = st.text_input(
                                                "Template Name",
                                                help="Name for the imported template",
                                            )
                                        with col2:
                                            import_as_preset = st.checkbox(
                                                "Import as Preset",
                                                help="Import with additional preset metadata",
                                            )

                                        if st.button("Import") and share_input and import_name:
                                            try:
                                                imported = TemplateShare.import_template(
                                                    share_input,
                                                    as_preset=import_as_preset,
                                                )
                                                self.template_library.save_template(
                                                    imported,
                                                    name=import_name,
                                                )
                                                st.success(f"Imported template: {import_name}")
                                                st.rerun()
                                            except (ValueError, ValidationError) as e:
                                                st.error(f"Import failed: {str(e)}")

                                else:  # Cloud tab
                                    if not self.template_cloud:
                                        st.error(
                                            "Cloud sync not configured. Set SUPABASE_URL, "
                                            "SUPABASE_KEY, and MERCHANT_ID environment variables."
                                        )
                                        template_config = None
                                    else:
                                        # Show recommendations first
                                        cloud_templates = self.template_cloud.list_templates(
                                            owned_only=owned_only,
                                            public_only=public_only,
                                        )
                                        
                                        # Get sample usage data (replace with actual DB query)
                                        usage_data = [
                                            TemplateUsage(
                                                template_id=t.id,
                                                user_id=self.merchant_id,
                                                timestamp=t.updated_at,
                                                duration=3600,
                                                exported=True,
                                                favorited=True
                                            )
                                            for t in cloud_templates[:3]
                                        ]
                                        
                                        # Get user's preferred tags
                                        user_tags = self.recommendation_engine.get_user_tags(
                                            user_id=self.merchant_id,
                                            usage_data=usage_data,
                                            templates=cloud_templates,
                                        )
                                        
                                        # Get recommendations
                                        recommendations = self.recommendation_engine.get_user_recommendations(
                                            templates=cloud_templates,
                                            usage_data=usage_data,
                                            current_template=template_config if "template_config" in locals() else None,
                                            user_tags=user_tags,
                                        )
                                        
                                        if recommendations:
                                            st.markdown("### Recommended Templates")
                                            for rec in recommendations:
                                                with st.expander(
                                                    f"{rec.template.name} ({rec.score:.1f}% match)",
                                                    expanded=rec == recommendations[0],
                                                ):
                                                    # Template details
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        st.markdown(f"**Why:** {rec.reason}")
                                                        if rec.similar_to:
                                                            st.markdown(f"**Similar to:** {rec.similar_to}")
                                                    with col2:
                                                        st.markdown(
                                                            f"**Updated:** {rec.template.updated_at.strftime('%Y-%m-%d %H:%M')}"
                                                        )
                                                        if rec.tags:
                                                            st.markdown(f"**Tags:** {', '.join(rec.tags)}")

                                                    # Template selection
                                                    if st.button("Use Template", key=f"rec_{rec.template.id}"):
                                                        template_id = rec.template.id
                                                        template_config = self.template_cloud.download_template(template_id)
                                                        st.success(f"Selected template: {rec.template.name}")
                                                        
                                                        # Record version if not exists
                                                        try:
                                                            self.version_control.get_version(template_id)
                                                        except ValueError:
                                                            self.version_control.create_version(
                                                                template_id=template_id,
                                                                content=template_config,
                                                                author=self.merchant_id,
                                                                commit_message="Initial version",
                                                                tags=set(rec.tags),
                                                                is_public=rec.template.is_public,
                                                            )
                                                        
                                                        # Record analytics
                                                        self.analytics.record_event(
                                                            template_id=template_id,
                                                            merchant_id=self.merchant_id,
                                                            event_type=EventType.VIEW,
                                                            metadata={"tags": ",".join(rec.tags)},
                                                        )
                                                        
                                            st.markdown("---")
                                        
                                        # Show trending tags
                                        trending_tags = self.recommendation_engine.get_trending_tags(
                                            usage_data=usage_data,
                                            templates=cloud_templates,
                                        )
                                        
                                        if trending_tags:
                                            st.markdown("### Trending Tags")
                                            tag_cols = st.columns(min(5, len(trending_tags)))
                                            for i, (tag, count) in enumerate(trending_tags):
                                                with tag_cols[i]:
                                                    st.markdown(f"**{tag}** ({count})")
                                            st.markdown("---")
                                        # Cloud template filters
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            owned_only = st.checkbox(
                                                "My Templates",
                                                help="Show only your templates",
                                            )
                                        with col2:
                                            public_only = st.checkbox(
                                                "Public Only",
                                                help="Show only public templates",
                                            )
                                        with col3:
                                            sync_auto = st.checkbox(
                                                "Auto Sync",
                                                help="Automatically sync with cloud",
                                            )

                                        # Template search
                                        st.markdown("### Search Templates")
                                        search_col1, search_col2 = st.columns([3, 1])
                                        with search_col1:
                                            search_query = st.text_input(
                                                "Search Templates",
                                                help="Search by name, description, or author",
                                            )
                                        with search_col2:
                                            min_score = st.slider(
                                                "Match Threshold",
                                                min_value=0,
                                                max_value=100,
                                                value=60,
                                                help="Minimum relevance score",
                                            )

                                        # Tag selection
                                        cloud_templates = self.template_cloud.list_templates(
                                            owned_only=owned_only,
                                            public_only=public_only,
                                        )

                                        # Show popular tags
                                        popular_tags = TemplateSearch.extract_popular_tags(cloud_templates)
                                        if popular_tags:
                                            st.markdown("### Popular Tags")
                                            tag_cols = st.columns(min(5, len(popular_tags)))
                                            selected_tags = set()
                                            for i, (tag, count) in enumerate(popular_tags):
                                                with tag_cols[i % len(tag_cols)]:
                                                    if st.button(
                                                        f"{tag} ({count})",
                                                        help=f"Add {tag} to search",
                                                        type="secondary",
                                                    ):
                                                        selected_tags.add(tag)

                                        # Custom tag input
                                        custom_tags = st.multiselect(
                                            "Filter by Tags",
                                            options=[t for t, _ in popular_tags],
                                            default=list(selected_tags),
                                            help="Select tags to filter templates",
                                        )

                                        # Search templates
                                        search_results = TemplateSearch.search_templates(
                                            templates=cloud_templates,
                                            query=search_query if search_query else None,
                                            tags=custom_tags if custom_tags else None,
                                            min_score=float(min_score),
                                        )

                                        if not search_results:
                                            st.info("No matching templates found. Try adjusting your search.")
                                            template_config = None
                                        else:
                                            # Show search results
                                            st.markdown("### Search Results")
                                            for result in search_results:
                                                template = result.template
                                                with st.expander(
                                                    f"{template.name} ({result.score:.1f}% match)",
                                                    expanded=result == search_results[0],
                                                ):
                                                    # Template details
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        st.markdown(f"**Author:** {template.author}")
                                                        st.markdown(f"**Version:** {template.version}")
                                                    with col2:
                                                        st.markdown(
                                                            f"**Updated:** {template.updated_at.strftime('%Y-%m-%d %H:%M')}"
                                                        )
                                                        st.markdown(
                                                            f"**Public:** {'Yes' if template.is_public else 'No'}"
                                                        )

                                                    # Show tags
                                                    if template.tags:
                                                        tag_text = ", ".join(
                                                            f"**{tag}**" if tag in result.matched_tags else tag
                                                            for tag in template.tags
                                                        )
                                                        st.markdown(f"**Tags:** {tag_text}")

                                                    # Show matched fields
                                                    if result.matched_fields:
                                                        st.markdown(
                                                            "**Matched:** " +
                                                            ", ".join(sorted(result.matched_fields))
                                                        )

                                                    # Template selection
                                                    if st.button("Select Template", key=template.id):
                                                        template_id = template.id
                                                        template_config = self.template_cloud.download_template(template_id)
                                                        st.success(f"Selected template: {template.name}")

                                            if not template_config:
                                                st.info("Select a template to continue.")
                                                template = None

                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.markdown(f"**Author:** {template.author}")
                                                st.markdown(f"**Version:** {template.version}")
                                            with col2:
                                                st.markdown(
                                                    f"**Updated:** {template.updated_at.strftime('%Y-%m-%d %H:%M')}"
                                                )
                                                st.markdown(
                                                    f"**Public:** {'Yes' if template.is_public else 'No'}"
                                                )

                                            if template.tags:
                                                st.markdown(f"**Tags:** {', '.join(template.tags)}")

                                        # Analytics
                                        with st.expander("Analytics"):
                                            try:
                                                # Time range selector
                                                time_range = st.selectbox(
                                                    "Time Range",
                                                    options=list(TimeRange),
                                                    format_func=lambda x: {
                                                        TimeRange.LAST_24H: "Last 24 Hours",
                                                        TimeRange.LAST_7D: "Last 7 Days",
                                                        TimeRange.LAST_30D: "Last 30 Days",
                                                        TimeRange.LAST_90D: "Last 90 Days",
                                                        TimeRange.ALL_TIME: "All Time",
                                                    }[x],
                                                )
                                                
                                                # Get metrics
                                                metrics = self.analytics.get_metrics(
                                                    template_id=template_id,
                                                    time_range=time_range,
                                                )
                                                
                                                # Display metrics
                                                col1, col2, col3 = st.columns(3)
                                                
                                                with col1:
                                                    st.metric("Total Views", metrics.total_views)
                                                    st.metric("Unique Views", metrics.unique_views)
                                                
                                                with col2:
                                                    st.metric("Exports", metrics.total_exports)
                                                    st.metric("Shares", metrics.total_shares)
                                                
                                                with col3:
                                                    st.metric("Favorites", metrics.favorites)
                                                    st.metric("Copies", metrics.copies)
                                                
                                                if metrics.avg_view_duration_ms:
                                                    st.metric(
                                                        "Avg. View Duration",
                                                        f"{metrics.avg_view_duration_ms/1000:.1f}s",
                                                    )
                                                
                                                # Top merchants
                                                if metrics.top_merchants:
                                                    st.markdown("### Top Users")
                                                    for merchant, count in metrics.top_merchants:
                                                        st.markdown(f"- {merchant}: {count} events")
                                                
                                                # Popular tags
                                                if metrics.popular_tags:
                                                    st.markdown("### Popular Tags")
                                                    for tag, count in metrics.popular_tags:
                                                        st.markdown(f"- {tag}: {count} uses")
                                                
                                                # Trend score
                                                st.metric(
                                                    "Trend Score",
                                                    f"{metrics.trend_score:.1f}",
                                                    help="Higher score indicates more recent activity",
                                                )
                                            except ValueError as e:
                                                st.info("No analytics data available yet.")
                                        
                                        # Version control
                                        with st.expander("Version History"):
                                            try:
                                                changes = self.version_control.get_changes(template_id)
                                                versions = self.version_control.get_template_versions(template_id)
                                                
                                                # Version list
                                                st.markdown("### Template Versions")
                                                for version in reversed(versions):
                                                    with st.expander(
                                                        f"Version {version.version} - {version.created_at.strftime('%Y-%m-%d %H:%M')}",
                                                        expanded=version == versions[-1],
                                                    ):
                                                        st.markdown(f"**Author:** {version.author}")
                                                        st.markdown(f"**Message:** {version.commit_message}")
                                                        
                                                        # Show changes
                                                        change = next(
                                                            (c for c in changes if c.new_version == version.version),
                                                            None
                                                        )
                                                        if change and change.diff:
                                                            with st.expander("View Changes"):
                                                                st.code(change.diff, language="diff")
                                                        
                                                        # Show metadata changes
                                                        if change and change.metadata_changes:
                                                            st.markdown("**Metadata Changes:**")
                                                            for field, (old, new) in change.metadata_changes.items():
                                                                st.markdown(f"- {field}: {old} → {new}")
                                                        
                                                        # Version actions
                                                        col1, col2 = st.columns(2)
                                                        with col1:
                                                            if version != versions[-1]:
                                                                if st.button(
                                                                    "Restore Version",
                                                                    key=f"restore_{version.version}",
                                                                ):
                                                                    try:
                                                                        self.version_control.rollback(
                                                                            template_id=template_id,
                                                                            version=version.version,
                                                                            author=self.merchant_id,
                                                                        )
                                                                        st.success(f"Restored version {version.version}")
                                                                        st.rerun()
                                                                    except ValueError as e:
                                                                        st.error(f"Restore failed: {str(e)}")
                                                        
                                                        with col2:
                                                            if version != versions[-1]:
                                                                if st.button(
                                                                    "Compare with Current",
                                                                    key=f"compare_{version.version}",
                                                                ):
                                                                    diff, metadata = self.version_control.compare_versions(
                                                                        template_id=template_id,
                                                                        version1=version.version,
                                                                        version2=versions[-1].version,
                                                                    )
                                                                    st.code(diff, language="diff")
                                                                    
                                                                    if metadata:
                                                                        st.markdown("**Metadata Differences:**")
                                                                        for field, (old, new) in metadata.items():
                                                                            st.markdown(f"- {field}: {old} → {new}")
                                            except ValueError as e:
                                                st.info("No version history available yet.")
                                        
                                        # Cloud template management
                                        with st.expander("Cloud Management"):
                                            # Upload template
                                            if template_config:
                                                col1, col2 = st.columns(2)
                                                with col1:
                                                    is_public = st.checkbox(
                                                        "Make Public",
                                                        value=template.is_public
                                                        if "template" in locals()
                                                        else False,
                                                    )
                                                with col2:
                                                    tags = st.text_input(
                                                        "Tags",
                                                        value=",".join(template.tags)
                                                        if "template" in locals() and template.tags
                                                        else "",
                                                        help="Comma-separated tags",
                                                    )

                                                commit_message = st.text_area(
                                                    "Commit Message",
                                                    help="Describe your changes",
                                                )
                                                
                                                if st.button("Update in Cloud"):
                                                    try:
                                                        # Update cloud template
                                                        self.template_cloud.update_template(
                                                            template_id=template_id,
                                                            template=template_config,
                                                            is_public=is_public,
                                                            tags=[
                                                                t.strip()
                                                                for t in tags.split(",")
                                                                if t.strip()
                                                            ],
                                                        )
                                                        
                                                        # Create new version
                                                        self.version_control.create_version(
                                                            template_id=template_id,
                                                            content=template_config,
                                                            author=self.merchant_id,
                                                            commit_message=commit_message or "Updated template",
                                                            tags=set(
                                                                t.strip()
                                                                for t in tags.split(",")
                                                                if t.strip()
                                                            ),
                                                            is_public=is_public,
                                                        )
                                                        
                                                        # Record analytics
                                                        self.analytics.record_event(
                                                            template_id=template_id,
                                                            merchant_id=self.merchant_id,
                                                            event_type=EventType.EDIT,
                                                            metadata={
                                                                "tags": tags,
                                                                "is_public": str(is_public),
                                                            },
                                                        )
                                                        
                                                        st.success("Template updated in cloud")
                                                        st.rerun()
                                                    except ValueError as e:
                                                        st.error(f"Update failed: {str(e)}")

                                            # Upload new template
                                            st.markdown("### Upload New Template")
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                upload_name = st.text_input(
                                                    "Template Name",
                                                    help="Name for the new template",
                                                )
                                            with col2:
                                                upload_public = st.checkbox(
                                                    "Public Template",
                                                    help="Make template public",
                                                )

                                            upload_desc = st.text_area(
                                                "Description",
                                                help="Template description",
                                            )
                                            upload_tags = st.text_input(
                                                "Tags",
                                                help="Comma-separated tags",
                                            )

                                            initial_message = st.text_area(
                                                "Initial Commit Message",
                                                value="Initial version",
                                                help="Describe the initial version",
                                            )
                                            
                                            if st.button("Upload to Cloud"):
                                                try:
                                                    # Upload to cloud
                                                    template = self.template_cloud.upload_template(
                                                        template=template_config,
                                                        name=upload_name,
                                                        description=upload_desc,
                                                        is_public=upload_public,
                                                        tags=[
                                                            t.strip()
                                                            for t in upload_tags.split(",")
                                                            if t.strip()
                                                        ],
                                                    )
                                                    
                                                    # Create initial version
                                                    self.version_control.create_version(
                                                        template_id=template.id,
                                                        content=template_config,
                                                        author=self.merchant_id,
                                                        commit_message=initial_message,
                                                        tags=set(
                                                            t.strip()
                                                            for t in upload_tags.split(",")
                                                            if t.strip()
                                                        ),
                                                        is_public=upload_public,
                                                    )
                                                    
                                                    # Record analytics
                                                    self.analytics.record_event(
                                                        template_id=template.id,
                                                        merchant_id=self.merchant_id,
                                                        event_type=EventType.SHARE,
                                                        metadata={
                                                            "tags": upload_tags,
                                                            "is_public": str(upload_public),
                                                            "name": upload_name,
                                                            "description": upload_desc,
                                                        },
                                                    )
                                                    
                                                    st.success("Template uploaded to cloud")
                                                    st.rerun()
                                                except ValueError as e:
                                                    st.error(f"Upload failed: {str(e)}")

                                            # Sync templates
                                            st.markdown("### Sync Templates")
                                            if st.button("Sync Now") or sync_auto:
                                                with st.spinner("Syncing templates..."):
                                                    try:
                                                        sync_status = self.template_cloud.sync_local(
                                                            library_dir="templates/shared",
                                                            download_public=True,
                                                        )
                                                        st.success("Templates synced successfully")
                                                        st.markdown(
                                                            "### Sync Status\n" + 
                                                            "\n".join(
                                                                f"- {k}: {v}"
                                                                for k, v in sync_status.items()
                                                            )
                                                        )
                                                    except Exception as e:
                                                        st.error(f"Sync failed: {str(e)}")

                            if template_source == "custom":
                                with st.expander("Customize Template", expanded=True):
                                    # Basic settings
                                    table_style = st.selectbox(
                                        "Table Style",
                                        options=list(TableStyle),
                                        format_func=lambda x: x.value.title(),
                                    )

                                    color_scheme = st.selectbox(
                                        "Color Scheme",
                                        options=list(ColorScheme),
                                        format_func=lambda x: x.value.title(),
                                    )

                                    chart_theme = st.selectbox(
                                        "Chart Theme",
                                        options=list(ChartTheme),
                                        format_func=lambda x: x.value.replace('_', ' ').title(),
                                    )

                                    # Advanced settings
                                    if st.checkbox("Advanced Settings"):
                                        # Font settings
                                        st.subheader("Font Settings")
                                        font_family = st.text_input(
                                            "Font Family",
                                            value="system-ui, -apple-system, sans-serif",
                                        )
                                        font_size = st.slider(
                                            "Base Font Size",
                                            min_value=12,
                                            max_value=24,
                                            value=16,
                                        )

                                        # Color settings
                                        st.subheader("Color Settings")
                                        if color_scheme == ColorScheme.CUSTOM:
                                            primary_color = st.color_picker(
                                                "Primary Color",
                                                value="#3B82F6",
                                            )
                                            secondary_color = st.color_picker(
                                                "Secondary Color",
                                                value="#6B7280",
                                            )

                                        # Chart settings
                                        st.subheader("Chart Settings")
                                        chart_height = st.slider(
                                            "Chart Height",
                                            min_value=200,
                                            max_value=800,
                                            value=400,
                                            step=50,
                                        )
                                        show_grid = st.checkbox(
                                            "Show Grid",
                                            value=True,
                                        )

                                        # Metrics settings
                                        st.subheader("Metrics Settings")
                                        decimal_places = st.number_input(
                                            "Decimal Places",
                                            min_value=0,
                                            max_value=4,
                                            value=1,
                                        )
                                        compact_numbers = st.checkbox(
                                            "Compact Numbers",
                                            value=False,
                                        )

                                        # Create custom template config
                                        template_config = TemplateConfig(
                                            name="Custom",
                                            description="Custom template configuration",
                                            fonts=FontConfig(
                                                family=font_family,
                                                size_base=font_size,
                                                size_title=font_size * 2,
                                                size_heading=int(font_size * 1.5),
                                                size_subheading=int(font_size * 1.25),
                                                size_text=font_size,
                                            ),
                                            colors=ColorConfig(
                                                primary=primary_color if color_scheme == ColorScheme.CUSTOM else "#3B82F6",
                                                secondary=secondary_color if color_scheme == ColorScheme.CUSTOM else "#6B7280",
                                            ),
                                            charts=ChartConfig(
                                                theme=chart_theme,
                                                height=chart_height,
                                                show_grid=show_grid,
                                            ),
                                            metrics=MetricsConfig(
                                                decimal_places=decimal_places,
                                                compact_numbers=compact_numbers,
                                            ),
                                            table_style=table_style,
                                        )
                            else:
                                # Use preset configuration
                                template_config = TEMPLATE_PRESETS[preset_key].config
                                st.markdown(
                                    f"*{TEMPLATE_PRESETS[preset_key].description}*",
                                    help="Preset description",
                                )

                                # Show preview if available
                                if TEMPLATE_PRESETS[preset_key].preview_image:
                                    st.image(
                                        TEMPLATE_PRESETS[preset_key].preview_image,
                                        caption="Template Preview",
                                        use_column_width=True,
                                    )

                    if st.button("Export"):
                        try:
                            output_path = self.result_exporter.export_results(
                                result=result,
                                format=export_format,
                                filename=export_name,
                                html_template=html_template,
                                template_config=template_config,
                            )
                            st.success(
                                f"Results exported to: {output_path.name}"
                            )
                            if export_format == ExportFormat.HTML:
                                st.markdown(
                                    f"""<a href="file://{output_path}" target="_blank">
                                    View Report</a>""",
                                    unsafe_allow_html=True,
                                )
                        except Exception as e:
                            st.error(f"Export failed: {str(e)}")

                # Results by rule
                st.subheader("Results by Rule")
                if not rule_metrics.empty:
                    # Rule chart
                    fig = px.bar(
                        rule_metrics,
                        x="Rule",
                        y="Total Alerts",
                        color="Category",
                        title="Alerts by Rule",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Rule metrics table with download
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.dataframe(
                            rule_metrics,
                            use_container_width=True,
                            hide_index=True,
                        )
                    with col2:
                        csv = rule_metrics.to_csv(index=False)
                        st.download_button(
                            "Download CSV",
                            data=csv,
                            file_name="rule_metrics.csv",
                            mime="text/csv",
                        )

                # Results by scenario
                st.subheader("Results by Scenario")
                if not scenario_metrics.empty:
                    fig = px.bar(
                        scenario_metrics,
                        x="Scenario",
                        y="Total Alerts",
                        title="Alerts by Scenario",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(
                        scenario_metrics,
                        use_container_width=True,
                        hide_index=True,
                    )

    def render_dashboard(self):
        """Render the alert dashboard."""
        st.title("EUDI-Connect Alert Dashboard")
        st.markdown("""
        Monitor and manage performance alerts in real-time.
        Updates every 30 seconds.
        """)

        # Sidebar navigation
        page = st.sidebar.radio(
            "Navigation",
            options=["Overview", "Rules Editor", "Rule Testing", "Batch Testing"],
        )

        if page == "Overview":
            # Alert statistics
            st.header("Alert Overview")
            self.render_alert_stats()

            # Alert visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Alert Timeline")
                timeline = self.create_alert_timeline()
                if timeline:
                    st.plotly_chart(timeline, use_container_width=True)
                else:
                    st.info("No alerts in the last 24 hours")

            with col2:
                st.subheader("Alert Frequency")
                heatmap = self.create_alert_heatmap()
                if heatmap:
                    st.plotly_chart(heatmap, use_container_width=True)
                else:
                    st.info("No alerts in the last 24 hours")

            # Active alerts table
            st.header("Active Alerts")
            active_alerts = self.alert_manager.history.get_active_alerts()
            if active_alerts:
                df = pd.DataFrame([
                    {
                        "Metric": a.metric_name,
                        "Severity": a.severity,
                        "Current Value": f"{a.current_value:.2f}",
                        "Threshold": f"{a.threshold_value:.2f}",
                        "Time": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for a in active_alerts
                ])
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("No active alerts")

        elif page == "Rules Editor":
            self.render_rules_editor()

        elif page == "Rule Testing":
            self.render_rule_testing()

        else:  # Batch Testing
            self.render_batch_testing()

        # Auto-refresh
        if st.sidebar.checkbox("Auto-refresh", value=True):
            st.empty()
            st.rerun()


if __name__ == "__main__":
    dashboard = AlertDashboard()
    dashboard.render_dashboard()
