# Five-Minute Video Script

## 0:00 - 0:30 Problem

This project solves a submission-readiness problem for Kaggle AI Agents capstone participants. A good agent project can still lose judging clarity if the writeup, video, setup instructions, security posture, deployment story, or course concept evidence are missing.

## 0:30 - 1:00 Solution

Kaggle Capstone Submission Coach is a Streamlit app that reads the competition brief and scans the repository. It produces a structured readiness report with a score, checklist, judge evidence dashboard, security summary, prioritized next steps, and downloadable draft artifacts.

## 1:00 - 1:45 Multi-Agent Architecture

Show the four workflow roles: Requirement Analyst, Repo Auditor, Submission Strategist, and Communication Coach. Explain that the same report contract works in deterministic mode and in optional Gemini-backed mode when `GOOGLE_API_KEY` or `GEMINI_API_KEY` is configured.

## 1:45 - 2:30 MCP Evidence

Show the MCP-compatible local tools:

- `read_competition_requirements`
- `scan_repository_files`
- `produce_readiness_checklist`
- `check_security_signals`

Explain that these tools expose the same evidence-gathering capabilities used by the app.

## 2:30 - 3:15 Security Evidence

Open the security summary. Explain that the scanner checks likely committed secrets, risky environment files, and safe repository read boundaries. Point out that secret-like values are redacted and that real keys belong in local or deployment environment variables.

## 3:15 - 4:15 App Demo

Run:

```powershell
python -m streamlit run app.py
```

Show the readiness score, model mode, judge evidence dashboard, agent findings, submission checklist, and downloadable report artifacts. Emphasize how the dashboard maps pitch, implementation, documentation, multi-agent evidence, MCP evidence, security, deployability, and required assets.

Mention that the Kaggle media gallery uses `docs/submission/media-gallery/cover.png` as the cover image, then add screenshots of the score, evidence dashboard, MCP tools, security summary, and downloads.

## 4:15 - 5:00 Deployability

Explain the deployment path: publish this repository to GitHub, create a Streamlit Community Cloud app from `app.py`, add `GOOGLE_API_KEY` or `GEMINI_API_KEY` as an optional secret, and keep deterministic fallback available so the demo still runs without a live model call.
