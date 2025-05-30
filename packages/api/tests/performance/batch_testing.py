"""Batch testing system for alert rules."""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
from pydantic import BaseModel

from tests.performance.alert_rules import AlertRule, MetricCategory, RuleManager
from tests.performance.alert_testing import RuleTester, TestScenario
from tests.performance.alerts import Alert, AlertManager


class BatchTestConfig(BaseModel):
    """Configuration for a batch test run."""
    name: str
    description: str
    rule_ids: Set[str] = set()
    rule_categories: Set[MetricCategory] = set()
    scenario_names: Set[str] = set()
    parallel_tests: int = 4
    save_results: bool = True


class BatchTestResult(BaseModel):
    """Results from a batch test run."""
    config: BatchTestConfig
    start_time: datetime
    end_time: datetime
    total_tests: int
    successful_tests: int
    failed_tests: int
    total_alerts: int
    results_by_rule: Dict[str, List[Dict]]
    results_by_scenario: Dict[str, List[Dict]]


class BatchTester:
    """Batch testing system for alert rules."""

    def __init__(
        self,
        rule_manager: RuleManager,
        alert_manager: AlertManager,
        results_dir: Path = Path("reports/batch_tests"),
    ):
        """Initialize batch tester."""
        self.rule_manager = rule_manager
        self.alert_manager = alert_manager
        self.rule_tester = RuleTester(rule_manager, alert_manager)
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _get_test_matrix(
        self,
        config: BatchTestConfig,
    ) -> List[Tuple[AlertRule, TestScenario]]:
        """Get all rule-scenario combinations to test."""
        # Get rules to test
        rules = []
        if config.rule_ids:
            rules.extend([
                r for r in self.rule_manager.get_rules()
                if r.id in config.rule_ids
            ])
        if config.rule_categories:
            for category in config.rule_categories:
                rules.extend(self.rule_manager.get_rules(category))
        if not rules and not config.rule_categories:
            rules = self.rule_manager.get_rules()

        # Get scenarios to test
        scenarios = self.rule_tester.get_test_scenarios()
        if config.scenario_names:
            scenarios = [
                s for s in scenarios
                if s.name in config.scenario_names
            ]

        # Create test matrix
        return [(rule, scenario) for rule in rules for scenario in scenarios]

    async def run_batch_test(
        self,
        config: BatchTestConfig,
    ) -> BatchTestResult:
        """Run a batch of tests."""
        start_time = datetime.utcnow()
        test_matrix = self._get_test_matrix(config)
        total_tests = len(test_matrix)

        if not total_tests:
            raise ValueError("No tests to run")

        # Initialize results
        results_by_rule: Dict[str, List[Dict]] = {}
        results_by_scenario: Dict[str, List[Dict]] = {}
        successful_tests = 0
        failed_tests = 0
        total_alerts = 0

        # Create thread pool for parallel testing
        with ThreadPoolExecutor(max_workers=config.parallel_tests) as executor:
            # Run tests in parallel
            futures = []
            for rule, scenario in test_matrix:
                future = executor.submit(
                    self.rule_tester.test_rule,
                    rule,
                    scenario,
                )
                futures.append((rule, scenario, future))

            # Process results as they complete
            for rule, scenario, future in futures:
                try:
                    df, alerts = future.result()
                    results = self.rule_tester.analyze_results(
                        df, alerts, rule, scenario,
                    )

                    # Save individual test results
                    if config.save_results:
                        self.rule_tester.save_results(results, scenario, rule)

                    # Aggregate results by rule
                    if rule.id not in results_by_rule:
                        results_by_rule[rule.id] = []
                    results_by_rule[rule.id].append(results)

                    # Aggregate results by scenario
                    if scenario.name not in results_by_scenario:
                        results_by_scenario[scenario.name] = []
                    results_by_scenario[scenario.name].append(results)

                    successful_tests += 1
                    total_alerts += len(alerts)

                except Exception as e:
                    print(f"Error testing {rule.name} with {scenario.name}: {e}")
                    failed_tests += 1

        end_time = datetime.utcnow()

        # Create batch result
        result = BatchTestResult(
            config=config,
            start_time=start_time,
            end_time=end_time,
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            total_alerts=total_alerts,
            results_by_rule=results_by_rule,
            results_by_scenario=results_by_scenario,
        )

        # Save batch results
        if config.save_results:
            self._save_batch_results(result)

        return result

    def _save_batch_results(self, result: BatchTestResult):
        """Save batch test results to file."""
        filename = (
            self.results_dir
            / f"batch_{result.config.name}_{result.start_time.isoformat()}.json"
        )
        with open(filename, "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)

    def analyze_batch_results(
        self,
        result: BatchTestResult,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze batch test results."""
        # Analysis by rule
        rule_metrics = []
        for rule_id, results in result.results_by_rule.items():
            rule = self.rule_manager.get_rule(rule_id)
            if not rule:
                continue

            metrics = {
                "Rule": rule.name,
                "Category": rule.category,
                "Total Tests": len(results),
                "Total Alerts": sum(r["metrics"]["total_alerts"] for r in results),
                "Avg Alerts/Test": sum(
                    r["metrics"]["total_alerts"] for r in results
                ) / len(results),
                "Avg Alert Interval": sum(
                    r["metrics"]["mean_alert_interval"] for r in results
                ) / len(results),
                "Max Value": max(r["metrics"]["max_value"] for r in results),
                "Min Value": min(r["metrics"]["min_value"] for r in results),
                "Avg Value": sum(
                    r["metrics"]["mean_value"] for r in results
                ) / len(results),
            }
            rule_metrics.append(metrics)

        # Analysis by scenario
        scenario_metrics = []
        for scenario_name, results in result.results_by_scenario.items():
            metrics = {
                "Scenario": scenario_name,
                "Total Tests": len(results),
                "Total Alerts": sum(r["metrics"]["total_alerts"] for r in results),
                "Avg Alerts/Test": sum(
                    r["metrics"]["total_alerts"] for r in results
                ) / len(results),
                "Avg Alert Interval": sum(
                    r["metrics"]["mean_alert_interval"] for r in results
                ) / len(results),
                "Max Value": max(r["metrics"]["max_value"] for r in results),
                "Min Value": min(r["metrics"]["min_value"] for r in results),
                "Avg Value": sum(
                    r["metrics"]["mean_value"] for r in results
                ) / len(results),
            }
            scenario_metrics.append(metrics)

        return (
            pd.DataFrame(rule_metrics),
            pd.DataFrame(scenario_metrics),
        )
