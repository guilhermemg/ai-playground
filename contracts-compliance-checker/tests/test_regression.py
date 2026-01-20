"""Regression tests for the contracts compliance checker.

These tests ensure consistent behavior across code changes by:
1. Testing against known contract samples with expected outputs
2. Validating that rule detection remains stable
3. Checking that the evaluation accuracy meets minimum thresholds
"""

import pytest
import json
from unittest.mock import patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.risk_schema import RiskExtractionOutput, Risk


class TestSampleContracts:
    """Regression tests using sample contracts."""

    @pytest.fixture
    def samples(self):
        """Load sample contracts from data file."""
        samples_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'samples.json')
        with open(samples_path) as f:
            return json.load(f)

    @pytest.fixture
    def expected_outputs(self):
        """Load expected outputs from data file."""
        expected_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'expected_outputs.json')
        with open(expected_path) as f:
            return json.load(f)

    @pytest.fixture
    def rules(self):
        """Load compliance rules from data file."""
        rules_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'rules.json')
        with open(rules_path) as f:
            return json.load(f)

    def test_samples_file_has_required_fields(self, samples):
        """Verify sample contracts have required fields."""
        assert len(samples) >= 1, "Should have at least one sample"
        
        for sample in samples:
            assert "id" in sample, "Each sample must have an id"
            assert "text" in sample, "Each sample must have text"
            assert isinstance(sample["id"], int), "Sample id must be an integer"
            assert len(sample["text"]) > 0, "Sample text must not be empty"

    def test_expected_outputs_match_samples(self, samples, expected_outputs):
        """Verify each sample has corresponding expected output."""
        sample_ids = {str(s["id"]) for s in samples}
        expected_ids = set(expected_outputs.keys())
        
        assert sample_ids == expected_ids, f"Sample IDs {sample_ids} don't match expected IDs {expected_ids}"

    def test_expected_outputs_have_terms(self, expected_outputs):
        """Verify expected outputs contain search terms."""
        for sample_id, terms in expected_outputs.items():
            assert isinstance(terms, list), f"Expected terms for sample {sample_id} must be a list"
            assert len(terms) > 0, f"Sample {sample_id} should have at least one expected term"
            
            for term in terms:
                assert isinstance(term, str), f"Terms must be strings"
                assert len(term) > 0, f"Terms must not be empty"

    def test_rules_file_structure(self, rules):
        """Verify rules file has correct structure."""
        assert "rules" in rules, "Rules file must have 'rules' key"
        assert len(rules["rules"]) >= 10, "Should have at least 10 rules"
        
        for rule in rules["rules"]:
            assert "id" in rule, "Each rule must have an id"
            assert "category" in rule, "Each rule must have a category"
            assert "name" in rule, "Each rule must have a name"
            assert "description" in rule, "Each rule must have a description"
            assert "severity" in rule, "Each rule must have a severity"
            assert rule["severity"] in ["low", "medium", "high"], f"Invalid severity: {rule['severity']}"

    def test_rules_cover_all_categories(self, rules):
        """Verify rules cover all expected categories."""
        expected_categories = {"Data Protection", "Contract Fairness", "Employment Law", "Service Levels", "Financial Terms"}
        actual_categories = {r["category"] for r in rules["rules"]}
        
        assert expected_categories == actual_categories, f"Missing categories: {expected_categories - actual_categories}"


class TestMockedRegressionScenarios:
    """Regression tests with mocked LLM responses to ensure stable behavior."""

    @pytest.fixture
    def prompt_template(self):
        """Load the prompt template."""
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'risk_extraction_v1.txt')
        with open(prompt_path) as f:
            return f.read()

    def test_software_license_risks(self, prompt_template):
        """Regression test: Software License Agreement should detect liability issues."""
        mock_response = {
            "risks": [
                {"description": "CONTRACT-003: Complete liability waiver - 'shall not be liable for any damages whatsoever' provides no reasonable limits", "severity": "medium"},
            ]
        }
        contract = "TechCorp shall not be liable for any damages whatsoever."
        
        with patch('src.pipeline.call_llm', return_value=mock_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(contract, prompt_template)
            
            assert len(result.risks) >= 1
            descriptions = " ".join([r.description.lower() for r in result.risks])
            assert "liability" in descriptions or "contract-003" in descriptions

    def test_data_processing_agreement_risks(self, prompt_template):
        """Regression test: DPA should detect GDPR compliance issues."""
        mock_response = {
            "risks": [
                {"description": "GDPR-001: Sub-processors may be engaged without prior consent from Controller", "severity": "high"},
                {"description": "GDPR-002: Personal data may be transferred to any country without adequacy assessment", "severity": "high"},
                {"description": "GDPR-003: Data retention period undefined - 'for business purposes' is too vague", "severity": "medium"},
            ]
        }
        contract = """
        Processor may engage sub-processors without prior consent.
        Data may be transferred to any country.
        Data will be retained for business purposes.
        """
        
        with patch('src.pipeline.call_llm', return_value=mock_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(contract, prompt_template)
            
            assert len(result.risks) >= 2
            high_risks = [r for r in result.risks if r.severity == "high"]
            assert len(high_risks) >= 1

    def test_employment_contract_risks(self, prompt_template):
        """Regression test: Employment contract should detect unfair terms."""
        mock_response = {
            "risks": [
                {"description": "EMPLOYMENT-001: Termination without notice violates reasonable notice requirements", "severity": "medium"},
                {"description": "EMPLOYMENT-002: Non-compete of 5 years worldwide is excessive and likely unenforceable", "severity": "high"},
                {"description": "EMPLOYMENT-003: Mandatory binding arbitration limits employee legal rights", "severity": "medium"},
            ]
        }
        contract = """
        Employer may terminate at any time without notice.
        Employee shall not work for competitors for 5 years, anywhere in the world.
        All disputes resolved through binding arbitration.
        """
        
        with patch('src.pipeline.call_llm', return_value=mock_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(contract, prompt_template)
            
            assert len(result.risks) >= 2
            descriptions = " ".join([r.description.lower() for r in result.risks])
            assert "non-compete" in descriptions or "employment-002" in descriptions

    def test_vendor_agreement_risks(self, prompt_template):
        """Regression test: Vendor agreement should detect unfair contract terms."""
        mock_response = {
            "risks": [
                {"description": "CONTRACT-001: Prices subject to change without notice period", "severity": "medium"},
                {"description": "CONTRACT-002: One-sided indemnification covering vendor's own negligence", "severity": "high"},
                {"description": "CONTRACT-004: Vendor may assign agreement without buyer consent", "severity": "low"},
            ]
        }
        contract = """
        Prices subject to change at any time without notice.
        Buyer shall indemnify Vendor including for Vendor's negligence.
        Vendor may assign this agreement without consent.
        """
        
        with patch('src.pipeline.call_llm', return_value=mock_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(contract, prompt_template)
            
            assert len(result.risks) >= 2
            descriptions = " ".join([r.description.lower() for r in result.risks])
            assert "indemnif" in descriptions or "contract-002" in descriptions

    def test_compliant_contract_minimal_risks(self, prompt_template):
        """Regression test: Well-drafted contract should have minimal or no risks."""
        mock_response = {"risks": []}
        contract = """
        COMPLIANT SERVICE AGREEMENT
        
        Prices: Fixed for 12 months. Changes require 60-day notice.
        Data: Stored in EU data centers only. Retained for 3 years, then deleted.
        Termination: Either party may terminate with 30-day written notice.
        Liability: Limited to fees paid in the preceding 12 months.
        Indemnification: Each party indemnifies for its own negligence.
        """
        
        with patch('src.pipeline.call_llm', return_value=mock_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(contract, prompt_template)
            
            # A compliant contract should have very few or no risks
            assert len(result.risks) <= 2


class TestEvaluationRegression:
    """Regression tests for the evaluation framework."""

    @pytest.fixture
    def samples(self):
        """Load sample contracts."""
        samples_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'samples.json')
        with open(samples_path) as f:
            return json.load(f)

    @pytest.fixture
    def expected_outputs(self):
        """Load expected outputs."""
        expected_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'expected_outputs.json')
        with open(expected_path) as f:
            return json.load(f)

    def test_evaluation_accuracy_with_perfect_extraction(self, samples, expected_outputs):
        """Test that evaluation reports 100% accuracy with perfect LLM responses."""
        
        def mock_perfect_llm(prompt):
            """Generate perfect responses based on expected terms."""
            # Find which sample this is for (crude but works for testing)
            for sample in samples:
                if sample["text"][:50] in prompt:
                    terms = expected_outputs.get(str(sample["id"]), [])
                    risks = [{"description": f"Risk related to {term}", "severity": "high"} for term in terms]
                    return {"risks": risks}
            return {"risks": []}

        with patch('src.pipeline.call_llm', side_effect=mock_perfect_llm):
            # Run evaluation logic manually
            from src.pipeline import run_pipeline
            prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'risk_extraction_v1.txt')
            with open(prompt_path) as f:
                prompt_template = f.read()

            hits = 0
            total = 0
            
            for sample in samples:
                result = run_pipeline(sample["text"], prompt_template)
                total += 1
                expected_terms = expected_outputs[str(sample["id"])]
                
                extracted = " ".join([r.description.lower() for r in result.risks])
                if all(term.lower() in extracted for term in expected_terms):
                    hits += 1
            
            accuracy = hits / total if total else 0
            assert accuracy == 1.0, f"Perfect extraction should yield 100% accuracy, got {accuracy:.2%}"

    def test_evaluation_handles_partial_matches(self, samples, expected_outputs):
        """Test that evaluation correctly handles partial matches."""
        
        def mock_partial_llm(prompt):
            """Return only some expected terms."""
            for sample in samples:
                if sample["text"][:50] in prompt:
                    terms = expected_outputs.get(str(sample["id"]), [])
                    # Only return half the expected terms
                    partial_terms = terms[:len(terms)//2] if terms else []
                    risks = [{"description": f"Risk: {term}", "severity": "medium"} for term in partial_terms]
                    return {"risks": risks}
            return {"risks": []}

        with patch('src.pipeline.call_llm', side_effect=mock_partial_llm):
            from src.pipeline import run_pipeline
            prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'risk_extraction_v1.txt')
            with open(prompt_path) as f:
                prompt_template = f.read()

            hits = 0
            total = 0
            
            for sample in samples:
                result = run_pipeline(sample["text"], prompt_template)
                total += 1
                expected_terms = expected_outputs[str(sample["id"])]
                
                extracted = " ".join([r.description.lower() for r in result.risks])
                if all(term.lower() in extracted for term in expected_terms):
                    hits += 1
            
            accuracy = hits / total if total else 0
            # With partial matches, accuracy should be less than 100%
            assert accuracy < 1.0, "Partial extraction should not yield 100% accuracy"
