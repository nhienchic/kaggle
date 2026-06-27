# Kaggle Capstone Submission Coach

Kaggle Capstone Submission Coach is a Streamlit app for checking whether this repository is ready for the Kaggle AI Agents capstone submission. It reads the competition brief in `requirement.md`, scans the current repository, runs a deterministic multi-agent readiness workflow, and produces a structured report with a checklist, readiness score, gaps, next steps, and draft submission artifacts.

The app is intentionally analysis-only. It does not edit the repository, create GitHub issues, deploy anything, or require a live model call for the first demo path.

## Problem

The Kaggle capstone submission requires more than code. A valid submission needs a Kaggle Writeup, media gallery, YouTube video, public project link, setup instructions, and clear evidence for at least three course concepts. The highest risk is missing judge-visible evidence near the deadline.

This project turns the competition brief and repository state into an actionable readiness package.

## Current Features

- Loads the local competition brief from `requirement.md`.
- Scans the current repository while ignoring Git internals and generated Python cache files.
- Runs four deterministic specialist agents:
  - Requirement Analyst
  - Repo Auditor
  - Submission Strategist
  - Communication Coach
- Exposes MCP-compatible local tools for requirement reading, repository scanning, readiness checklist generation, and security signal checks.
- Produces a readiness score and submission checklist.
- Maps current evidence and missing assets.
- Scans for likely committed secrets, risky environment files, and unsafe read-boundary attempts without exposing full secret values.
- Preserves deterministic fallback when no `GOOGLE_API_KEY` is configured.
- Supports a model-backed runtime adapter path when `GOOGLE_API_KEY` is configured.
- Generates draft README, Kaggle Writeup, and five-minute video script content.
- Exports the full readiness report as Markdown.

## Architecture

The core analysis workflow is separate from Streamlit:

```text
app.py
  -> build_default_report()
  -> kaggle_capstone_coach.workflow.run_readiness_workflow()
  -> optional model adapter gated by GOOGLE_API_KEY
  -> kaggle_capstone_coach.mcp_tools.LocalMcpToolLayer
  -> ReadinessReport.to_markdown()
```

`app.py` is a thin UI adapter. The workflow module owns deterministic agent findings, scoring, gap analysis, and Markdown export. Repository scanning, checklist data, and security checks are routed through `LocalMcpToolLayer` so the same analysis capabilities are available as MCP-compatible tools. Tests exercise the workflow and tool interfaces rather than Streamlit internals.

## Setup

Use Python 3.14 or a recent Python 3 version.

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run tests:

```powershell
python -m unittest discover -s tests
```

Launch the app:

```powershell
python -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## MCP-Compatible Tools

Inspect available local tools:

```powershell
python -m kaggle_capstone_coach.mcp_tools list --repo-root .
```

Run a tool:

```powershell
python -m kaggle_capstone_coach.mcp_tools run scan_repository_files --repo-root .
```

Run the checklist tool with requirement text:

```powershell
python -m kaggle_capstone_coach.mcp_tools run produce_readiness_checklist --repo-root . --requirement-text "Submission Requirements"
```

The current tool layer exposes:

- `read_competition_requirements`
- `scan_repository_files`
- `produce_readiness_checklist`
- `check_security_signals`

## Configuration

No API key is required for the default local demo. When `GOOGLE_API_KEY` is absent, the workflow uses deterministic fallback mode.

The workflow also supports a model-backed adapter path gated by `GOOGLE_API_KEY`. Tests use a fake model adapter to verify configured and missing-key behavior without making live model calls.

Set the environment variable only in your local shell or deployment environment:

```powershell
$env:GOOGLE_API_KEY = "your-local-key"
```

Do not commit API keys, passwords, tokens, or private credentials to this repository.

## Testing

The primary test seam is the readiness workflow:

```python
from kaggle_capstone_coach.workflow import run_readiness_workflow

report = run_readiness_workflow(requirement_text, repo_root)
markdown = report.to_markdown()
```

This keeps tests focused on observable behavior: checklist status, report structure, deterministic mode, and Markdown output.

## Submission Roadmap

Next evidence to add:

1. Deployability documentation and deployment option notes.
2. Live Gemini / Google ADK adapter implementation if needed beyond the tested runtime seam.
3. Kaggle Writeup draft refined into final submission form.
4. Media gallery cover image and demo screenshots.
5. YouTube demo script and final video.

## Status

This repository currently implements the first runnable readiness report slice. It is ready for local review, but not yet a complete Kaggle submission package.
