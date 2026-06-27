# Coding Report: Issue 6 Gemini / Google ADK Runtime Fallback

## Scope

Added a runtime seam for deterministic fallback and model-backed execution:

- `run_readiness_workflow()` now accepts an optional `environment` mapping and `model_adapter`.
- Missing `GOOGLE_API_KEY` keeps deterministic fallback mode, even if an adapter is supplied.
- Present `GOOGLE_API_KEY` plus a model adapter switches the report to `model-backed` mode.
- The adapter receives the same structured workflow context used by deterministic execution.
- The app helper forwards runtime options so the UI can report the active mode through the existing `Model mode` metric.

No live model calls are made in tests. The model-backed path is verified with fake adapters.

## Verification

Passed:

```powershell
python -m unittest discover -s tests
```

Smoke checked deterministic fallback:

```powershell
python -c "from app import build_default_report; r = build_default_report(environment={}); print(r.model_mode)"
```

Smoke checked configured adapter mode:

```powershell
python -c "from app import build_default_report; A=type('A',(),{'build_agent_summaries':lambda self, context: context['deterministic_summaries']}); r=build_default_report(environment={'GOOGLE_API_KEY':'configured'}, model_adapter=A()); print(r.model_mode)"
```

## Notes

The repository does not contain API keys. `GOOGLE_API_KEY` is documented as a local or deployment environment variable only.
