# Coding Report: YouTube Demo Checklist

## Scope

Made the video submission package upload-ready:

- Added `docs/submission/youtube-demo-checklist.md` with YouTube title, description, recording setup, evidence beats, media-gallery cross-check, and upload/no-secrets checklist.
- Linked the checklist from `docs/submission/five-minute-video-script.md`.
- Added the checklist to the README submission package and updated the roadmap to focus on final recording and optional hosting.
- Extended `tests/test_submission_package.py` so the repository must document the YouTube metadata, five-minute limit, local run command, `GOOGLE_API_KEY`, media gallery, and public visibility expectations.

## Verification

Passed:

```powershell
python -m unittest tests.test_submission_package
python -m unittest discover -s tests
```

Smoke check:

```text
Streamlit HTTP status: 200
```
