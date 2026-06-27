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
- Produces a readiness score and submission checklist.
- Maps current evidence and missing assets.
- Generates draft README, Kaggle Writeup, and five-minute video script content.
- Exports the full readiness report as Markdown.

## Architecture

The core analysis workflow is separate from Streamlit:

```text
app.py
  -> build_default_report()
  -> kaggle_capstone_coach.workflow.run_readiness_workflow()
  -> ReadinessReport.to_markdown()
```

`app.py` is a thin UI adapter. The workflow module owns repository scanning, deterministic agent findings, checklist generation, scoring, gap analysis, and Markdown export. Tests exercise the workflow interface rather than Streamlit internals.

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

## Configuration

The current slice uses deterministic fallback behavior only, so no API key is required.

Future Gemini / Google ADK integration should use environment variables such as `GOOGLE_API_KEY`. Do not commit API keys, passwords, tokens, or private credentials to this repository.

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

1. MCP-compatible tool layer for requirement reading and repo scanning.
2. Security scan for likely secrets and unsafe credential files.
3. Deployability documentation and deployment option notes.
4. Kaggle Writeup draft refined into final submission form.
5. Media gallery cover image and demo screenshots.
6. YouTube demo script and final video.

## Status

This repository currently implements the first runnable readiness report slice. It is ready for local review, but not yet a complete Kaggle submission package.
