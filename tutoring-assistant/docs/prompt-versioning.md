# Prompt Versioning

## Overview

Every expert agent in the system has versioned prompts. When a professor edits an agent's prompt, a new version is created -- the old version is never overwritten. This enables:

- **Rollback**: Switch back to any previous prompt version
- **A/B testing**: Compare agent performance across prompt versions
- **Audit trail**: See exactly what prompt was active at any point
- **Docker traceability**: Docker images are tagged with the prompt template version they ship with

## How It Works

### Standard Template

When a professor creates a new agent, the system generates an initial prompt from the standard template:

```
System Message:
  You are an expert in {domain}. Your role is to evaluate student answers
  to questions within your domain of expertise.

  When evaluating answers, you must:
  1. Assess factual accuracy within {domain}
  2. Evaluate depth of understanding
  3. Identify misconceptions specific to {domain}
  4. Provide constructive feedback with correct explanations
  5. Score the answer on a 0-100 scale

Full Prompt:
  You are {agent_name}, a domain expert in {domain}.
  [... structured evaluation instructions ...]
```

This becomes **version 1** of the agent's prompt.

### Editing Prompts

In the Agent Config panel, professors can:

1. Edit the **System Message** (defines the agent's persona and behavior)
2. Edit the **Full Prompt** (the complete template used for evaluations)
3. Click **Save New Version** to create a new version

The new version becomes immediately active. The previous version is preserved.

### Version History

The Version History panel shows all versions for an agent:
- Version number and creation timestamp
- Ability to view any version's content
- **Activate** button to switch the active version

### API Endpoints

```
GET  /api/agents/{id}/prompt              → Current active prompt
PUT  /api/agents/{id}/prompt              → Create new version (auto-activates)
GET  /api/agents/{id}/prompt/versions     → List all versions
PUT  /api/agents/{id}/prompt/versions/{v}/activate → Switch active version
```

## Database Schema

```
prompt_versions
├── id (UUID, PK)
├── agent_id (FK → agents.id)
├── version (int, auto-incremented per agent)
├── system_message (text)
├── full_prompt (text)
└── created_at (timestamp)

agents
├── ...
└── active_prompt_version_id (FK → prompt_versions.id)
```

## Docker Image Tagging

Docker images carry the prompt template version in their tag:

```
tutoring-backend:1.0.0-prompt-v1
tutoring-backend:1.1.0-prompt-v2
```

The Dockerfile also includes a `LABEL prompt_version=v1` for programmatic access.

Note: The image tag reflects the **standard template** version shipped with the image. Runtime prompt edits by professors are stored in the database and are independent of the Docker image.

## LangSmith Integration

Every LLM trace in LangSmith includes:
- `prompt_version`: The version number of the prompt used
- `agent_name`: The name of the agent
- `agent_domain`: The domain of expertise

This allows filtering LangSmith traces by prompt version to compare performance across versions.
