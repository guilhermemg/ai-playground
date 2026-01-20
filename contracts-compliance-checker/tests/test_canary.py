"""Tests for the canary deployment module."""

import pytest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.canary import CanaryDeployment, CanaryResult, CANARY_CONFIG


class TestCanaryDeployment:
    """Tests for CanaryDeployment class."""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def canary(self, temp_log_file):
        """Create a canary deployment instance with temp log file."""
        config = {
            "enabled": True,
            "v2_percentage": 50,
            "prompts": {
                "v1": "prompts/risk_extraction_v1.txt",
                "v2": "prompts/risk_extraction_v2.txt",
            }
        }
        return CanaryDeployment(config=config, log_path=temp_log_file)

    def test_select_version_respects_percentage(self, canary):
        """Test that version selection respects the percentage."""
        # With 50% rollout, should get mix of both versions
        versions = [canary.select_version() for _ in range(100)]
        v1_count = versions.count("v1")
        v2_count = versions.count("v2")
        
        # Should be roughly 50/50 (allow for variance)
        assert 30 <= v1_count <= 70, f"v1 count {v1_count} outside expected range"
        assert 30 <= v2_count <= 70, f"v2 count {v2_count} outside expected range"

    def test_select_version_disabled_returns_v1(self, canary):
        """Test that disabled canary always returns v1."""
        canary.disable()
        versions = [canary.select_version() for _ in range(20)]
        assert all(v == "v1" for v in versions)

    def test_select_version_100_percent_returns_v2(self, canary):
        """Test that 100% rollout always returns v2."""
        canary.set_rollout_percentage(100)
        versions = [canary.select_version() for _ in range(20)]
        assert all(v == "v2" for v in versions)

    def test_select_version_0_percent_returns_v1(self, canary):
        """Test that 0% rollout always returns v1."""
        canary.set_rollout_percentage(0)
        versions = [canary.select_version() for _ in range(20)]
        assert all(v == "v1" for v in versions)

    def test_get_prompt_returns_tuple(self, canary):
        """Test that get_prompt returns version and template."""
        version, prompt = canary.get_prompt("v1")
        assert version == "v1"
        assert prompt is not None or prompt == ""  # May not exist in test env

    def test_get_prompt_with_version_override(self, canary):
        """Test that specifying version overrides canary selection."""
        version, _ = canary.get_prompt("v2")
        assert version == "v2"

    def test_set_rollout_percentage_valid(self, canary):
        """Test setting valid rollout percentages."""
        canary.set_rollout_percentage(0)
        assert canary.config["v2_percentage"] == 0
        
        canary.set_rollout_percentage(100)
        assert canary.config["v2_percentage"] == 100
        
        canary.set_rollout_percentage(50)
        assert canary.config["v2_percentage"] == 50

    def test_set_rollout_percentage_invalid(self, canary):
        """Test that invalid percentages raise error."""
        with pytest.raises(ValueError):
            canary.set_rollout_percentage(-1)
        
        with pytest.raises(ValueError):
            canary.set_rollout_percentage(101)

    def test_enable_disable(self, canary):
        """Test enable and disable methods."""
        canary.disable()
        assert canary.config["enabled"] == False
        
        canary.enable()
        assert canary.config["enabled"] == True


class TestCanaryLogging:
    """Tests for canary result logging."""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def canary(self, temp_log_file):
        """Create a canary deployment instance with temp log file."""
        config = {
            "enabled": True,
            "v2_percentage": 50,
            "prompts": {"v1": "", "v2": ""}
        }
        return CanaryDeployment(config=config, log_path=temp_log_file)

    def test_log_result_creates_file(self, canary, temp_log_file):
        """Test that logging creates the log file."""
        result = CanaryResult(
            version="v1",
            latency=1.5,
            num_risks=3,
            high_severity_count=1,
            medium_severity_count=1,
            low_severity_count=1,
            timestamp="2026-01-19T12:00:00Z"
        )
        canary.log_result(result)
        
        assert os.path.exists(temp_log_file)
        with open(temp_log_file) as f:
            content = f.read()
        assert "v1" in content
        assert "1.5" in content

    def test_log_result_appends(self, canary, temp_log_file):
        """Test that logging appends to existing file."""
        result1 = CanaryResult(
            version="v1", latency=1.0, num_risks=2,
            high_severity_count=1, medium_severity_count=1, low_severity_count=0,
            timestamp="2026-01-19T12:00:00Z"
        )
        result2 = CanaryResult(
            version="v2", latency=1.5, num_risks=4,
            high_severity_count=2, medium_severity_count=1, low_severity_count=1,
            timestamp="2026-01-19T12:01:00Z"
        )
        
        canary.log_result(result1)
        canary.log_result(result2)
        
        with open(temp_log_file) as f:
            lines = f.readlines()
        
        assert len(lines) == 2


class TestCanaryMetrics:
    """Tests for canary metrics calculation."""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file with test data."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Write test data
        test_data = [
            {"version": "v1", "latency": 1.0, "num_risks": 2, "high_severity_count": 1, "medium_severity_count": 1, "low_severity_count": 0},
            {"version": "v1", "latency": 1.2, "num_risks": 3, "high_severity_count": 1, "medium_severity_count": 1, "low_severity_count": 1},
            {"version": "v2", "latency": 1.5, "num_risks": 4, "high_severity_count": 2, "medium_severity_count": 1, "low_severity_count": 1},
            {"version": "v2", "latency": 1.3, "num_risks": 5, "high_severity_count": 2, "medium_severity_count": 2, "low_severity_count": 1},
        ]
        with open(path, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")
        
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def canary(self, temp_log_file):
        """Create a canary deployment instance with temp log file."""
        config = {
            "enabled": True,
            "v2_percentage": 50,
            "prompts": {"v1": "", "v2": ""}
        }
        return CanaryDeployment(config=config, log_path=temp_log_file)

    def test_get_metrics_returns_dict(self, canary):
        """Test that get_metrics returns a dictionary."""
        metrics = canary.get_metrics()
        assert isinstance(metrics, dict)
        assert "v1" in metrics
        assert "v2" in metrics
        assert "comparison" in metrics

    def test_get_metrics_calculates_averages(self, canary):
        """Test that metrics are correctly calculated."""
        metrics = canary.get_metrics()
        
        # v1: latencies 1.0, 1.2 -> avg 1.1
        assert metrics["v1"]["count"] == 2
        assert abs(metrics["v1"]["avg_latency"] - 1.1) < 0.01
        assert abs(metrics["v1"]["avg_risks"] - 2.5) < 0.01
        
        # v2: latencies 1.5, 1.3 -> avg 1.4
        assert metrics["v2"]["count"] == 2
        assert abs(metrics["v2"]["avg_latency"] - 1.4) < 0.01
        assert abs(metrics["v2"]["avg_risks"] - 4.5) < 0.01

    def test_get_metrics_comparison(self, canary):
        """Test that comparison metrics are calculated."""
        metrics = canary.get_metrics()
        comparison = metrics["comparison"]
        
        # Latency diff: (1.4 - 1.1) / 1.1 * 100 ≈ 27.3%
        assert "latency_diff_pct" in comparison
        assert comparison["latency_diff_pct"] > 0  # v2 is slower
        
        # Risk detection diff: 4.5 - 2.5 = 2.0
        assert abs(comparison["risk_detection_diff"] - 2.0) < 0.01

    def test_get_metrics_empty_file(self):
        """Test metrics with empty log file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        try:
            canary = CanaryDeployment(
                config={"enabled": True, "v2_percentage": 50, "prompts": {}},
                log_path=path
            )
            metrics = canary.get_metrics()
            
            assert metrics["v1"]["count"] == 0
            assert metrics["v2"]["count"] == 0
            assert metrics["comparison"] == {}
        finally:
            os.unlink(path)
