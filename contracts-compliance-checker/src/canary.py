"""Canary deployment logic for A/B testing prompt versions.

This module provides:
- Traffic routing between prompt versions
- Performance comparison metrics
- Gradual rollout control
"""

import random
import json
import os
from datetime import datetime, timezone
from typing import Literal, Optional
from dataclasses import dataclass, asdict


# Canary configuration
CANARY_CONFIG = {
    "enabled": True,
    "v2_percentage": 20,  # Percentage of traffic routed to v2
    "prompts": {
        "v1": "prompts/risk_extraction_v1.txt",
        "v2": "prompts/risk_extraction_v2.txt",
    }
}


@dataclass
class CanaryResult:
    """Result of a canary experiment run."""
    version: str
    latency: float
    num_risks: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    timestamp: str
    contract_id: Optional[str] = None


class CanaryDeployment:
    """Manages canary deployment for prompt versions."""
    
    def __init__(self, config: dict = None, log_path: str = "canary_logs.json"):
        self.config = config or CANARY_CONFIG
        self.log_path = log_path
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompt templates from files."""
        self.prompts = {}
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for version, path in self.config["prompts"].items():
            if not path:  # Skip empty paths
                self.prompts[version] = None
                continue
            full_path = os.path.join(base_path, path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path) as f:
                    self.prompts[version] = f.read()
            else:
                self.prompts[version] = None
    
    def select_version(self) -> Literal["v1", "v2"]:
        """Select which prompt version to use based on canary percentage."""
        if not self.config["enabled"]:
            return "v1"
        
        roll = random.randint(1, 100)
        return "v2" if roll <= self.config["v2_percentage"] else "v1"
    
    def get_prompt(self, version: str = None) -> tuple[str, str]:
        """
        Get the prompt template for the specified or selected version.
        
        Returns:
            tuple: (version, prompt_template)
        """
        if version is None:
            version = self.select_version()
        
        prompt = self.prompts.get(version)
        if prompt is None:
            # Fallback to v1 if v2 not available
            version = "v1"
            prompt = self.prompts.get("v1", "")
        
        return version, prompt
    
    def log_result(self, result: CanaryResult):
        """Log a canary experiment result."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(asdict(result)) + "\n")
    
    def get_metrics(self) -> dict:
        """
        Calculate comparison metrics between versions.
        
        Returns:
            dict: Metrics for each version including avg latency, risk counts, etc.
        """
        if not os.path.exists(self.log_path):
            return {"v1": {}, "v2": {}, "comparison": {}}
        
        results = {"v1": [], "v2": []}
        
        with open(self.log_path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    version = data.get("version", "v1")
                    if version in results:
                        results[version].append(data)
        
        metrics = {}
        for version, data in results.items():
            if data:
                metrics[version] = {
                    "count": len(data),
                    "avg_latency": sum(d["latency"] for d in data) / len(data),
                    "avg_risks": sum(d["num_risks"] for d in data) / len(data),
                    "avg_high_severity": sum(d["high_severity_count"] for d in data) / len(data),
                    "avg_medium_severity": sum(d["medium_severity_count"] for d in data) / len(data),
                    "avg_low_severity": sum(d["low_severity_count"] for d in data) / len(data),
                }
            else:
                metrics[version] = {"count": 0}
        
        # Comparison if both have data
        if metrics.get("v1", {}).get("count", 0) > 0 and metrics.get("v2", {}).get("count", 0) > 0:
            metrics["comparison"] = {
                "latency_diff_pct": ((metrics["v2"]["avg_latency"] - metrics["v1"]["avg_latency"]) 
                                     / metrics["v1"]["avg_latency"] * 100),
                "risk_detection_diff": metrics["v2"]["avg_risks"] - metrics["v1"]["avg_risks"],
                "high_severity_diff": metrics["v2"]["avg_high_severity"] - metrics["v1"]["avg_high_severity"],
            }
        else:
            metrics["comparison"] = {}
        
        return metrics
    
    def set_rollout_percentage(self, percentage: int):
        """Update the canary rollout percentage."""
        if 0 <= percentage <= 100:
            self.config["v2_percentage"] = percentage
        else:
            raise ValueError("Percentage must be between 0 and 100")
    
    def enable(self):
        """Enable canary deployment."""
        self.config["enabled"] = True
    
    def disable(self):
        """Disable canary deployment (all traffic goes to v1)."""
        self.config["enabled"] = False


# Global canary instance
_canary = None

def get_canary() -> CanaryDeployment:
    """Get or create the global canary deployment instance."""
    global _canary
    if _canary is None:
        _canary = CanaryDeployment()
    return _canary
