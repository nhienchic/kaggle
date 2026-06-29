# Kaggle Capstone Submission Coach

Kaggle Capstone Submission Coach is a Streamlit app that checks whether this repository is ready for the Kaggle AI Agents capstone submission. It reads the local capstone brief, scans repository evidence, runs a multi-agent readiness workflow, and produces a judge-facing report with a readiness score, checklist, evidence dashboard, security summary, prioritized next steps, and downloadable draft artifacts.

The app is analysis-only. It does not edit files, create issues, deploy infrastructure, or require a live model call for the default demo path.

## Live Links

- Live app: https://kaggle-perdwfgy6aujyfbxsf2mhh.streamlit.app/
- Demo video: https://youtu.be/GGFt-Wg-aCo
- Source repository: https://github.com/nhienchic/kaggle
- Kaggle Writeup: https://kaggle.com/competitions/vibecoding-agents-capstone-project/writeups/new-writeup-1782309198303

## Problem

The Kaggle AI Agents capstone submission requires more than working code. A valid submission needs a Kaggle Writeup, media gallery, YouTube video, public project link, setup instructions, and clear evidence for course concepts such as multi-agent design, MCP-style tool use, security, and deployability.

The risk near the deadline is that evidence exists but is scattered across code, docs, screenshots, and deployment settings. This app turns that scattered state into one readiness package.

## Solution

The app gives a capstone team one review surface for submission readiness:

- Parse the local competition brief in `requirement.md`.
- Scan the visible repository files used as evidence.
- Run four specialist agent roles over the same report contract.
- Produce a readiness score and required-asset checklist.
- Show a judge evidence dashboard for rubric readiness, course concept evidence, submission assets, and next steps.
- Scan for likely committed secrets and risky environment files.
- Generate downloadable Markdown artifacts for README, Kaggle Writeup, video script, and the full readiness report.

The default workflow is deterministic so a judge can run the app without API credentials. If `GEMINI_API_KEY` or `GOOGLE_API_KEY` is configured, the workflow can call the Gemini adapter for model-backed summaries. If the model call fails, the app falls back to deterministic output.

## Course Concept Map

| Course concept | Demonstrated where | Evidence |
| --- | --- | --- |
| Agent / multi-agent system | Code | `kaggle_capstone_coach/workflow.py` coordinates Requirement Analyst, Repo Auditor, Submission Strategist, and Communication Coach roles. |
| MCP-style tool layer | Code | `kaggle_capstone_coach/mcp_tools.py` exposes local tools for requirements, repo scanning, checklist generation, and security signals. |
| Security features | Code and UI | `kaggle_capstone_coach/security.py` checks likely secrets, risky env files, and repository read-boundary violations with redacted findings. |
| Deployability | Live app and video | Streamlit Community Cloud deployment plus documented local and cloud setup. |
| Gemini integration | Code | `kaggle_capstone_coach/gemini_adapter.py` provides optional model-backed summaries through deployment or local secrets. |

## What The App Shows

- Readiness score.
- Current model mode: deterministic, model-backed, or model-error fallback.
- Judge evidence dashboard.
- Rubric readiness table.
- Course concept evidence table.
- Required submission asset checklist.
- Prioritized next steps.
- Agent findings.
- Security summary.
- Download buttons for generated submission artifacts.

## Architecture

The Streamlit entrypoint is intentionally thin. The core workflow is importable and testable without running the UI.

```text
app.py
  -> build_default_report()
  -> kaggle_capstone_coach.workflow.run_readiness_workflow()
  -> optional kaggle_capstone_coach.gemini_adapter.GeminiModelAdapter
  -> kaggle_capstone_coach.mcp_tools.LocalMcpToolLayer
  -> kaggle_capstone_coach.security.scan_repository_security()
  -> ReadinessReport.to_markdown()
```

The multi-agent workflow uses four roles:

- Requirement Analyst extracts hard submission requirements and scoring criteria.
- Repo Auditor maps repository files to judge-visible evidence.
- Submission Strategist prioritizes gaps that affect scoring.
- Communication Coach drafts public-facing submission material.

Repository inspection, checklist data, and security checks go through `LocalMcpToolLayer`, which keeps the evidence-gathering operations explicit and reusable.

## Repository Layout

```text
app.py                              Streamlit UI entrypoint
kaggle_capstone_coach/workflow.py   Readiness workflow, scoring, dashboard, artifacts
kaggle_capstone_coach/mcp_tools.py  MCP-compatible local tool layer
kaggle_capstone_coach/security.py   Secret and repository-boundary scanner
kaggle_capstone_coach/gemini_adapter.py Optional Gemini-backed summaries
tests/                              Unit tests for workflow, tools, security, and package assets
docs/submission/                    Writeup, video, deployment, and media-gallery assets
.streamlit/                         Streamlit config and secrets example
```

## Quick Start

Use a recent Python 3 version.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

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

Open:

```text
http://localhost:8501
```

## MCP-Compatible Tools

List available local tools:

```powershell
python -m kaggle_capstone_coach.mcp_tools list --repo-root .
```

Run the repository scanner:

```powershell
python -m kaggle_capstone_coach.mcp_tools run scan_repository_files --repo-root .
```

Run the readiness checklist tool:

```powershell
python -m kaggle_capstone_coach.mcp_tools run produce_readiness_checklist --repo-root . --requirement-text "Submission Requirements"
```

Run the security signal check:

```powershell
python -m kaggle_capstone_coach.mcp_tools run check_security_signals --repo-root .
```

Available tools:

- `read_competition_requirements`
- `scan_repository_files`
- `produce_readiness_checklist`
- `check_security_signals`

## Gemini Configuration

No API key is required for deterministic mode.

For optional Gemini-backed summaries, set a key only in your local shell or deployment secrets. The app accepts either `GEMINI_API_KEY` or `GOOGLE_API_KEY`; if both are configured, `GEMINI_API_KEY` is preferred.

```powershell
$env:GEMINI_API_KEY = "your-local-key"
```

Do not commit API keys, passwords, tokens, `.env` files with real values, or Streamlit secrets. The repository includes safe templates:

- `.env.example`
- `.streamlit/secrets.toml.example`

## Security Model

The scanner checks repository files for:

- likely committed API keys, tokens, passwords, secrets, or credentials;
- risky committed `.env` files;
- unsafe reads outside the repository root;
- runtime secret mounts that should not be read by repository scans.

Findings redact secret-like values before display. The scanner is designed to inspect committed project evidence, not deployment secret contents.

## Deployment

The live deployment uses Streamlit Community Cloud:

1. Push the repository to GitHub.
2. Create a Streamlit Community Cloud app from the repository.
3. Set the main file path to `app.py`.
4. Let Streamlit install dependencies from `requirements.txt`.
5. Optionally add `GEMINI_API_KEY` or `GOOGLE_API_KEY` in the Streamlit secrets UI.
6. Confirm the public app loads without login and does not expose secrets.

Deployment details are documented in `docs/submission/deployment-checklist.md`.

## Submission Package

Durable submission assets live in `docs/submission/`:

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

The running app can also generate downloadable README, Kaggle Writeup, video script, and full report artifacts from the current repository state.

## Testing

The test suite covers the workflow, MCP-compatible tools, Gemini adapter behavior, security scanner, and submission package assets.

Run all tests:

```powershell
python -m unittest discover -s tests
```

Run the security scanner directly:

```powershell
python -m kaggle_capstone_coach.mcp_tools run check_security_signals --repo-root .
```

The primary code seam is:

```python
from kaggle_capstone_coach.workflow import run_readiness_workflow

report = run_readiness_workflow(requirement_text, repo_root)
markdown = report.to_markdown()
```

## Limitations

- The app evaluates this repository's submission readiness; it is not a general-purpose Kaggle platform integration.
- The MCP layer is local and MCP-compatible in shape, not a hosted remote server.
- Gemini-backed summaries are optional; deterministic output is the supported baseline.
- The security scanner is a lightweight committed-secret and environment-file check, not a full secret-detection or supply-chain security product.

## Status

The app is complete, deployed, and packaged for Kaggle review. The repository includes code, tests, deployment instructions, submission assets, a demo video, and a public Streamlit app.
