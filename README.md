# Kaggle Capstone Submission Coach

Kaggle Capstone Submission Coach is a Streamlit app for checking whether this repository is ready for the Kaggle AI Agents capstone submission. It reads the competition brief in `requirement.md`, scans the current repository, runs a deterministic multi-agent readiness workflow, and produces a structured report with a checklist, readiness score, judge evidence dashboard, gaps, next steps, and draft submission artifacts.

The app is intentionally analysis-only. It does not edit the repository, create GitHub issues, deploy anything, or require a live model call for the default demo path.

## Problem

The Kaggle capstone submission requires more than code. A valid submission needs a Kaggle Writeup, media gallery, YouTube video, public project link, setup instructions, and clear evidence for at least three course concepts. The highest risk is missing judge-visible evidence near the deadline.

This project turns the competition brief and repository state into an actionable readiness package.

## Solution

The app gives a capstone team one local command that turns repository evidence into a submission package. It combines deterministic agent roles, MCP-compatible inspection tools, security scanning, optional Gemini-backed summaries, and downloadable draft artifacts into one Streamlit review surface.

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
- Displays a judge-facing dashboard for rubric readiness, concept evidence, required assets, and scoring next steps.
- Scans for likely committed secrets, risky environment files, and unsafe read-boundary attempts without exposing full secret values.
- Preserves deterministic fallback when no Gemini API key is configured.
- Uses a Gemini model-backed runtime adapter when `GEMINI_API_KEY` or `GOOGLE_API_KEY` is configured.
- Generates draft README, Kaggle Writeup, and five-minute video script content.
- Exports the full readiness report as Markdown.

## Architecture

The core analysis workflow is separate from Streamlit:

```text
app.py
  -> build_default_report()
  -> kaggle_capstone_coach.workflow.run_readiness_workflow()
  -> optional Gemini adapter gated by GEMINI_API_KEY or GOOGLE_API_KEY
  -> kaggle_capstone_coach.mcp_tools.LocalMcpToolLayer
  -> ReadinessReport.to_markdown()
```

`app.py` is a thin UI adapter. The workflow module owns deterministic agent findings, scoring, gap analysis, and Markdown export. Repository scanning, checklist data, and security checks are routed through `LocalMcpToolLayer` so the same analysis capabilities are available as MCP-compatible tools. Tests exercise the workflow and tool interfaces rather than Streamlit internals.

The multi-agent workflow uses four specialist roles:

- Requirement Analyst extracts hard submission requirements and scoring criteria.
- Repo Auditor maps repository evidence to judge-visible assets.
- Submission Strategist prioritizes the gaps that affect scoring.
- Communication Coach drafts public-facing submission material.

The project demonstrates an ADK-style multi-agent design with optional Gemini-backed summaries. The default deterministic path remains available so a judge can run the app without a live model call.

## Setup

Use Python 3.14 or a recent Python 3 version.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Optional: configure Gemini-backed summaries by copying `.env.example` to a local `.env` file or by setting variables in your shell or deployment dashboard. Real `.env` files are ignored by git.

```powershell
$env:GOOGLE_API_KEY = "replace_me"
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

No API key is required for the default local demo. When `GEMINI_API_KEY` and `GOOGLE_API_KEY` are absent, the workflow uses deterministic fallback mode.

The workflow also supports a Gemini-backed adapter path gated by `GEMINI_API_KEY` or `GOOGLE_API_KEY`. Tests use fake adapters to verify configured and missing-key behavior without making live model calls.

Set the environment variable only in your local shell or deployment environment:

```powershell
$env:GEMINI_API_KEY = "your-local-key"
$env:GOOGLE_API_KEY = $env:GEMINI_API_KEY
```

Google AI Studio examples use `GEMINI_API_KEY`; this app accepts either name. If both are set, the app prefers `GEMINI_API_KEY`.

Do not commit API keys, passwords, tokens, or private credentials to this repository.

## Deployment Option

Streamlit Community Cloud is the simplest deployment path:

1. Push this repository to a public GitHub repository.
2. Create a Streamlit Community Cloud app from the repository.
3. Set the main file path to `app.py`.
4. Let Streamlit install dependencies from `requirements.txt`.
5. Optionally add `GOOGLE_API_KEY` or `GEMINI_API_KEY` in the Streamlit secrets/settings UI.

The deployed app still works without an API key because deterministic fallback mode is the default. If a live deployment is not available, the public GitHub repository can serve as the project link because this README includes setup, test, local run, MCP, security, Gemini configuration, and deployment guidance.

## Submission Package

Durable draft submission assets live in `docs/submission/`:

- `kaggle-writeup-draft.md`
- `five-minute-video-script.md`
- `youtube-demo-checklist.md`
- `deployment-checklist.md`
- `media-gallery/cover.png`
- `media-gallery/streamlit-readiness-overview.png`
- `media-gallery/judge-evidence-dashboard.png`
- `media-gallery/mcp-tools-output.png`
- `media-gallery/security-and-downloads.png`
- `media-gallery/README.md`

The running app can also generate downloadable README, writeup, video script, and full report artifacts from the current repository state.

Deployment details live in `docs/submission/deployment-checklist.md`. The repo includes `.streamlit/config.toml` for headless deployment and `.streamlit/secrets.toml.example` for optional `GOOGLE_API_KEY` / `GEMINI_API_KEY` configuration. Real `.streamlit/secrets.toml` files are ignored by git.

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

1. Final YouTube recording using `docs/submission/five-minute-video-script.md` and `docs/submission/youtube-demo-checklist.md`.
2. Optional hosted Streamlit Community Cloud deployment using `docs/submission/deployment-checklist.md`.

## Status

This repository is packaged to serve as the public project link for the capstone submission if needed. It is ready for local review and has documented next steps for final media and optional hosting.
