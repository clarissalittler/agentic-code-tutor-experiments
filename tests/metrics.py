"""Metrics tracking for LLM regression testing.

This module provides utilities for tracking test metrics over time
and detecting regressions.
"""

import json
import subprocess
from datetime import datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class TestRunMetrics:
    """Metrics from a single test run."""
    timestamp: str
    git_sha: str
    model: str

    # Parsing metrics
    parse_success_rate: float = 0.0
    avg_questions: float = 0.0
    avg_observations: float = 0.0

    # Quality metrics (from LLM-judge, if available)
    avg_relevance: Optional[float] = None
    avg_helpfulness: Optional[float] = None
    avg_tone: Optional[float] = None
    avg_overall: Optional[float] = None

    # Performance metrics
    avg_latency_ms: float = 0.0
    avg_input_tokens: int = 0
    avg_output_tokens: int = 0

    # Contract metrics
    contract_pass_rate: float = 0.0

    # Test counts
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestRunMetrics":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class RegressionAlert:
    """Alert for a detected regression."""
    metric_name: str
    current_value: float
    baseline_value: float
    threshold_pct: float
    direction: str  # "higher_better" or "lower_better"
    severity: str  # "warning" or "critical"

    @property
    def message(self) -> str:
        """Generate alert message."""
        change_pct = abs(self.current_value - self.baseline_value) / self.baseline_value * 100
        direction_word = "decreased" if self.direction == "higher_better" else "increased"
        return (
            f"{self.severity.upper()}: {self.metric_name} {direction_word} by {change_pct:.1f}% "
            f"(current: {self.current_value:.2f}, baseline: {self.baseline_value:.2f})"
        )


class MetricsTracker:
    """Track and store test metrics over time."""

    # Metrics configuration: (direction, warning_threshold, critical_threshold)
    METRIC_CONFIG = {
        "parse_success_rate": ("higher_better", 5, 10),
        "avg_overall": ("higher_better", 10, 20),
        "contract_pass_rate": ("higher_better", 5, 15),
        "avg_latency_ms": ("lower_better", 20, 50),
    }

    def __init__(self, metrics_dir: Path):
        """
        Initialize the metrics tracker.

        Args:
            metrics_dir: Directory to store metrics files
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "test_metrics_history.json"
        self.current_observations: List[Dict[str, Any]] = []

    def record_observation(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a single metric observation.

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for categorization
        """
        self.current_observations.append({
            "metric": metric_name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat()
        })

    def save_run(self, run_metrics: TestRunMetrics):
        """
        Save a completed test run's metrics.

        Args:
            run_metrics: Metrics from the test run
        """
        history = self._load_history()
        history.append(run_metrics.to_dict())

        # Keep only last 100 runs
        if len(history) > 100:
            history = history[-100:]

        with open(self.metrics_file, 'w') as f:
            json.dump(history, f, indent=2)

        # Also save current observations
        observations_file = self.metrics_dir / f"observations_{run_metrics.timestamp.replace(':', '-')}.json"
        with open(observations_file, 'w') as f:
            json.dump(self.current_observations, f, indent=2)

        self.current_observations = []

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load historical metrics."""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                return json.load(f)
        return []

    def get_baseline(self, num_runs: int = 5) -> Optional[Dict[str, float]]:
        """
        Calculate baseline from recent runs.

        Args:
            num_runs: Number of recent runs to average

        Returns:
            Dictionary of metric baselines, or None if insufficient history
        """
        history = self._load_history()
        if len(history) < num_runs:
            return None

        recent = history[-num_runs:]
        baseline = {}

        for metric_name in self.METRIC_CONFIG.keys():
            values = [r.get(metric_name) for r in recent if r.get(metric_name) is not None]
            if values:
                baseline[metric_name] = sum(values) / len(values)

        return baseline

    def check_for_regressions(
        self,
        current: TestRunMetrics
    ) -> List[RegressionAlert]:
        """
        Check for regressions against historical baseline.

        Args:
            current: Current test run metrics

        Returns:
            List of regression alerts (empty if no regressions)
        """
        baseline = self.get_baseline()
        if not baseline:
            return []  # Not enough history

        alerts = []

        for metric_name, (direction, warn_thresh, crit_thresh) in self.METRIC_CONFIG.items():
            baseline_val = baseline.get(metric_name)
            current_val = getattr(current, metric_name, None)

            if baseline_val is None or current_val is None:
                continue

            # Calculate change percentage
            if baseline_val == 0:
                continue

            if direction == "higher_better":
                change_pct = (baseline_val - current_val) / baseline_val * 100
            else:  # lower_better
                change_pct = (current_val - baseline_val) / baseline_val * 100

            if change_pct > crit_thresh:
                alerts.append(RegressionAlert(
                    metric_name=metric_name,
                    current_value=current_val,
                    baseline_value=baseline_val,
                    threshold_pct=crit_thresh,
                    direction=direction,
                    severity="critical"
                ))
            elif change_pct > warn_thresh:
                alerts.append(RegressionAlert(
                    metric_name=metric_name,
                    current_value=current_val,
                    baseline_value=baseline_val,
                    threshold_pct=warn_thresh,
                    direction=direction,
                    severity="warning"
                ))

        return alerts

    def generate_report(self, current: TestRunMetrics) -> str:
        """
        Generate a human-readable metrics report.

        Args:
            current: Current test run metrics

        Returns:
            Formatted report string
        """
        baseline = self.get_baseline()
        lines = [
            "=" * 60,
            "Test Metrics Report",
            f"Timestamp: {current.timestamp}",
            f"Git SHA: {current.git_sha}",
            f"Model: {current.model}",
            "=" * 60,
            "",
            "Test Results:",
            f"  Tests Run: {current.tests_run}",
            f"  Passed: {current.tests_passed}",
            f"  Failed: {current.tests_failed}",
            "",
            "Parsing Metrics:",
            f"  Parse Success Rate: {current.parse_success_rate:.1%}",
            f"  Avg Questions: {current.avg_questions:.1f}",
            f"  Avg Observations: {current.avg_observations:.1f}",
            "",
            "Contract Metrics:",
            f"  Contract Pass Rate: {current.contract_pass_rate:.1%}",
            "",
        ]

        if current.avg_overall is not None:
            lines.extend([
                "Quality Metrics (LLM-Judge):",
                f"  Avg Relevance: {current.avg_relevance:.2f}/5" if current.avg_relevance else "",
                f"  Avg Helpfulness: {current.avg_helpfulness:.2f}/5" if current.avg_helpfulness else "",
                f"  Avg Tone: {current.avg_tone:.2f}/5" if current.avg_tone else "",
                f"  Avg Overall: {current.avg_overall:.2f}/5",
                "",
            ])

        if current.avg_latency_ms > 0:
            lines.extend([
                "Performance Metrics:",
                f"  Avg Latency: {current.avg_latency_ms:.0f}ms",
                f"  Avg Input Tokens: {current.avg_input_tokens}",
                f"  Avg Output Tokens: {current.avg_output_tokens}",
                "",
            ])

        # Compare to baseline
        if baseline:
            lines.extend([
                "Comparison to Baseline:",
            ])
            for metric_name in ["parse_success_rate", "contract_pass_rate", "avg_overall"]:
                base_val = baseline.get(metric_name)
                curr_val = getattr(current, metric_name, None)
                if base_val and curr_val:
                    change = ((curr_val - base_val) / base_val) * 100
                    direction = "↑" if change > 0 else "↓" if change < 0 else "→"
                    lines.append(f"  {metric_name}: {direction} {abs(change):.1f}%")

        # Check for regressions
        alerts = self.check_for_regressions(current)
        if alerts:
            lines.extend([
                "",
                "⚠️  REGRESSION ALERTS:",
            ])
            for alert in alerts:
                lines.append(f"  {alert.message}")

        lines.append("=" * 60)
        return "\n".join(lines)


def get_git_sha() -> str:
    """Get the current git SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()[:8]
    except Exception:
        return "unknown"


def create_test_run_metrics(
    model: str = "claude-haiku-4-5",
    **kwargs
) -> TestRunMetrics:
    """
    Create a TestRunMetrics instance with defaults.

    Args:
        model: Model used for testing
        **kwargs: Additional metric values

    Returns:
        TestRunMetrics instance
    """
    return TestRunMetrics(
        timestamp=datetime.now().isoformat(),
        git_sha=get_git_sha(),
        model=model,
        **kwargs
    )


# Example usage
if __name__ == "__main__":
    # Demo the metrics system
    tracker = MetricsTracker(Path("./test_metrics"))

    # Simulate a test run
    metrics = create_test_run_metrics(
        model="claude-haiku-4-5",
        parse_success_rate=0.95,
        avg_questions=2.5,
        avg_observations=3.0,
        contract_pass_rate=0.90,
        tests_run=50,
        tests_passed=48,
        tests_failed=2,
    )

    # Check for regressions
    alerts = tracker.check_for_regressions(metrics)
    for alert in alerts:
        print(alert.message)

    # Generate and print report
    report = tracker.generate_report(metrics)
    print(report)

    # Save the run
    tracker.save_run(metrics)
