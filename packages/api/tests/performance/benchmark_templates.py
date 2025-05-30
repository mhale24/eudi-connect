"""Template performance benchmarking utility.

This module provides benchmarking tools to measure template rendering
performance against the EUDI-Connect performance targets:
- MVP: ≤800ms P95 credential exchange latency
- Future: ≤300ms performance target

Usage:
    python benchmark_templates.py --num-templates 5 --num-alerts 100 --iterations 3
"""
import argparse
import json
import logging
import statistics
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from test_templates_standalone import (
    Alert,
    AlertSeverity,
    AlertType,
    NotificationTemplate,
    TemplateFormat,
    TemplateManager,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("template_benchmark")


class TemplateBenchmark:
    """Benchmark utility for template rendering performance."""

    def __init__(self, merchant_id: str = "benchmark_merchant"):
        """Initialize benchmark utility.
        
        Args:
            merchant_id: Optional merchant ID to use for templates
        """
        # Create mock Supabase client
        self.mock_supabase = self._create_mock_supabase()
        
        # Create template manager
        self.template_manager = TemplateManager(
            supabase_client=self.mock_supabase,
            merchant_id=merchant_id,
        )
        
        # Performance targets in milliseconds
        self.targets = {
            "mvp": 800,
            "future": 300,
            "template_render": 10,  # Target for individual template render time
        }
        
        # Results storage
        self.results = []
        
    def _create_mock_supabase(self):
        """Create a mock Supabase client for testing."""
        # This is a simplified mock that returns pre-defined data
        class MockSubase:
            def table(self, name):
                return self
                
            def select(self):
                return self
                
            def eq(self, field, value):
                return self
                
            def execute(self):
                return {"data": []}
                
            def insert(self, data):
                return self
                
        return MockSubase()
        
    def create_sample_template(self, index: int) -> NotificationTemplate:
        """Create a sample template for benchmarking.
        
        Args:
            index: Template index for unique naming
            
        Returns:
            Sample notification template
        """
        return NotificationTemplate(
            id=f"benchmark_template_{index}",
            merchant_id="benchmark_merchant",
            name=f"Benchmark Template {index}",
            description=f"Template for benchmarking performance #{index}",
            alert_types=[AlertType.USAGE_SPIKE],
            min_severity=AlertSeverity.WARNING,
            subject_template="Benchmark Alert: {title}",
            html_template="""<html>
                <body>
                    <h1>{title}</h1>
                    <p>{description}</p>
                    <p>Value: {metric_value}</p>
                    <p>Threshold: {threshold_value}</p>
                    <p>Severity: {severity}</p>
                    <p>Type: {alert_type}</p>
                    <p>Created: {created_at}</p>
                </body>
            </html>""",
            plain_template="""{title}
            {description}
            Value: {metric_value}
            Threshold: {threshold_value}
            Severity: {severity}
            Type: {alert_type}
            Created: {created_at}""",
            slack_template="""*{title}*
            {description}
            Value: {metric_value}
            Threshold: {threshold_value}
            Severity: {severity}
            Type: {alert_type}
            Created: {created_at}""",
            webhook_template=json.dumps({
                "title": "{title}",
                "description": "{description}",
                "value": "{metric_value}",
                "threshold": "{threshold_value}",
                "severity": "{severity}",
                "type": "{alert_type}",
                "created": "{created_at}",
            }, indent=2),
        )
        
    def create_sample_alert(self, index: int) -> Alert:
        """Create a sample alert for benchmarking.
        
        Args:
            index: Alert index for unique identification
            
        Returns:
            Sample alert instance
        """
        return Alert(
            id=f"benchmark_alert_{index}",
            title=f"Benchmark Alert {index}",
            description=f"Alert generated for benchmarking #{index}",
            alert_type=AlertType.USAGE_SPIKE,
            severity=AlertSeverity.WARNING,
            created_at=datetime.now(timezone.utc),
            metric_value=150.0 + index,
            threshold_value=100.0,
            template_id=f"benchmark_template_{index % 5}",  # Cycle through templates
            tag=f"benchmark_tag_{index % 10}",
            metadata={"benchmark": True, "index": index},
        )
        
    def benchmark_template_creation(self, num_templates: int = 5) -> Dict:
        """Benchmark template creation performance.
        
        Args:
            num_templates: Number of templates to create
            
        Returns:
            Performance metrics dictionary
        """
        logger.info(f"Benchmarking creation of {num_templates} templates...")
        
        # Setup templates
        templates = [self.create_sample_template(i) for i in range(num_templates)]
        
        # Setup mock response
        self.mock_supabase.execute = lambda: {"data": [templates[0].dict()]}
        
        # Benchmark creation
        timings = []
        for template in templates:
            start_time = time.time()
            
            # Create template - exclude id and merchant_id fields
            template_data = template.dict()
            template_data.pop('id', None)
            template_data.pop('merchant_id', None)
            self.template_manager.create_template(**template_data)
            
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000
            timings.append(elapsed_ms)
            
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Template creation metrics: {metrics}")
        return metrics
        
    def benchmark_single_template_render(
        self, 
        num_alerts: int = 100,
        template_index: int = 0,
        format: TemplateFormat = TemplateFormat.HTML,
    ) -> Dict:
        """Benchmark single template rendering performance.
        
        Args:
            num_alerts: Number of alerts to render
            template_index: Index of template to use
            format: Template format to render
            
        Returns:
            Performance metrics dictionary
        """
        logger.info(f"Benchmarking rendering of {num_alerts} alerts with template {template_index}...")
        
        # Setup template and alerts
        template = self.create_sample_template(template_index)
        alerts = [self.create_sample_alert(i) for i in range(num_alerts)]
        
        # Setup mock response for template retrieval
        self.mock_supabase.execute = lambda: {"data": [template.dict()]}
        
        # Measure individual render times
        individual_timings = []
        for alert in alerts:
            start_time = time.time()
            self.template_manager.render_template(
                template_id=template.id,
                format=format,
                alert=alert,
            )
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000
            individual_timings.append(elapsed_ms)
            
        # Measure batch render time
        batch_start_time = time.time()
        self.template_manager.render_batch(
            template_id=template.id,
            format=format,
            alerts=alerts,
        )
        batch_end_time = time.time()
        batch_elapsed_ms = (batch_end_time - batch_start_time) * 1000
        
        # Calculate metrics
        individual_metrics = self._calculate_metrics(individual_timings)
        
        # Calculate batch metrics and efficiency
        avg_individual = individual_metrics["mean"]
        theoretical_batch = avg_individual * num_alerts
        batch_efficiency = (theoretical_batch / batch_elapsed_ms) * 100
        
        # Combined metrics
        metrics = {
            **individual_metrics,
            "batch_total_ms": batch_elapsed_ms,
            "batch_per_item_ms": batch_elapsed_ms / num_alerts,
            "batch_efficiency_percent": batch_efficiency,
        }
        
        logger.info(f"Single template render metrics ({format.value}): {metrics}")
        return metrics
        
    def benchmark_multi_template_render(
        self,
        num_templates: int = 5,
        num_alerts_per_template: int = 20,
        formats: List[TemplateFormat] = None,
    ) -> Dict[str, Dict]:
        """Benchmark rendering with multiple templates.
        
        Args:
            num_templates: Number of templates to use
            num_alerts_per_template: Number of alerts per template
            formats: List of formats to benchmark (defaults to all)
            
        Returns:
            Dictionary of metrics by format
        """
        if formats is None:
            formats = [
                TemplateFormat.HTML, 
                TemplateFormat.PLAIN, 
                TemplateFormat.SLACK, 
                TemplateFormat.WEBHOOK_JSON
            ]
            
        logger.info(f"Benchmarking multi-template rendering with {num_templates} templates...")
        
        # Results by format
        results_by_format = {}
        
        for format in formats:
            format_results = []
            
            # Test each template
            for i in range(num_templates):
                metrics = self.benchmark_single_template_render(
                    num_alerts=num_alerts_per_template,
                    template_index=i,
                    format=format,
                )
                format_results.append(metrics)
                
            # Aggregate metrics across templates
            aggregated = self._aggregate_metrics(format_results)
            results_by_format[format.value] = aggregated
            
        return results_by_format
        
    def _calculate_metrics(self, timings: List[float]) -> Dict:
        """Calculate performance metrics from timing data.
        
        Args:
            timings: List of timing measurements in milliseconds
            
        Returns:
            Dictionary of performance metrics
        """
        if not timings:
            return {}
            
        # Sort timings for percentile calculations
        sorted_timings = sorted(timings)
        
        # Calculate metrics
        return {
            "mean": statistics.mean(timings),
            "median": statistics.median(timings),
            "min": min(timings),
            "max": max(timings),
            "p95": sorted_timings[int(len(sorted_timings) * 0.95)],
            "p99": sorted_timings[int(len(sorted_timings) * 0.99)],
            "stddev": statistics.stdev(timings) if len(timings) > 1 else 0,
            "samples": len(timings),
        }
        
    def _aggregate_metrics(self, metrics_list: List[Dict]) -> Dict:
        """Aggregate metrics from multiple runs.
        
        Args:
            metrics_list: List of metrics dictionaries
            
        Returns:
            Aggregated metrics
        """
        if not metrics_list:
            return {}
            
        # Extract specific metrics to aggregate
        keys_to_aggregate = [
            "mean", "median", "min", "max", "p95", "p99", 
            "batch_total_ms", "batch_per_item_ms"
        ]
        
        aggregated = {}
        for key in keys_to_aggregate:
            values = [m.get(key, 0) for m in metrics_list if key in m]
            if values:
                aggregated[f"{key}_avg"] = statistics.mean(values)
                aggregated[f"{key}_min"] = min(values)
                aggregated[f"{key}_max"] = max(values)
                
        # Include total samples
        aggregated["total_samples"] = sum(m.get("samples", 0) for m in metrics_list)
        
        return aggregated
        
    def run_full_benchmark(
        self,
        num_templates: int = 5,
        num_alerts: int = 100,
        iterations: int = 3,
    ) -> Dict:
        """Run a complete benchmark suite.
        
        Args:
            num_templates: Number of templates to create
            num_alerts: Total number of alerts to process
            iterations: Number of benchmark iterations
            
        Returns:
            Comprehensive benchmark results
        """
        logger.info(f"Running full benchmark suite ({iterations} iterations)...")
        results = {
            "creation": [],
            "rendering": {},
            "system_info": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "num_templates": num_templates,
                "num_alerts": num_alerts,
                "iterations": iterations,
                "performance_targets": self.targets,
            }
        }
        
        # Initialize format results
        for format in [f.value for f in [
            TemplateFormat.HTML, 
            TemplateFormat.PLAIN, 
            TemplateFormat.SLACK, 
            TemplateFormat.WEBHOOK_JSON
        ]]:
            results["rendering"][format] = []
        
        # Run multiple iterations
        for i in range(iterations):
            logger.info(f"Starting benchmark iteration {i+1}/{iterations}")
            
            # Reset cache between iterations
            self.template_manager.invalidate_cache()
            
            # Benchmark template creation
            creation_metrics = self.benchmark_template_creation(num_templates)
            results["creation"].append(creation_metrics)
            
            # Benchmark rendering with different formats
            render_results = self.benchmark_multi_template_render(
                num_templates=num_templates,
                num_alerts_per_template=num_alerts // num_templates,
            )
            
            # Store rendering results
            for format, metrics in render_results.items():
                results["rendering"][format].append(metrics)
                
        # Final aggregated results
        final_results = {
            "creation": self._aggregate_metrics(results["creation"]),
            "rendering": {},
            "system_info": results["system_info"],
        }
        
        for format in results["rendering"]:
            final_results["rendering"][format] = self._aggregate_metrics(
                results["rendering"][format]
            )
            
        # Check against performance targets
        meets_targets = self._check_performance_targets(final_results)
        final_results["meets_targets"] = meets_targets
        
        return final_results
        
    def _check_performance_targets(self, results: Dict) -> Dict[str, bool]:
        """Check if results meet performance targets.
        
        Args:
            results: Benchmark results
            
        Returns:
            Dictionary of target check results
        """
        target_checks = {}
        
        # Check template rendering against 10ms target
        render_p95_avg = results["rendering"]["html"].get("p95_avg", float("inf"))
        target_checks["template_render"] = render_p95_avg <= self.targets["template_render"]
        
        # Check batch rendering efficiency
        html_batch_per_item = results["rendering"]["html"].get("batch_per_item_ms_avg", float("inf"))
        target_checks["mvp_latency"] = html_batch_per_item <= self.targets["mvp"]
        target_checks["future_latency"] = html_batch_per_item <= self.targets["future"]
        
        return target_checks
        
    def save_results(self, results: Dict, filename: str = None) -> str:
        """Save benchmark results to file.
        
        Args:
            results: Benchmark results dictionary
            filename: Optional filename (defaults to timestamp-based name)
            
        Returns:
            Path to saved results file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"template_benchmark_{timestamp}.json"
            
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Benchmark results saved to {filename}")
        return filename


def main():
    """Run benchmark as a command-line tool."""
    parser = argparse.ArgumentParser(description="Template rendering performance benchmark")
    parser.add_argument("--num-templates", type=int, default=5, help="Number of templates")
    parser.add_argument("--num-alerts", type=int, default=100, help="Number of alerts")
    parser.add_argument("--iterations", type=int, default=3, help="Benchmark iterations")
    parser.add_argument("--output", type=str, help="Output file path")
    args = parser.parse_args()
    
    benchmark = TemplateBenchmark()
    results = benchmark.run_full_benchmark(
        num_templates=args.num_templates,
        num_alerts=args.num_alerts,
        iterations=args.iterations,
    )
    
    benchmark.save_results(results, args.output)
    
    # Print summary
    print("\n=== BENCHMARK SUMMARY ===")
    print(f"Templates: {args.num_templates}, Alerts: {args.num_alerts}, Iterations: {args.iterations}")
    
    # Print creation metrics if available
    print("\nTemplate Creation:")
    if 'creation' in results and results['creation']:
        # Handle single iteration case where no averaging happened
        if 'mean_avg' in results['creation']:
            print(f"  Average: {results['creation']['mean_avg']:.2f}ms")
        elif 'mean' in results['creation']:
            print(f"  Average: {results['creation']['mean']:.2f}ms")
        else:
            print("  Average: N/A")
            
        if 'p95_avg' in results['creation']:
            print(f"  P95: {results['creation']['p95_avg']:.2f}ms")
        elif 'p95' in results['creation']:
            print(f"  P95: {results['creation']['p95']:.2f}ms")
        else:
            print("  P95: N/A")
    else:
        print("  No creation metrics available")
    
    # Print HTML rendering metrics if available
    print("\nTemplate Rendering (HTML):")
    if 'rendering' in results and 'html' in results['rendering'] and results['rendering']['html']:
        html_results = results['rendering']['html']
        
        # Handle single vs aggregated metrics
        if 'mean_avg' in html_results:
            print(f"  Single Average: {html_results['mean_avg']:.2f}ms")
        elif 'mean' in html_results:
            print(f"  Single Average: {html_results['mean']:.2f}ms")
        else:
            print("  Single Average: N/A")
            
        if 'p95_avg' in html_results:
            print(f"  Single P95: {html_results['p95_avg']:.2f}ms")
        elif 'p95' in html_results:
            print(f"  Single P95: {html_results['p95']:.2f}ms")
        else:
            print("  Single P95: N/A")
            
        if 'batch_per_item_ms_avg' in html_results:
            print(f"  Batch Per Item: {html_results['batch_per_item_ms_avg']:.2f}ms")
        elif 'batch_per_item_ms' in html_results:
            print(f"  Batch Per Item: {html_results['batch_per_item_ms']:.2f}ms")
        else:
            print("  Batch Per Item: N/A")
    else:
        print("  No HTML rendering metrics available")
    
    # Print performance target results if available
    print("\nPerformance Targets:")
    if 'meets_targets' in results:
        for target, achieved in results["meets_targets"].items():
            status = "✅ PASS" if achieved else "❌ FAIL"
            print(f"  {target}: {status}")
    else:
        print("  No target metrics available")


if __name__ == "__main__":
    main()
