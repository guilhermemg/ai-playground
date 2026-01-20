from schemas.risk_schema import RiskExtractionOutput
from src.llm_client import call_llm
from src.logger import log_event
from src.canary import get_canary, CanaryResult
from datetime import datetime, timezone
import time


def run_pipeline(text: str, prompt_template: str = None, version: str = None, contract_id: str = None):
    """
    Run the compliance risk extraction pipeline.
    
    Args:
        text: Contract text to analyze
        prompt_template: Optional prompt template (if None, uses canary selection)
        version: Optional version override ("v1" or "v2")
        contract_id: Optional contract identifier for logging
        
    Returns:
        RiskExtractionOutput: Extracted risks
    """
    canary = get_canary()
    
    # Determine which prompt to use
    if prompt_template is not None:
        # Legacy mode: use provided template, assume v1
        selected_version = version or "v1"
    else:
        # Canary mode: select version and get prompt
        selected_version, prompt_template = canary.get_prompt(version)
    
    start = time.time()
    prompt = prompt_template.format(context=text)
    response = call_llm(prompt)
    output = RiskExtractionOutput(**response)
    latency = time.time() - start

    # Count risks by severity
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for risk in output.risks:
        severity_counts[risk.severity] = severity_counts.get(risk.severity, 0) + 1

    # Log to standard logs
    log_event({
        "prompt_version": selected_version,
        "latency": latency,
        "num_risks": len(output.risks),
        "severity_breakdown": severity_counts
    })
    
    # Log to canary logs for metrics
    canary_result = CanaryResult(
        version=selected_version,
        latency=latency,
        num_risks=len(output.risks),
        high_severity_count=severity_counts["high"],
        medium_severity_count=severity_counts["medium"],
        low_severity_count=severity_counts["low"],
        timestamp=datetime.now(timezone.utc).isoformat(),
        contract_id=contract_id
    )
    canary.log_result(canary_result)

    return output
