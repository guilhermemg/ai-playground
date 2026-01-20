"""Unit tests for Pydantic schema models."""

import pytest
from pydantic import ValidationError
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.risk_schema import Risk, RiskExtractionOutput


class TestRiskModel:
    """Tests for the Risk Pydantic model."""

    def test_valid_risk_high_severity(self):
        """Test creating a risk with high severity."""
        risk = Risk(description="Missing consent clause", severity="high")
        assert risk.description == "Missing consent clause"
        assert risk.severity == "high"

    def test_valid_risk_medium_severity(self):
        """Test creating a risk with medium severity."""
        risk = Risk(description="Unclear data retention", severity="medium")
        assert risk.description == "Unclear data retention"
        assert risk.severity == "medium"

    def test_valid_risk_low_severity(self):
        """Test creating a risk with low severity."""
        risk = Risk(description="Minor formatting issue", severity="low")
        assert risk.description == "Minor formatting issue"
        assert risk.severity == "low"

    def test_invalid_severity_rejected(self):
        """Test that invalid severity values are rejected."""
        with pytest.raises(ValidationError):
            Risk(description="Test risk", severity="critical")

    def test_invalid_severity_case_sensitive(self):
        """Test that severity is case-sensitive."""
        with pytest.raises(ValidationError):
            Risk(description="Test risk", severity="HIGH")

    def test_empty_description_allowed(self):
        """Test that empty description is technically allowed by Pydantic."""
        risk = Risk(description="", severity="low")
        assert risk.description == ""

    def test_missing_description_rejected(self):
        """Test that missing description raises ValidationError."""
        with pytest.raises(ValidationError):
            Risk(severity="high")

    def test_missing_severity_rejected(self):
        """Test that missing severity raises ValidationError."""
        with pytest.raises(ValidationError):
            Risk(description="Test risk")


class TestRiskExtractionOutput:
    """Tests for the RiskExtractionOutput Pydantic model."""

    def test_valid_output_with_risks(self):
        """Test creating output with multiple risks."""
        output = RiskExtractionOutput(risks=[
            Risk(description="Risk 1", severity="high"),
            Risk(description="Risk 2", severity="medium"),
            Risk(description="Risk 3", severity="low"),
        ])
        assert len(output.risks) == 3
        assert output.risks[0].severity == "high"
        assert output.risks[1].severity == "medium"
        assert output.risks[2].severity == "low"

    def test_valid_output_empty_risks(self):
        """Test creating output with empty risks list."""
        output = RiskExtractionOutput(risks=[])
        assert len(output.risks) == 0

    def test_output_from_dict(self):
        """Test creating output from dictionary (simulating LLM response)."""
        data = {
            "risks": [
                {"description": "GDPR-001: Missing consent", "severity": "high"},
                {"description": "CONTRACT-002: One-sided indemnification", "severity": "medium"},
            ]
        }
        output = RiskExtractionOutput(**data)
        assert len(output.risks) == 2
        assert "GDPR-001" in output.risks[0].description

    def test_output_to_dict(self):
        """Test converting output to dictionary."""
        output = RiskExtractionOutput(risks=[
            Risk(description="Test risk", severity="high"),
        ])
        data = output.model_dump()
        assert "risks" in data
        assert len(data["risks"]) == 1
        assert data["risks"][0]["description"] == "Test risk"
        assert data["risks"][0]["severity"] == "high"

    def test_missing_risks_field_rejected(self):
        """Test that missing risks field raises ValidationError."""
        with pytest.raises(ValidationError):
            RiskExtractionOutput()

    def test_invalid_risk_in_list_rejected(self):
        """Test that invalid risk objects in list are rejected."""
        with pytest.raises(ValidationError):
            RiskExtractionOutput(risks=[
                {"description": "Valid risk", "severity": "high"},
                {"description": "Invalid risk", "severity": "extreme"},
            ])


class TestSchemaIntegration:
    """Integration tests for schema validation."""

    def test_realistic_llm_response(self):
        """Test parsing a realistic LLM response structure."""
        llm_response = {
            "risks": [
                {
                    "description": "GDPR-001: The contract allows sub-processor engagement without requiring explicit consent from the data controller.",
                    "severity": "high"
                },
                {
                    "description": "GDPR-003: Data retention period is vaguely defined as 'for business purposes' without specific timeframes.",
                    "severity": "medium"
                },
                {
                    "description": "CONTRACT-004: The vendor can assign the contract without the buyer's consent.",
                    "severity": "low"
                }
            ]
        }
        output = RiskExtractionOutput(**llm_response)
        assert len(output.risks) == 3
        
        # Check severity distribution
        high_risks = [r for r in output.risks if r.severity == "high"]
        medium_risks = [r for r in output.risks if r.severity == "medium"]
        low_risks = [r for r in output.risks if r.severity == "low"]
        
        assert len(high_risks) == 1
        assert len(medium_risks) == 1
        assert len(low_risks) == 1

    def test_no_risks_found_response(self):
        """Test parsing response when no risks are found."""
        llm_response = {"risks": []}
        output = RiskExtractionOutput(**llm_response)
        assert len(output.risks) == 0
