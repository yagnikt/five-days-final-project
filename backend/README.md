# AI-Driven Travel Itinerary Planner - Backend

Agent codebase built using the Google ADK and `agents-cli`.

## Project Structure

```
backend/
├── app/                             # Core agent & API code (Consolidated ADK)
│   ├── app_utils/                   # Utilities and helper modules
│   ├── agent.py                     # Main ADK routing agent logic
│   ├── itinerary_agent.py           # Primary travel agent with Google Search grounding
│   ├── evaluator_agent.py           # Gemini Flash LLM-as-a-judge real-time evaluator
│   ├── orchestrator.py              # Real-time grading orchestration & agent loop
│   ├── database.py                  # Firestore collections and Google Agent Memory Bank integration
│   ├── fast_api_app.py              # FastAPI server implementing routes for dashboard & client polling
│   ├── security.py                  # Vertex AI Safety Settings and input validation
│   └── main.py                      # Main entrypoint script to launch the FastAPI server
├── tests/                           # Offline unit, integration, and load test suite
│   └── evalsets/                    # Evaluation datasets for regression checks
├── Dockerfile                       # Container deployment definition
├── agents-cli-manifest.yaml         # Deployment and evaluation configuration metadata
├── GEMINI.md                        # AI-assisted development instructions
└── pyproject.toml                   # Project dependencies and environment metadata
```

> 💡 **Tip:** Use [Antigravity CLI](https://antigravity.google/) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Agent Runtime                                                                |
| `agents-cli publish gemini-enterprise` | Register deployed agent to Gemini Enterprise                    || [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | Launch A2A Protocol Inspector                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `backend/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.
