"""Alert rule testing and simulation system."""
import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel

from tests.performance.alert_rules import AlertRule, RuleManager
from tests.performance.alerts import Alert, AlertManager, AlertSeverity


class MetricPattern(str, Enum):
    """Patterns for generating test metric data."""
    CONSTANT = "constant"
    RANDOM = "random"
    SPIKE = "spike"
    GRADUAL = "gradual"
    OSCILLATING = "oscillating"
    STEP = "step"


class TestScenario(BaseModel):
    """Test scenario configuration."""
    name: str
    description: str
    duration_minutes: int
    metric_pattern: MetricPattern
    base_value: float
    variation: float = 0.1  # For random/oscillating patterns
    spike_probability: float = 0.05  # For spike pattern
    trend_direction: float = 1.0  # For gradual pattern (1.0 = up, -1.0 = down)
    step_changes: List[Tuple[int, float]] = []  # [(minute, new_value)]


class RuleTester:
    """Alert rule testing system."""

    def __init__(
        self,
        rule_manager: RuleManager,
        alert_manager: AlertManager,
        results_dir: Path = Path("reports/rule_tests"),
    ):
        """Initialize rule tester."""
        self.rule_manager = rule_manager
        self.alert_manager = alert_manager
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def generate_test_data(
        self,
        scenario: TestScenario,
        rule: AlertRule,
    ) -> pd.DataFrame:
        """Generate test metric data based on pattern."""
        timestamps = pd.date_range(
            start=datetime.utcnow(),
            periods=scenario.duration_minutes * 60,  # One point per second
            freq="s",
        )

        if scenario.metric_pattern == MetricPattern.CONSTANT:
            values = np.full(len(timestamps), scenario.base_value)

        elif scenario.metric_pattern == MetricPattern.RANDOM:
            values = np.random.normal(
                scenario.base_value,
                scenario.base_value * scenario.variation,
                len(timestamps),
            )

        elif scenario.metric_pattern == MetricPattern.SPIKE:
            values = np.full(len(timestamps), scenario.base_value)
            # Add random spikes
            spike_mask = np.random.random(len(timestamps)) < scenario.spike_probability
            spike_values = np.random.normal(
                scenario.base_value * 2,
                scenario.base_value * 0.5,
                sum(spike_mask),
            )
            values[spike_mask] = spike_values

        elif scenario.metric_pattern == MetricPattern.GRADUAL:
            slope = (
                scenario.base_value
                * scenario.variation
                * scenario.trend_direction
                / len(timestamps)
            )
            values = np.linspace(
                scenario.base_value,
                scenario.base_value * (1 + scenario.trend_direction * scenario.variation),
                len(timestamps),
            )

        elif scenario.metric_pattern == MetricPattern.OSCILLATING:
            t = np.linspace(0, 4 * np.pi, len(timestamps))
            values = scenario.base_value + (
                scenario.base_value
                * scenario.variation
                * np.sin(t)
            )

        elif scenario.metric_pattern == MetricPattern.STEP:
            values = np.full(len(timestamps), scenario.base_value)
            for minute, new_value in scenario.step_changes:
                if minute < scenario.duration_minutes:
                    start_idx = minute * 60
                    values[start_idx:] = new_value

        return pd.DataFrame({
            "timestamp": timestamps,
            "value": values,
        })

    def test_rule(
        self,
        rule: AlertRule,
        scenario: TestScenario,
    ) -> Tuple[pd.DataFrame, List[Alert]]:
        """Test a rule against a scenario."""
        # Generate test data
        df = self.generate_test_data(scenario, rule)
        alerts = []
        consecutive_violations = 0
        last_alert_time = None

        # Process each data point
        for _, row in df.iterrows():
            # Check cooldown period
            if last_alert_time and (
                row["timestamp"] - last_alert_time
            ).total_seconds() < rule.cooldown:
                continue

            # Check thresholds
            if rule.operator == "greater_than":
                if row["value"] >= rule.critical_threshold:
                    consecutive_violations += 1
                    severity = AlertSeverity.CRITICAL
                    threshold = rule.critical_threshold
                elif row["value"] >= rule.warning_threshold:
                    consecutive_violations += 1
                    severity = AlertSeverity.WARNING
                    threshold = rule.warning_threshold
                else:
                    consecutive_violations = 0
                    continue
            else:  # less_than
                if row["value"] <= rule.critical_threshold:
                    consecutive_violations += 1
                    severity = AlertSeverity.CRITICAL
                    threshold = rule.critical_threshold
                elif row["value"] <= rule.warning_threshold:
                    consecutive_violations += 1
                    severity = AlertSeverity.WARNING
                    threshold = rule.warning_threshold
                else:
                    consecutive_violations = 0
                    continue

            # Generate alert if enough consecutive violations
            if consecutive_violations >= rule.duration:
                alert = Alert(
                    id=f"test_{rule.id}_{len(alerts)}",
                    severity=severity,
                    metric_name=rule.metric,
                    current_value=row["value"],
                    threshold_value=threshold,
                    message=f"Test alert: {rule.metric} = {row['value']:.2f}",
                    timestamp=row["timestamp"],
                )
                alerts.append(alert)
                last_alert_time = row["timestamp"]
                consecutive_violations = 0

        return df, alerts

    def analyze_results(
        self,
        df: pd.DataFrame,
        alerts: List[Alert],
        rule: AlertRule,
        scenario: TestScenario,
    ) -> Dict:
        """Analyze test results."""
        total_duration = (df["timestamp"].max() - df["timestamp"].min()).total_seconds()
        total_points = len(df)
        points_above_warning = sum(df["value"] >= rule.warning_threshold)
        points_above_critical = sum(df["value"] >= rule.critical_threshold)
        
        alert_intervals = []
        for i in range(1, len(alerts)):
            interval = (
                alerts[i].timestamp - alerts[i-1].timestamp
            ).total_seconds()
            alert_intervals.append(interval)

        return {
            "scenario": scenario.dict(),
            "rule": rule.dict(),
            "metrics": {
                "total_duration_seconds": total_duration,
                "total_points": total_points,
                "total_alerts": len(alerts),
                "points_above_warning": points_above_warning,
                "points_above_critical": points_above_critical,
                "alert_frequency": len(alerts) / (total_duration / 60),  # alerts per minute
                "mean_alert_interval": np.mean(alert_intervals) if alert_intervals else 0,
                "min_value": df["value"].min(),
                "max_value": df["value"].max(),
                "mean_value": df["value"].mean(),
                "std_value": df["value"].std(),
            },
            "alerts": [a.dict() for a in alerts],
        }

    def save_results(self, results: Dict, scenario: TestScenario, rule: AlertRule):
        """Save test results to file."""
        filename = self.results_dir / f"{scenario.name}_{rule.id}_{datetime.utcnow().isoformat()}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        return filename

    def get_test_scenarios(self) -> List[TestScenario]:
        """Get predefined test scenarios."""
        return [
            TestScenario(
                name="Stable Baseline",
                description="Constant metric value with small random variations",
                duration_minutes=5,
                metric_pattern=MetricPattern.RANDOM,
                base_value=500,  # 500ms latency
                variation=0.05,
            ),
            TestScenario(
                name="Gradual Degradation",
                description="Gradually increasing metric value",
                duration_minutes=10,
                metric_pattern=MetricPattern.GRADUAL,
                base_value=500,
                variation=1.0,
                trend_direction=1.0,
            ),
            TestScenario(
                name="Sudden Spikes",
                description="Normal operation with occasional spikes",
                duration_minutes=15,
                metric_pattern=MetricPattern.SPIKE,
                base_value=500,
                spike_probability=0.05,
            ),
            TestScenario(
                name="Load Pattern",
                description="Oscillating load pattern",
                duration_minutes=20,
                metric_pattern=MetricPattern.OSCILLATING,
                base_value=500,
                variation=0.3,
            ),
            TestScenario(
                name="Service Degradation",
                description="Step changes in metric value",
                duration_minutes=15,
                metric_pattern=MetricPattern.STEP,
                base_value=500,
                step_changes=[
                    (5, 700),   # Warning at 5 minutes
                    (10, 900),  # Critical at 10 minutes
                ],
            ),
        ]
