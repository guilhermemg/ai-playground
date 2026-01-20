#!/usr/bin/env python3
"""
Canary deployment runner for testing prompt versions.

Usage:
    python run_canary.py              # Run with canary selection (default 20% v2)
    python run_canary.py --v1         # Force v1 for all
    python run_canary.py --v2         # Force v2 for all
    python run_canary.py --rollout 50 # Set 50% canary rollout
    python run_canary.py --metrics    # Show comparison metrics
"""

import argparse
import json
from src.pipeline import run_pipeline
from src.canary import get_canary


def run_analysis(version: str = None):
    """Run contract analysis with canary deployment."""
    samples = json.load(open("data/samples.json"))
    canary = get_canary()
    
    print(f"\n{'='*70}")
    print(f"CANARY DEPLOYMENT - v2 rollout: {canary.config['v2_percentage']}%")
    print(f"{'='*70}")
    
    version_counts = {"v1": 0, "v2": 0}
    
    for sample in samples:
        # Get the version that will be used
        if version:
            selected_version = version
        else:
            selected_version = canary.select_version()
        
        version_counts[selected_version] += 1
        _, prompt = canary.get_prompt(selected_version)
        
        print(f"\n{'─'*70}")
        print(f"Contract #{sample['id']}: {sample.get('title', 'Untitled')}")
        print(f"Using: {selected_version.upper()}")
        print('─'*70)
        
        output = run_pipeline(
            sample["text"], 
            prompt_template=prompt, 
            version=selected_version,
            contract_id=str(sample["id"])
        )
        
        print(f"\nFound {len(output.risks)} compliance risks:\n")
        for i, risk in enumerate(output.risks, 1):
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk.severity, "⚪")
            print(f"  {i}. {severity_icon} [{risk.severity.upper()}] {risk.description[:80]}...")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY: v1={version_counts['v1']}, v2={version_counts['v2']}")
    print(f"{'='*70}\n")


def show_metrics():
    """Display canary comparison metrics."""
    canary = get_canary()
    metrics = canary.get_metrics()
    
    print(f"\n{'='*70}")
    print("CANARY METRICS COMPARISON")
    print(f"{'='*70}\n")
    
    for version in ["v1", "v2"]:
        data = metrics.get(version, {})
        if data.get("count", 0) > 0:
            print(f"{version.upper()} Performance:")
            print(f"  Samples:         {data['count']}")
            print(f"  Avg Latency:     {data['avg_latency']:.2f}s")
            print(f"  Avg Risks Found: {data['avg_risks']:.1f}")
            print(f"  Avg High:        {data['avg_high_severity']:.1f}")
            print(f"  Avg Medium:      {data['avg_medium_severity']:.1f}")
            print(f"  Avg Low:         {data['avg_low_severity']:.1f}")
            print()
        else:
            print(f"{version.upper()}: No data yet\n")
    
    comparison = metrics.get("comparison", {})
    if comparison:
        print("Comparison (v2 vs v1):")
        print(f"  Latency Diff:    {comparison['latency_diff_pct']:+.1f}%")
        print(f"  Risk Detection:  {comparison['risk_detection_diff']:+.1f} risks")
        print(f"  High Severity:   {comparison['high_severity_diff']:+.1f}")
    else:
        print("Comparison: Need data from both versions")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="Canary deployment for prompt versions")
    parser.add_argument("--v1", action="store_true", help="Force v1 for all requests")
    parser.add_argument("--v2", action="store_true", help="Force v2 for all requests")
    parser.add_argument("--rollout", type=int, help="Set v2 rollout percentage (0-100)")
    parser.add_argument("--metrics", action="store_true", help="Show comparison metrics")
    
    args = parser.parse_args()
    
    canary = get_canary()
    
    if args.rollout is not None:
        canary.set_rollout_percentage(args.rollout)
        print(f"Set canary rollout to {args.rollout}%")
    
    if args.metrics:
        show_metrics()
        return
    
    version = None
    if args.v1:
        version = "v1"
        canary.disable()
    elif args.v2:
        version = "v2"
        canary.set_rollout_percentage(100)
    
    run_analysis(version)


if __name__ == "__main__":
    main()
