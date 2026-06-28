# YouTube Demo Checklist

Use this checklist with `five-minute-video-script.md` when recording and uploading the final Kaggle video. Keep the finished video at 5 minutes or less.

Copy the youtube title and youtube description below into YouTube Studio, then replace placeholder links after the public project link and Kaggle Writeup are available.

## YouTube Title

Kaggle Capstone Submission Coach - AI Agent Readiness Dashboard

## YouTube Description

Kaggle Capstone Submission Coach is a Streamlit app that turns a Kaggle AI Agents capstone brief and repository evidence into a judge-facing readiness package. The demo shows the multi-agent workflow, MCP-compatible local tools, security checks, optional Gemini configuration through `GOOGLE_API_KEY` or `GEMINI_API_KEY`, media gallery assets, downloadable submission artifacts, and a Streamlit Community Cloud deployment path.

Suggested links to include after upload:

- Public project link: add the GitHub repository URL.
- Kaggle Writeup: add the final Kaggle Writeup URL after publishing.
- Demo assets: `docs/submission/media-gallery/`

## Recording Setup

1. Start from a clean shell with no real keys visible.
2. Run tests:

   ```powershell
   python -m unittest discover -s tests
   ```

3. Launch the app:

   ```powershell
   python -m streamlit run app.py
   ```

4. Open `http://localhost:8501`.
5. If showing model-backed mode, set `GOOGLE_API_KEY` or `GEMINI_API_KEY` only in the local shell or deployment secrets UI. Do not show the value on screen.

## Recording Beats

1. Problem: missing judge-visible evidence can weaken a strong capstone project.
2. Solution: Streamlit readiness dashboard over the current repository.
3. Multi-agent architecture: Requirement Analyst, Repo Auditor, Submission Strategist, Communication Coach.
4. MCP evidence: local tools for requirements, repo scan, checklist data, and security signals.
5. Security evidence: pass/warn/fail summary, secret redaction, and repository read boundary.
6. App demo: readiness score, model mode, judge evidence dashboard, checklist, and artifacts.
7. Deployability: README setup, Streamlit Community Cloud path, and deterministic fallback without secrets.

## Media Gallery Cross-Check

Attach these media gallery assets to the Kaggle Writeup before or alongside the YouTube video:

- `cover.png`
- `streamlit-readiness-overview.png`
- `judge-evidence-dashboard.png`
- `mcp-tools-output.png`
- `security-and-downloads.png`

## Upload Checklist

- The video is public or unlisted with a shareable YouTube URL.
- The video is 5 minutes or less.
- The video does not show API keys, passwords, tokens, `.env` contents, or private dashboard secrets.
- The description links to the public project repository.
- The description mentions Streamlit, multi-agent workflow, MCP, security, Gemini configuration, and deployability.
- The Kaggle Writeup attaches the YouTube video and the media gallery assets.
