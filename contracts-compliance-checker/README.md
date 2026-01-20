# Contracts Compliance Checker

This folder contains a **Contracts Compliance Checker** that leverages [LangChain](https://github.com/langchain-ai/langchain), [OpenAI's GPT-3.5-Turbo](https://platform.openai.com/), and structured output parsing to analyze contracts for compliance risks. It's part of the larger [ai-playground](https://github.com/guilhermemg/ai-playground) repository, which showcases various experimental AI projects and integrations.

---

## Table of Contents

1. [Overview](#overview)  
2. [Features](#features)  
3. [Project Structure](#project-structure)  
4. [Installation](#installation)  
5. [Usage](#usage)  
6. [Canary Deployment](#canary-deployment)  
7. [Compliance Rules](#compliance-rules)  
8. [Testing](#testing)  
9. [Future Implementations](#future-implementations)  
10. [License](#license)  
11. [Contact](#contact)

---

## Overview

This Contracts Compliance Checker is an LLMOps-focused project designed to **automatically analyze contracts for compliance risks** using LangChain and OpenAI. The system can:
- **Extract** potential compliance risks from contract text.
- **Classify** risks by severity (low, medium, high).
- **Reference** specific compliance rules that are violated.
- **Evaluate** extraction accuracy against expected outputs.
- **A/B test** different prompt versions with canary deployment.

By combining structured Pydantic outputs with a versioned prompt system and canary deployments, this project demonstrates production-ready LLMOps practices.

---

## Features

- **Structured LLM Outputs**: Uses Pydantic models to ensure consistent, type-safe responses from the LLM.
- **Prompt Versioning**: Multiple prompt versions (v1, v2) with different strategies for risk extraction.
- **Canary Deployment**: A/B testing framework to gradually roll out new prompts and compare performance.
- **Compliance Rule Engine**: Checks contracts against 15 predefined compliance rules across 5 categories.
- **Regression Testing**: 51 automated tests to ensure consistent behavior across changes.
- **Production Logging**: Captures latency, prompt versions, severity breakdowns, and extraction metrics.
- **Extensible Design**: Easy to add new rules, contracts, or prompt variations.

---

## Project Structure

Inside the `contracts-compliance-checker` folder, you'll find:

```
contracts-compliance-checker/
├── data/
│   ├── samples.json           # 6 sample contracts for testing
│   ├── rules.json             # 15 compliance rules definition
│   └── expected_outputs.json  # Expected extraction results
├── prompts/
│   ├── risk_extraction_v1.txt # Basic prompt template
│   └── risk_extraction_v2.txt # Enhanced prompt with chain-of-thought
├── schemas/
│   └── risk_schema.py         # Pydantic models for structured output
├── src/
│   ├── llm_client.py          # LangChain/OpenAI integration
│   ├── pipeline.py            # Main extraction pipeline
│   ├── canary.py              # Canary deployment logic
│   ├── evaluator.py           # Accuracy evaluation logic
│   └── logger.py              # Event logging
├── tests/
│   ├── test_pipeline.py       # Pipeline unit tests
│   ├── test_schema.py         # Schema validation tests
│   ├── test_regression.py     # Regression tests
│   └── test_canary.py         # Canary deployment tests
├── run_pipeline.py            # CLI to analyze contracts
├── run_canary.py              # CLI for canary A/B testing
├── run_evaluation.py          # CLI to run evaluations
├── requirements.txt           # Python dependencies
└── README.md
```

**Key Files**

1. **`src/llm_client.py`**  
   - Configures LangChain with ChatOpenAI (`gpt-3.5-turbo`).
   - Uses `PydanticOutputParser` for structured JSON responses.
   - Handles API calls and response parsing.

2. **`src/pipeline.py`**  
   - Orchestrates the extraction workflow.
   - Integrates with canary deployment for version selection.
   - Logs performance metrics (latency, risk count, severity breakdown).

3. **`src/canary.py`**  
   - Manages A/B testing between prompt versions.
   - Configurable traffic splitting (e.g., 20% to v2).
   - Tracks metrics for comparison.

4. **`schemas/risk_schema.py`**  
   - Defines `Risk` and `RiskExtractionOutput` Pydantic models.
   - Ensures type safety and validation.

---

## Installation

1. **Clone the Repository** (if you haven't already cloned the entire `ai-playground`):
   
   ```bash
   git clone https://github.com/guilhermemg/ai-playground.git
   cd ai-playground/contracts-compliance-checker
   ```

2. **Create and Activate a Virtual Environment**

    ```bash
    conda create -n contracts-compliance-checker python=3.12
    conda activate contracts-compliance-checker
    ```

3. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables**

    Create a `.env` file (not committed to Git) and include your OpenAI API key:

    ```bash
    OPENAI_API_KEY=sk-xxxx
    ```

---

## Usage

### Analyze All Sample Contracts

```bash
python run_pipeline.py
```

**Sample Output:**

```
============================================================
Contract #1: Software License Agreement - TechCorp
============================================================

Found 2 compliance risks:

  1. 🟡 [MEDIUM] CONTRACT-003: Complete liability waiver without reasonable limits
  2. 🟢 [LOW] Missing governing law specifics beyond state jurisdiction

```

### Run Evaluation

```bash
python run_evaluation.py
```

This compares extracted risks against expected outputs and reports accuracy.

### Programmatic Usage

```python
from src.pipeline import run_pipeline

# Using canary deployment (auto-selects version)
result = run_pipeline("Your contract text here...")

# Or with explicit prompt
prompt = open("prompts/risk_extraction_v2.txt").read()
result = run_pipeline("Your contract text here...", prompt_template=prompt, version="v2")

for risk in result.risks:
    print(f"[{risk.severity.upper()}] {risk.description}")
```

---

## Canary Deployment

The project includes a canary deployment system for A/B testing prompt versions.

### Quick Start

```bash
# Run with canary selection (default: 20% v2, 80% v1)
python run_canary.py

# Force all traffic to v2
python run_canary.py --v2

# Force all traffic to v1
python run_canary.py --v1

# Set custom rollout percentage
python run_canary.py --rollout 50

# View comparison metrics
python run_canary.py --metrics
```

### Prompt Versions

| Version | Description |
|---------|-------------|
| **v1** | Basic prompt with rule list and JSON output format |
| **v2** | Enhanced prompt with chain-of-thought reasoning, violation indicators, severity guidelines, and examples |

### Metrics Comparison

```bash
$ python run_canary.py --metrics

======================================================================
CANARY METRICS COMPARISON
======================================================================

V1 Performance:
  Samples:         12
  Avg Latency:     1.23s
  Avg Risks Found: 2.5
  Avg High:        0.8
  Avg Medium:      1.2
  Avg Low:         0.5

V2 Performance:
  Samples:         8
  Avg Latency:     1.45s
  Avg Risks Found: 3.2
  Avg High:        1.1
  Avg Medium:      1.5
  Avg Low:         0.6

Comparison (v2 vs v1):
  Latency Diff:    +17.9%
  Risk Detection:  +0.7 risks
  High Severity:   +0.3
```

### Programmatic Canary Control

```python
from src.canary import get_canary

canary = get_canary()

# Get current rollout percentage
print(f"v2 rollout: {canary.config['v2_percentage']}%")

# Change rollout percentage
canary.set_rollout_percentage(50)

# Disable canary (all traffic to v1)
canary.disable()

# Enable canary
canary.enable()

# Get comparison metrics
metrics = canary.get_metrics()
```

---

## Compliance Rules

The checker validates contracts against 15 rules in 5 categories:

| Category | Rule ID | Description |
|----------|---------|-------------|
| **Data Protection** | GDPR-001 | Sub-processor consent required |
| | GDPR-002 | Data transfer adequacy requirements |
| | GDPR-003 | Clear data retention periods |
| | GDPR-004 | Privacy disclosure requirements |
| **Contract Fairness** | CONTRACT-001 | No unilateral price changes |
| | CONTRACT-002 | Fair indemnification clauses |
| | CONTRACT-003 | Reasonable liability limits |
| | CONTRACT-004 | Assignment consent required |
| **Employment Law** | EMPLOYMENT-001 | Termination notice periods |
| | EMPLOYMENT-002 | Reasonable non-compete scope |
| | EMPLOYMENT-003 | Arbitration clause disclosure |
| **Service Levels** | SLA-001 | Binding uptime commitments |
| | SLA-002 | Data location disclosure |
| **Financial Terms** | FINANCIAL-001 | Fair refund policies |
| | FINANCIAL-002 | Expense documentation |

Rules are defined in `data/rules.json` and can be extended.

### Sample Contracts

The project includes 6 sample contracts for testing:

1. **Software License Agreement** - Tests liability waivers
2. **Data Processing Agreement** - Tests GDPR compliance
3. **Employment Contract** - Tests non-compete and arbitration
4. **Vendor Services Agreement** - Tests pricing and indemnification
5. **SaaS Subscription** - Tests uptime and data location
6. **Consulting Agreement** - Tests expense and warranty terms

---

## Testing

Run the full test suite (51 tests):

```bash
pytest tests/ -v
```

### Test Categories

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_schema.py` | 14 | Pydantic model validation |
| `test_pipeline.py` | 8 | Pipeline logic with mocked LLM |
| `test_regression.py` | 14 | Data integrity and regression scenarios |
| `test_canary.py` | 15 | Canary deployment logic |

### Test Coverage

- ✅ Schema validation (valid/invalid severity, required fields)
- ✅ Pipeline extraction with mocked responses
- ✅ Error handling for malformed LLM responses
- ✅ Sample data file integrity
- ✅ Rule coverage across all categories
- ✅ Canary traffic splitting and metrics

---

## Future Implementations

Looking ahead, here are potential enhancements:

* **Multi-Document Analysis**: Analyze multiple related contracts together for cross-reference compliance.
* **Custom Rule Builder**: UI to define custom compliance rules without code changes.
* **Risk Scoring**: Weighted risk scores based on rule severity and frequency.
* **Contract Comparison**: Compare two contract versions to highlight compliance changes.
* **Audit Trail**: Full traceability of all extractions for compliance reporting.
* **Fine-tuned Models**: Train specialized models for specific industries (healthcare, finance, etc.).
* **Prompt Optimization**: Automated prompt tuning based on canary metrics.

---

## License

Unless otherwise specified, this project is available under an open-source license (e.g., MIT). Check the LICENSE file in the repository's root for more details.

---

## Contact

Interested in learning more or collaborating on similar AI-driven projects?

I'd love to connect! Feel free to reach out on [LinkedIn](https://www.linkedin.com/in/ggadelha/) or [GitHub](https://github.com/guilhermemg) so we can explore new ideas, discuss potential opportunities, and continue pushing the boundaries of what's possible with AI.
