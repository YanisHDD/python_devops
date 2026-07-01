import os
import sys

# Add api directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../api")))

from metrics import get_system_metrics


def test_get_system_metrics():
    """Tests the structure and boundaries of system metrics returned."""
    metrics = get_system_metrics()
    assert isinstance(metrics, dict)
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics

    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["memory_percent"] <= 100
    assert 0 <= metrics["disk_percent"] <= 100
