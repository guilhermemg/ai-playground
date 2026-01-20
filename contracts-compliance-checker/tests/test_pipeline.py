"""Unit tests for the pipeline module with mocked LLM calls."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.risk_schema import RiskExtractionOutput, Risk


class TestPipelineWithMockedLLM:
    """Tests for the pipeline using mocked LLM responses."""

    @pytest.fixture
    def sample_prompt_template(self):
        """Return a sample prompt template."""
        return """You are a compliance analyst.
Analyze this contract: {context}
Return JSON with risks."""

    @pytest.fixture
    def sample_contract_text(self):
        """Return sample contract text."""
        return "The vendor may change prices at any time without notice."

    @pytest.fixture
    def mock_llm_response(self):
        """Return a mock LLM response dictionary."""
        return {
            "risks": [
                {"description": "CONTRACT-001: Unilateral price changes without notice", "severity": "medium"},
            ]
        }

    def test_pipeline_returns_risk_extraction_output(self, sample_prompt_template, sample_contract_text, mock_llm_response):
        """Test that pipeline returns a RiskExtractionOutput object."""
        with patch('src.pipeline.call_llm', return_value=mock_llm_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(sample_contract_text, sample_prompt_template)
            
            assert isinstance(result, RiskExtractionOutput)
            assert len(result.risks) == 1

    def test_pipeline_extracts_correct_risks(self, sample_prompt_template, sample_contract_text, mock_llm_response):
        """Test that pipeline extracts the correct risk information."""
        with patch('src.pipeline.call_llm', return_value=mock_llm_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(sample_contract_text, sample_prompt_template)
            
            assert result.risks[0].description == "CONTRACT-001: Unilateral price changes without notice"
            assert result.risks[0].severity == "medium"

    def test_pipeline_handles_empty_risks(self, sample_prompt_template):
        """Test that pipeline handles contracts with no risks."""
        empty_response = {"risks": []}
        contract_text = "This is a perfectly compliant contract."
        
        with patch('src.pipeline.call_llm', return_value=empty_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(contract_text, sample_prompt_template)
            
            assert isinstance(result, RiskExtractionOutput)
            assert len(result.risks) == 0

    def test_pipeline_handles_multiple_risks(self, sample_prompt_template):
        """Test that pipeline handles multiple risks correctly."""
        multi_risk_response = {
            "risks": [
                {"description": "GDPR-001: Missing consent", "severity": "high"},
                {"description": "GDPR-002: Data transfer issues", "severity": "high"},
                {"description": "CONTRACT-003: Liability waiver", "severity": "medium"},
                {"description": "FINANCIAL-001: No refund policy", "severity": "low"},
            ]
        }
        contract_text = "Complex contract with many issues."
        
        with patch('src.pipeline.call_llm', return_value=multi_risk_response):
            from src.pipeline import run_pipeline
            result = run_pipeline(contract_text, sample_prompt_template)
            
            assert len(result.risks) == 4
            high_risks = [r for r in result.risks if r.severity == "high"]
            assert len(high_risks) == 2

    def test_pipeline_logs_event(self, sample_prompt_template, sample_contract_text, mock_llm_response):
        """Test that pipeline logs events correctly."""
        with patch('src.pipeline.call_llm', return_value=mock_llm_response):
            with patch('src.pipeline.log_event') as mock_log:
                from src.pipeline import run_pipeline
                result = run_pipeline(sample_contract_text, sample_prompt_template)
                
                mock_log.assert_called_once()
                log_data = mock_log.call_args[0][0]
                
                assert "prompt_version" in log_data
                assert "latency" in log_data
                assert "num_risks" in log_data
                assert log_data["num_risks"] == 1

    def test_pipeline_formats_prompt_correctly(self, sample_contract_text, mock_llm_response):
        """Test that the prompt template is formatted with contract text."""
        template = "Analyze: {context}"
        
        with patch('src.pipeline.call_llm', return_value=mock_llm_response) as mock_call:
            from src.pipeline import run_pipeline
            run_pipeline(sample_contract_text, template)
            
            # Verify the prompt was called with formatted text
            called_prompt = mock_call.call_args[0][0]
            assert sample_contract_text in called_prompt


class TestPipelineErrorHandling:
    """Tests for pipeline error handling."""

    @pytest.fixture
    def sample_prompt_template(self):
        return "Analyze: {context}"

    def test_pipeline_raises_on_invalid_llm_response(self, sample_prompt_template):
        """Test that pipeline raises error on invalid LLM response structure."""
        invalid_response = {"invalid_key": "no risks here"}
        
        with patch('src.pipeline.call_llm', return_value=invalid_response):
            from src.pipeline import run_pipeline
            with pytest.raises(Exception):  # Will raise ValidationError
                run_pipeline("Some contract", sample_prompt_template)

    def test_pipeline_raises_on_invalid_severity(self, sample_prompt_template):
        """Test that pipeline raises error on invalid severity value."""
        invalid_response = {
            "risks": [{"description": "Test", "severity": "critical"}]
        }
        
        with patch('src.pipeline.call_llm', return_value=invalid_response):
            from src.pipeline import run_pipeline
            with pytest.raises(Exception):
                run_pipeline("Some contract", sample_prompt_template)
