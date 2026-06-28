# Kaggle Capstone Submission Coach

## Subtitle

A Streamlit readiness agent that turns a Kaggle capstone brief and repository evidence into a judge-facing submission plan.

## Problem

Kaggle AI Agents capstone projects are judged on more than working code. A valid submission needs a strong project story, public project link, Kaggle Writeup, media gallery, YouTube demo, setup instructions, and visible evidence for course concepts. Near the deadline, the highest risk is not that the prototype fails, but that important judge-visible evidence is missing or scattered across files.

## Solution

Kaggle Capstone Submission Coach packages that review into a local Streamlit app. The app reads `requirement.md`, scans the repository, runs a readiness workflow, and returns a structured report with a checklist, scoring dashboard, security summary, prioritized gaps, and draft submission artifacts.

The default path is deterministic so a reviewer can run the app without an API key. When `GOOGLE_API_KEY` or `GEMINI_API_KEY` is configured, the same workflow can call the Gemini adapter for model-backed agent summaries while preserving deterministic fallback if the provider is unavailable.

## Multi-Agent Architecture

The workflow uses four specialist roles:

- Requirement Analyst extracts required submission assets and scoring concerns from the competition brief.
- Repo Auditor scans repository evidence through the local tool layer.
- Submission Strategist turns missing evidence into prioritized next steps.
- Communication Coach drafts judge-facing README, writeup, and video material.

The report explicitly shows whether it ran in deterministic, model-backed, or model-error fallback mode.

## Course Concept Evidence

- Multi-agent system: `kaggle_capstone_coach/workflow.py` coordinates specialist agent summaries and a shared report contract.
- MCP: `kaggle_capstone_coach/mcp_tools.py` exposes local MCP-compatible tools for reading requirements, scanning files, producing checklist data, and checking security signals.
- Security: `kaggle_capstone_coach/security.py` scans for likely committed secrets, risky environment files, and read-boundary violations while redacting secret-like values.
- Deployability: the app is a standard Streamlit application with `requirements.txt`, local setup commands, and a documented Streamlit Community Cloud deployment path.
- Gemini: `kaggle_capstone_coach/gemini_adapter.py` adds optional model-backed summaries when a key is configured outside the repository.

## Demo Story

The demo opens the Streamlit app, shows the readiness score, then walks through the judge evidence dashboard. The key moment is the dashboard that groups rubric readiness, course concept evidence, required assets, and next steps in one place. The demo then opens the MCP-compatible tool commands, shows the security summary, and downloads the generated report artifacts.

## Media Gallery

Use `docs/submission/media-gallery/cover.png` as the cover image. Add `streamlit-readiness-overview.png`, `judge-evidence-dashboard.png`, `mcp-tools-output.png`, and `security-and-downloads.png` to make the submission evidence visible at a glance.

## Current Status

The repository can serve as the public project link if a live deployment is not available. A fresh user can install dependencies, run tests, launch the app locally, and inspect the same readiness evidence a judge would need.
