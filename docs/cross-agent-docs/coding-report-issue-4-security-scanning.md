# Coding Report: Issue 4 Security Scanning

## Scope

Added visible security checks to the readiness workflow:

- Scans repository files for likely committed secrets.
- Flags risky committed environment files such as `.env`.
- Allows template files such as `.env.example`.
- Redacts matched values in findings instead of printing full secret values.
- Provides `safe_read_text(repo_root, path)` to reject reads outside the selected repository root.
- Includes security status, findings, and remediation guidance in the Markdown report and Streamlit UI.

## Public Interface

```python
from kaggle_capstone_coach.security import scan_repository_security, safe_read_text

summary = scan_repository_security(repo_root)
text = safe_read_text(repo_root, path)
```

The workflow exposes the result as:

```python
report.security_summary
```

## Verification

Passed:

```powershell
python -m unittest discover -s tests
```

Smoke checked:

```powershell
python -c "from app import build_default_report; r = build_default_report(); print(r.security_summary.status)"
```

The current repository reports `pass`, and the running Streamlit app responded with HTTP 200.
