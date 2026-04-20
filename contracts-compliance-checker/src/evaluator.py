import json
import os

from src.pipeline import run_pipeline


def evaluate(prompt_template: str, version: str = "v1"):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    samples_path = os.path.join(root, "data", "samples.json")
    expected_path = os.path.join(root, "data", "expected_outputs.json")

    with open(samples_path, encoding="utf-8") as f:
        samples = json.load(f)
    with open(expected_path, encoding="utf-8") as f:
        expected = json.load(f)

    total = 0
    hits = 0

    for sample in samples:
        result = run_pipeline(sample["text"], prompt_template, version=version)
        total += 1
        expected_terms = expected[str(sample["id"])]

        extracted = " ".join([r.description.lower() for r in result.risks])
        if all(term in extracted for term in expected_terms):
            hits += 1

    accuracy = hits / total if total else 0
    print(f"Evaluation accuracy: {accuracy:.2f}")
