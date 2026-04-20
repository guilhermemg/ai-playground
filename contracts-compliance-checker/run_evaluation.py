#!/usr/bin/env python3
"""
Evaluate risk extraction against expected keyword coverage per sample contract.

Compares each sample in data/samples.json to expected_terms in
data/expected_outputs.json (substring match on risk descriptions).
"""

import argparse
import json
import os

from src.evaluator import evaluate


def _load_prompt(version: str) -> str:
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "prompts",
        f"risk_extraction_{version}.txt",
    )
    with open(path, encoding="utf-8") as f:
        return f.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run extraction evaluation over sample contracts"
    )
    parser.add_argument(
        "--version",
        choices=("v1", "v2"),
        default="v1",
        help="Prompt template version to use (default: v1)",
    )
    args = parser.parse_args()

    prompt = _load_prompt(args.version)
    evaluate(prompt, version=args.version)


if __name__ == "__main__":
    main()
