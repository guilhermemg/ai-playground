# Evaluation Guide

## Overview

The system includes a comprehensive evaluation module powered by [RAGAS](https://docs.ragas.io/) that measures the quality of the entire pipeline: routing accuracy, agent response quality, and RAG retrieval quality.

## Metrics

### RAGAS Metrics

| Metric | What it measures | Range |
| --- | --- | --- |
| **Faithfulness** | Are answers grounded in the retrieved context? | 0-1 |
| **Answer Relevancy** | Are answers relevant to the question? | 0-1 |
| **Context Precision** | Is the retrieved context precise and useful? | 0-1 |
| **Context Recall** | Does retrieval capture all relevant information? | 0-1 |
| **Answer Correctness** | How correct is the answer vs. ground truth? | 0-1 |

### Custom Metrics

| Metric | What it measures |
| --- | --- |
| **Routing Accuracy** | Does the router send questions to the correct domain agent? |

## Golden Datasets

Golden datasets are JSON files in `backend/app/evaluation/golden_datasets/` that contain ground-truth Q&A pairs per domain.

### Format

```json
{
  "domain": "medicine",
  "questions": [
    {
      "question": "What is the mechanism of action of aspirin?",
      "ground_truth": "Aspirin irreversibly inhibits cyclooxygenase...",
      "expected_agent": "medicine",
      "contexts": ["Aspirin acts by irreversibly acetylating..."]
    }
  ]
}
```

### Fields

- `question`: The question to evaluate
- `ground_truth`: The ideal/correct answer for comparison
- `expected_agent`: The domain name of the agent that should handle this question (for routing accuracy)
- `contexts`: Reference context passages (for faithfulness and context metrics)

### Available Datasets

- `medicine.json` - 3 questions on pharmacology and pathophysiology
- `physics.json` - 3 questions on mechanics and quantum physics
- `math.json` - 2 questions on calculus and linear algebra
- `law.json` - 2 questions on legal systems and principles
- `engineering.json` - 2 questions on materials science and control systems

### Adding New Datasets

Create a new JSON file following the format above. The evaluator automatically discovers all `.json` files in the `golden_datasets/` directory.

## Running Evaluations

### Via the UI

1. Navigate to the **Evaluation** page
2. Select a domain (or "All Domains")
3. Click **Run Evaluation**
4. Wait for the run to complete (shown in Run History)
5. View metric cards, trend charts, and per-question results

### Via the API

```bash
# Run evaluation for all domains
curl -X POST http://localhost:8000/api/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{"domain": null}'

# Run evaluation for a specific domain
curl -X POST http://localhost:8000/api/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{"domain": "medicine"}'

# Get results
curl http://localhost:8000/api/evaluation/results
```

### Prerequisites

For evaluation to work:
1. At least one active agent must exist for the domain(s) being evaluated
2. The agent's domain name must match the `expected_agent` field in the golden dataset

## Evaluation Pipeline

1. Load golden dataset questions (filtered by domain if specified)
2. For each question:
   - Feed it through the LangGraph router
   - Record which agent was selected (for routing accuracy)
   - Execute the selected agent to get an answer
   - Collect retrieved contexts (for RAG agents)
3. Build a RAGAS `Dataset` with questions, answers, contexts, and ground truths
4. Run RAGAS metrics
5. Calculate routing accuracy
6. Store results in PostgreSQL
7. Return summary with per-question breakdown

## Interpreting Results

### Good Scores
- Faithfulness > 0.8: Answers are well-grounded in context
- Answer Relevancy > 0.8: Answers address the question directly
- Answer Correctness > 0.7: Answers align with ground truth
- Routing Accuracy > 0.9: Router consistently picks the right agent

### Improvement Actions
- Low faithfulness → Improve RAG retrieval (more/better documents, tuning chunk size)
- Low relevancy → Refine agent prompts to focus on the question
- Low correctness → Upgrade model, add more context, improve prompts
- Low routing accuracy → Add clearer domain descriptions, add more agents for ambiguous domains

## Exporting Results

The Evaluation Dashboard includes an **Export CSV** button that downloads per-question results for offline analysis.
