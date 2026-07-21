"""
Custom pytest plugins for ChatBot Tester Framework.
"""

import pytest
import time
import json
from typing import Dict, Any, Optional


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--chatbot-name",
        action="store",
        default="ChatBot",
        help="Name of the chatbot being tested"
    )
    parser.addoption(
        "--baseline-file",
        action="store",
        default=None,
        help="Path to baseline performance file for regression testing"
    )
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow running tests"
    )
    parser.addoption(
        "--auth-type",
        action="store",
        default=None,
        help="Override authentication type from config"
    )


class OutputCapturePlugin:
    """Plugin to capture and attach output on test failure."""

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if report.when == "call" and report.failed:
            if hasattr(item, '_captured_output'):
                report.extra_outputs = item._captured_output


class PerformanceTrackingPlugin:
    """Plugin for tracking performance metrics across test runs."""

    def __init__(self, baseline_file: Optional[str] = None):
        self.baseline_file = baseline_file
        self.current_run_metrics = {}
        self.baseline_metrics = {}
        if baseline_file:
            self._load_baseline()

    def _load_baseline(self):
        try:
            with open(self.baseline_file, 'r') as f:
                self.baseline_metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.baseline_metrics = {}

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report):
        if hasattr(report, 'duration') and "performance" in report.keywords:
            test_name = report.nodeid
            self.current_run_metrics[test_name] = {"duration": report.duration}

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        if self.current_run_metrics:
            terminalreporter.section("Performance Metrics")
            for test_name, metrics in self.current_run_metrics.items():
                terminalreporter.write_line(f"{test_name}: {metrics['duration']:.2f}s")


@pytest.fixture
def latency_tracker():
    """Track latency across tests."""
    class LatencyTracker:
        def __init__(self):
            self.latencies = []

        def record(self, latency_ms: float):
            self.latencies.append(latency_ms)

        def percentile(self, p: float) -> float:
            if not self.latencies:
                return 0.0
            sorted_l = sorted(self.latencies)
            idx = int(len(sorted_l) * p / 100)
            return sorted_l[min(idx, len(sorted_l) - 1)]

    return LatencyTracker()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "regression: marks regression tests")

    baseline_file = config.getoption("--baseline-file")
    if baseline_file:
        config.pluginmanager.register(PerformanceTrackingPlugin(baseline_file), "perf_tracker")