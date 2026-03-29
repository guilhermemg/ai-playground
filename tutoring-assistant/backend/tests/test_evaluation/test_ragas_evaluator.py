import pytest
import json
from pathlib import Path

from app.evaluation.ragas_evaluator import load_golden_dataset, GOLDEN_DATASETS_DIR


def test_golden_datasets_exist():
    datasets = list(GOLDEN_DATASETS_DIR.glob("*.json"))
    assert len(datasets) >= 3, "Should have at least medicine, physics, and math golden datasets"


def test_load_all_golden_datasets():
    data = load_golden_dataset()
    assert len(data) > 0
    for item in data:
        assert "question" in item
        assert "ground_truth" in item
        assert "domain" in item


def test_load_domain_specific_dataset():
    medicine = load_golden_dataset("medicine")
    assert len(medicine) > 0
    for item in medicine:
        assert item["domain"] == "medicine"


def test_load_nonexistent_domain():
    data = load_golden_dataset("nonexistent_domain_xyz")
    assert data == []


def test_golden_dataset_structure():
    for f in GOLDEN_DATASETS_DIR.glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
        assert "domain" in data
        assert "questions" in data
        assert isinstance(data["questions"], list)
        for q in data["questions"]:
            assert "question" in q
            assert "ground_truth" in q
