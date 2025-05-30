"""Test result export system."""
import csv
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from tests.performance.alert_rules import AlertRule, MetricCategory, RuleManager
from tests.performance.batch_testing import BatchTestResult
from tests.performance.template_config import (
    DEFAULT_TEMPLATE,
    DETAILED_TEMPLATE,
    MINIMAL_TEMPLATE,
    TemplateConfig,
)


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class HtmlTemplate(str, Enum):
    """Available HTML report templates."""
    DEFAULT = "default"
    MINIMAL = "minimal"
    DETAILED = "detailed"


class ResultExporter:
    """Test result export system."""

    def __init__(
        self,
        rule_manager: RuleManager,
        export_dir: Path = Path("reports/exports"),
        template_dir: Path = Path("tests/performance/templates"),
    ):
        """Initialize result exporter."""
        self.rule_manager = rule_manager
        self.export_dir = export_dir
        self.template_dir = template_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def _create_html_template(self):
        """Create default HTML template if it doesn't exist."""
        template_path = self.template_dir / "report_template.html"
        if not template_path.exists():
            template = """<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .summary {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chart {
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
        }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>{{ description }}</p>
        <p>Generated: {{ timestamp }}</p>
    </div>

    <div class="summary">
        <h2>Test Summary</h2>
        <div class="metrics">
            <div class="metric-card">
                <h3>Total Tests</h3>
                <p>{{ total_tests }}</p>
            </div>
            <div class="metric-card">
                <h3>Successful Tests</h3>
                <p>{{ successful_tests }}</p>
            </div>
            <div class="metric-card">
                <h3>Failed Tests</h3>
                <p>{{ failed_tests }}</p>
            </div>
            <div class="metric-card">
                <h3>Total Alerts</h3>
                <p>{{ total_alerts }}</p>
            </div>
        </div>
    </div>

    <h2>Results by Rule</h2>
    <div class="chart" id="ruleChart">
        {{ rule_chart | safe }}
    </div>
    <table>
        <thead>
            <tr>
                {% for header in rule_headers %}
                <th>{{ header }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in rule_data %}
            <tr>
                {% for value in row %}
                <td>{{ value }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2>Results by Scenario</h2>
    <div class="chart" id="scenarioChart">
        {{ scenario_chart | safe }}
    </div>
    <table>
        <thead>
            <tr>
                {% for header in scenario_headers %}
                <th>{{ header }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in scenario_data %}
            <tr>
                {% for value in row %}
                <td>{{ value }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""
            template_path.write_text(template)

    def export_results(
        self,
        result: BatchTestResult,
        format: ExportFormat,
        filename: Optional[str] = None,
        html_template: HtmlTemplate = HtmlTemplate.DEFAULT,
    ) -> Path:
        """Export test results in specified format."""
        if not filename:
            filename = f"test_results_{result.start_time.strftime('%Y%m%d_%H%M%S')}"

        if format == ExportFormat.JSON:
            return self._export_json(result, filename)
        elif format == ExportFormat.CSV:
            return self._export_csv(result, filename)
        elif format == ExportFormat.HTML:
            return self._export_html(result, filename)
        elif format == ExportFormat.PDF:
            return self._export_pdf(result, filename)
        elif format == ExportFormat.EXCEL:
            return self._export_excel(result, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, result: BatchTestResult, filename: str) -> Path:
        """Export results as JSON."""
        output_path = self.export_dir / f"{filename}.json"
        with open(output_path, "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        return output_path

    def _export_csv(self, result: BatchTestResult, filename: str) -> Path:
        """Export results as CSV."""
        # Create directory for multiple CSV files
        output_dir = self.export_dir / filename
        output_dir.mkdir(exist_ok=True)

        # Export summary
        summary_path = output_dir / "summary.csv"
        with open(summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Tests", result.total_tests])
            writer.writerow(["Successful Tests", result.successful_tests])
            writer.writerow(["Failed Tests", result.failed_tests])
            writer.writerow(["Total Alerts", result.total_alerts])

        # Export rule results
        rule_path = output_dir / "rule_results.csv"
        rule_data = []
        for rule_id, results in result.results_by_rule.items():
            rule = self.rule_manager.get_rule(rule_id)
            if not rule:
                continue
            for r in results:
                metrics = r["metrics"]
                rule_data.append({
                    "Rule": rule.name,
                    "Category": rule.category,
                    "Total Alerts": metrics["total_alerts"],
                    "Alert Frequency": metrics["alert_frequency"],
                    "Mean Alert Interval": metrics["mean_alert_interval"],
                    "Max Value": metrics["max_value"],
                    "Min Value": metrics["min_value"],
                    "Mean Value": metrics["mean_value"],
                })
        pd.DataFrame(rule_data).to_csv(rule_path, index=False)

        # Export scenario results
        scenario_path = output_dir / "scenario_results.csv"
        scenario_data = []
        for scenario_name, results in result.results_by_scenario.items():
            for r in results:
                metrics = r["metrics"]
                scenario_data.append({
                    "Scenario": scenario_name,
                    "Total Alerts": metrics["total_alerts"],
                    "Alert Frequency": metrics["alert_frequency"],
                    "Mean Alert Interval": metrics["mean_alert_interval"],
                    "Max Value": metrics["max_value"],
                    "Min Value": metrics["min_value"],
                    "Mean Value": metrics["mean_value"],
                })
        pd.DataFrame(scenario_data).to_csv(scenario_path, index=False)

        return output_dir

    def _get_template_config(self, template: HtmlTemplate) -> TemplateConfig:
        """Get template configuration based on template type."""
        if template == HtmlTemplate.MINIMAL:
            return MINIMAL_TEMPLATE
        elif template == HtmlTemplate.DETAILED:
            return DETAILED_TEMPLATE
        return DEFAULT_TEMPLATE

    def _export_html(self, result: BatchTestResult, filename: str, template: HtmlTemplate = HtmlTemplate.DEFAULT) -> Path:
        """Export results as HTML report."""
        output_path = self.export_dir / f"{filename}.html"
        template_config = self._get_template_config(template)

        # Create rule chart
        rule_df = pd.DataFrame([
            {
                "Rule": self.rule_manager.get_rule(rule_id).name,
                "Category": self.rule_manager.get_rule(rule_id).category,
                "Total Alerts": sum(r["metrics"]["total_alerts"] for r in results),
            }
            for rule_id, results in result.results_by_rule.items()
            if self.rule_manager.get_rule(rule_id)
        ])

        # Configure rule chart
        rule_chart = px.bar(
            rule_df,
            x="Rule",
            y="Total Alerts",
            color="Category",
            title="Alerts by Rule",
            template=template_config.charts.theme,
            height=template_config.charts.height,
            color_discrete_sequence=template_config.charts.color_sequence,
        )
        if not template_config.charts.show_grid:
            rule_chart.update_layout(xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        rule_chart_json = plotly.utils.PlotlyJSONEncoder().encode(rule_chart)

        # Create scenario chart
        scenario_df = pd.DataFrame([
            {
                "Scenario": scenario_name,
                "Total Alerts": sum(r["metrics"]["total_alerts"] for r in results),
            }
            for scenario_name, results in result.results_by_scenario.items()
        ])

        # Configure scenario chart
        scenario_chart = px.bar(
            scenario_df,
            x="Scenario",
            y="Total Alerts",
            title="Alerts by Scenario",
            template=template_config.charts.theme,
            height=template_config.charts.height,
            color_discrete_sequence=template_config.charts.color_sequence,
        )
        if not template_config.charts.show_grid:
            scenario_chart.update_layout(xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        scenario_chart_json = plotly.utils.PlotlyJSONEncoder().encode(scenario_chart)

        # Calculate metrics
        duration = (result.end_time - result.start_time).total_seconds()
        success_rate = (
            (result.successful_tests / result.total_tests * 100)
            if result.total_tests > 0
            else 0
        )
        rule_count = len(result.results_by_rule)
        category_count = len({self.rule_manager.get_rule(rule_id).category
                            for rule_id in result.results_by_rule.keys()
                            if self.rule_manager.get_rule(rule_id)})
        scenario_count = len(result.results_by_scenario)

        # Format numbers according to template config
        formatted_metrics = {
            "total_tests": template_config.format_number(result.total_tests),
            "successful_tests": template_config.format_number(result.successful_tests),
            "failed_tests": template_config.format_number(result.failed_tests),
            "total_alerts": template_config.format_number(result.total_alerts),
            "duration": template_config.format_number(duration) + "s",
            "success_rate": template_config.format_number(success_rate) + "%",
            "rule_count": template_config.format_number(rule_count),
            "category_count": template_config.format_number(category_count),
            "scenario_count": template_config.format_number(scenario_count),
        }

        # Prepare template data
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template(f"{template.value}.html")
        html = template.render(
            title=f"Test Results: {result.config.name}",
            description=result.config.description,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            config=template_config,
            metrics=formatted_metrics,
            rule_chart=rule_chart_json if template_config.metrics.show_charts else None,
            scenario_chart=scenario_chart_json if template_config.metrics.show_charts else None,
            rule_headers=rule_df.columns if template_config.metrics.show_tables else None,
            rule_data=rule_df.values.tolist() if template_config.metrics.show_tables else None,
            scenario_headers=scenario_df.columns if template_config.metrics.show_tables else None,
            scenario_data=scenario_df.values.tolist() if template_config.metrics.show_tables else None,
        )

        output_path.write_text(html)
        return output_path

    def _export_pdf(self, result: BatchTestResult, filename: str) -> Path:
        """Export results as PDF report."""
        # First create HTML
        html_path = self._export_html(result, filename)
        pdf_path = self.export_dir / f"{filename}.pdf"

        # Convert HTML to PDF using weasyprint
        try:
            import weasyprint
            weasyprint.HTML(html_path).write_pdf(pdf_path)
        except ImportError:
            raise ImportError(
                "weasyprint is required for PDF export. "
                "Install it with: pip install weasyprint"
            )

        return pdf_path

    def _export_excel(self, result: BatchTestResult, filename: str) -> Path:
        """Export results as Excel workbook."""
        output_path = self.export_dir / f"{filename}.xlsx"

        with pd.ExcelWriter(output_path) as writer:
            # Summary sheet
            summary_data = {
                "Metric": [
                    "Total Tests",
                    "Successful Tests",
                    "Failed Tests",
                    "Total Alerts",
                ],
                "Value": [
                    result.total_tests,
                    result.successful_tests,
                    result.failed_tests,
                    result.total_alerts,
                ],
            }
            pd.DataFrame(summary_data).to_excel(
                writer,
                sheet_name="Summary",
                index=False,
            )

            # Rule results
            rule_data = []
            for rule_id, results in result.results_by_rule.items():
                rule = self.rule_manager.get_rule(rule_id)
                if not rule:
                    continue
                for r in results:
                    metrics = r["metrics"]
                    rule_data.append({
                        "Rule": rule.name,
                        "Category": rule.category,
                        "Total Alerts": metrics["total_alerts"],
                        "Alert Frequency": metrics["alert_frequency"],
                        "Mean Alert Interval": metrics["mean_alert_interval"],
                        "Max Value": metrics["max_value"],
                        "Min Value": metrics["min_value"],
                        "Mean Value": metrics["mean_value"],
                    })
            pd.DataFrame(rule_data).to_excel(
                writer,
                sheet_name="Rule Results",
                index=False,
            )

            # Scenario results
            scenario_data = []
            for scenario_name, results in result.results_by_scenario.items():
                for r in results:
                    metrics = r["metrics"]
                    scenario_data.append({
                        "Scenario": scenario_name,
                        "Total Alerts": metrics["total_alerts"],
                        "Alert Frequency": metrics["alert_frequency"],
                        "Mean Alert Interval": metrics["mean_alert_interval"],
                        "Max Value": metrics["max_value"],
                        "Min Value": metrics["min_value"],
                        "Mean Value": metrics["mean_value"],
                    })
            pd.DataFrame(scenario_data).to_excel(
                writer,
                sheet_name="Scenario Results",
                index=False,
            )

        return output_path
