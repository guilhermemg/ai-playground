import json
from src.pipeline import run_pipeline

# Load prompt and sample contracts
prompt = open("prompts/risk_extraction_v1.txt").read()
samples = json.load(open("data/samples.json"))

# Analyze each contract
for sample in samples:
    print(f"\n{'='*60}")
    print(f"Contract #{sample['id']}: {sample['title']}")
    print('='*60)
    
    output = run_pipeline(sample["text"], prompt)
    
    print(f"\nFound {len(output.risks)} compliance risks:\n")
    for i, risk in enumerate(output.risks, 1):
        severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk.severity, "⚪")
        print(f"  {i}. {severity_icon} [{risk.severity.upper()}] {risk.description}")
    
    print()
