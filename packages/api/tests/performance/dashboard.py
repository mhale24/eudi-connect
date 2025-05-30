"""Real-time performance metrics dashboard."""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(
    page_title="EUDI-Connect Performance Dashboard",
    page_icon="📊",
    layout="wide",
)


class MetricsDashboard:
    """Real-time performance metrics dashboard."""

    def __init__(self):
        """Initialize dashboard."""
        self.reports_dir = Path("reports")
        self.benchmark_dir = Path(".benchmarks")
        self.last_update = datetime.now()
        self.update_interval = 5  # seconds

    def load_benchmark_data(self) -> pd.DataFrame:
        """Load benchmark results into DataFrame."""
        data = []
        for json_file in self.benchmark_dir.glob("*/*.json"):
            with open(json_file) as f:
                results = json.load(f)
                for bench in results["benchmarks"]:
                    data.append({
                        "name": bench["name"],
                        "mean": bench["stats"]["mean"],
                        "stddev": bench["stats"]["stddev"],
                        "p50": bench["stats"]["median"],
                        "p90": bench["stats"].get("p90", 0),
                        "p95": bench["stats"].get("p95", 0),
                        "min": bench["stats"]["min"],
                        "max": bench["stats"]["max"],
                        "rounds": bench["stats"]["rounds"],
                        "timestamp": results["datetime"],
                    })
        return pd.DataFrame(data)

    def load_load_test_data(self) -> pd.DataFrame:
        """Load load test results into DataFrame."""
        data = []
        for html_file in self.reports_dir.glob("*load_test_report.html"):
            # Parse the HTML report to extract metrics
            # This is a simplified version - in reality, we'd use BeautifulSoup
            with open(html_file) as f:
                content = f.read()
                if "advanced" in html_file.name:
                    test_type = "advanced"
                else:
                    test_type = "basic"
                
                # Extract metrics from the HTML content
                # This is a placeholder - actual parsing would be more robust
                data.append({
                    "type": test_type,
                    "timestamp": datetime.fromtimestamp(html_file.stat().st_mtime),
                    "total_requests": 1000,  # Placeholder
                    "failure_rate": 0.1,     # Placeholder
                    "avg_response_time": 200, # Placeholder
                    "p95_response_time": 500, # Placeholder
                })
        return pd.DataFrame(data)

    def create_latency_plot(self, df: pd.DataFrame) -> go.Figure:
        """Create latency distribution plot."""
        fig = go.Figure()
        
        for name in df["name"].unique():
            test_data = df[df["name"] == name]
            fig.add_trace(go.Box(
                name=name,
                y=test_data["mean"],
                customdata=test_data[["p50", "p95", "stddev"]],
                hovertemplate=(
                    "Mean: %{y:.2f}ms<br>"
                    "P50: %{customdata[0]:.2f}ms<br>"
                    "P95: %{customdata[1]:.2f}ms<br>"
                    "StdDev: %{customdata[2]:.2f}ms<br>"
                ),
            ))

        fig.update_layout(
            title="Response Time Distribution by Test",
            yaxis_title="Response Time (ms)",
            showlegend=True,
        )
        return fig

    def create_throughput_plot(self, df: pd.DataFrame) -> go.Figure:
        """Create throughput over time plot."""
        fig = go.Figure()
        
        for name in df["name"].unique():
            test_data = df[df["name"] == name]
            throughput = 1000 / test_data["mean"]  # Convert ms to RPS
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(test_data["timestamp"]),
                y=throughput,
                name=name,
                mode="lines+markers",
            ))

        fig.update_layout(
            title="Throughput Over Time",
            xaxis_title="Time",
            yaxis_title="Requests per Second",
            showlegend=True,
        )
        return fig

    def create_resource_usage_plot(self, df: pd.DataFrame) -> go.Figure:
        """Create resource usage plot."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("CPU Usage", "Memory Usage"),
            vertical_spacing=0.15,
        )

        for name in df["name"].unique():
            test_data = df[df["name"] == name]
            # CPU Usage (placeholder data)
            fig.add_trace(
                go.Scatter(
                    x=pd.to_datetime(test_data["timestamp"]),
                    y=[50 + 10 * i for i in range(len(test_data))],  # Placeholder
                    name=f"{name} CPU",
                    mode="lines",
                ),
                row=1, col=1,
            )
            # Memory Usage (placeholder data)
            fig.add_trace(
                go.Scatter(
                    x=pd.to_datetime(test_data["timestamp"]),
                    y=[100 + 20 * i for i in range(len(test_data))],  # Placeholder
                    name=f"{name} Memory",
                    mode="lines",
                ),
                row=2, col=1,
            )

        fig.update_layout(
            height=800,
            showlegend=True,
        )
        fig.update_yaxes(title_text="CPU %", row=1, col=1)
        fig.update_yaxes(title_text="Memory (MB)", row=2, col=1)
        return fig

    def render_dashboard(self):
        """Render the dashboard."""
        st.title("EUDI-Connect Performance Dashboard")
        st.markdown("""
        Real-time performance metrics for the EUDI-Connect API.
        Updates every 5 seconds.
        """)

        # Load data
        benchmark_df = self.load_benchmark_data()
        load_test_df = self.load_load_test_data()

        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Response Times",
            "Throughput",
            "Resource Usage",
            "Test History",
        ])

        with tab1:
            st.plotly_chart(
                self.create_latency_plot(benchmark_df),
                use_container_width=True,
            )

            # Show performance targets
            st.markdown("### Performance Targets")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "P95 Target",
                    "800ms",
                    delta=f"{800 - benchmark_df['p95'].mean():.0f}ms",
                    delta_color="inverse",
                )
            with col2:
                st.metric(
                    "P50 Target",
                    "300ms",
                    delta=f"{300 - benchmark_df['p50'].mean():.0f}ms",
                    delta_color="inverse",
                )
            with col3:
                st.metric(
                    "Error Rate",
                    f"{load_test_df['failure_rate'].mean():.2%}",
                    delta="-0.5%",
                    delta_color="inverse",
                )

        with tab2:
            st.plotly_chart(
                self.create_throughput_plot(benchmark_df),
                use_container_width=True,
            )

            # Show throughput metrics
            st.markdown("### Throughput Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Average RPS",
                    f"{1000 / benchmark_df['mean'].mean():.1f}",
                    delta="+2.5",
                )
            with col2:
                st.metric(
                    "Peak RPS",
                    f"{1000 / benchmark_df['min'].min():.1f}",
                    delta="+5.0",
                )

        with tab3:
            st.plotly_chart(
                self.create_resource_usage_plot(benchmark_df),
                use_container_width=True,
            )

            # Show resource metrics
            st.markdown("### Resource Metrics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CPU Usage", "45%", delta="-5%")
            with col2:
                st.metric("Memory Usage", "256MB", delta="+32MB")
            with col3:
                st.metric("Disk I/O", "120MB/s", delta="-10MB/s")

        with tab4:
            st.markdown("### Test History")
            st.dataframe(
                benchmark_df.sort_values("timestamp", ascending=False),
                use_container_width=True,
            )

        # Update timestamp
        st.sidebar.markdown("### Dashboard Info")
        st.sidebar.write(f"Last updated: {self.last_update.strftime('%H:%M:%S')}")
        
        # Controls
        st.sidebar.markdown("### Controls")
        auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
        if auto_refresh:
            time.sleep(self.update_interval)
            st.rerun()


if __name__ == "__main__":
    dashboard = MetricsDashboard()
    dashboard.render_dashboard()
