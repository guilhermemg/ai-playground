import json
from src.pipeline import run_pipeline

def evaluate(prompt_template: str):
    samples = json.load(open("data/samples.json"))
    expected = json.load(open("data/expected_outputs.json"))

    total = 0
    hits = 0

    for sample in samples:
        result = run_pipeline(sample["text"], prompt_template)
        total += 1
        expected_terms = expected[str(sample["id"])]

        extracted = " ".join([r.description.lower() for r in result.risks])
        if all(term in extracted for term in expected_terms):
            hits += 1

    accuracy = hits / total if total else 0
    print(f"Evaluation accuracy: {accuracy:.2f}")
