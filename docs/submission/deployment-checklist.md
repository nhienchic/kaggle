# Deployment Checklist

This repository is ready to deploy as a Streamlit app. The safest default is deterministic mode, which requires no API key. Model-backed summaries are optional and should use deployment secrets only.

References:

- Streamlit Community Cloud deploy guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- Streamlit secrets management: https://docs.streamlit.io/develop/concepts/connections/secrets-management

## Local Preflight

1. Confirm tests pass:

   ```powershell
   python -m unittest discover -s tests
   ```

2. Confirm the app runs locally:

   ```powershell
   python -m streamlit run app.py
   ```

3. Open `http://localhost:8501`.
4. Confirm the report shows a readiness score, model mode, judge evidence dashboard, security summary, and downloadable artifacts.

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a new Streamlit Community Cloud app from the GitHub repository.
3. Set the app entrypoint to `app.py`.
4. Let Streamlit install Python dependencies from `requirements.txt`.
5. Leave secrets empty for deterministic fallback mode, or add secrets for model-backed mode.
6. After deploy, open the public app URL and confirm the app renders without exposing credentials.

## Secrets

Use `.streamlit/secrets.toml.example` as the shape for deployment secrets:

```toml
GOOGLE_API_KEY = "replace_me"
GEMINI_API_KEY = "replace_me"
```

Do not commit `.streamlit/secrets.toml`. The repository ignores that file.

The app accepts either `GOOGLE_API_KEY` or `GEMINI_API_KEY`. If both are configured, `GEMINI_API_KEY` is preferred by `app.py`.

## Public Submission Link

For the Kaggle submission, use one of these links:

- Preferred: the deployed Streamlit Community Cloud app URL.
- Fallback: the public GitHub repository URL, because the README documents setup, tests, local run, MCP tools, security posture, Gemini configuration, and deployability.

## Final Deploy Check

- The public app loads without login.
- The app does not show API key values.
- `requirements.txt` contains `streamlit` and `google-genai`.
- `.streamlit/config.toml` is committed.
- `.streamlit/secrets.toml` is not committed.
- `README.md` links to this deployment checklist.
