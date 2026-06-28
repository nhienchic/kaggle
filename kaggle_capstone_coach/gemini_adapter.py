from __future__ import annotations

import json
from typing import Any


class GeminiModelAdapter:
    def __init__(
        self,
        api_key: str,
        client: object | None = None,
        model: str = "gemini-2.5-flash",
    ):
        self.model = model
        self._client = client if client is not None else self._build_client(api_key)

    def build_agent_summaries(self, context: dict[str, object]) -> list[dict[str, str]]:
        response = self._client.models.generate_content(  # type: ignore[attr-defined]
            model=self.model,
            contents=_build_prompt(context),
        )
        return _parse_agent_summaries(str(response.text))

    def _build_client(self, api_key: str) -> object:
        try:
            from google import genai
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "google-genai is not installed. Run `python -m pip install -r requirements.txt`."
            ) from exc
        return genai.Client(api_key=api_key)


def _build_prompt(context: dict[str, object]) -> str:
    context_payload = {
        "requirement_text": str(context.get("requirement_text", ""))[:6000],
        "repo_files": list(context.get("repo_files", ()))[:80],
        "checklist": [_serialize_item(item) for item in context.get("checklist", ())],
        "security_summary": _serialize_security_summary(context.get("security_summary")),
    }
    return (
        "You are the model-backed runtime for Kaggle Capstone Submission Coach.\n"
        "Return strict JSON only. Do not include markdown fences.\n"
        "Return exactly this shape:\n"
        '{"agent_summaries":[{"name":"Requirement Analyst","responsibility":"...",'
        '"finding":"..."},{"name":"Repo Auditor","responsibility":"...","finding":"..."},'
        '{"name":"Submission Strategist","responsibility":"...","finding":"..."},'
        '{"name":"Communication Coach","responsibility":"...","finding":"..."}]}\n'
        "Base findings on this repository context:\n"
        f"{json.dumps(context_payload, indent=2)}"
    )


def _parse_agent_summaries(text: str) -> list[dict[str, str]]:
    payload = json.loads(_strip_json_fence(text))
    summaries = payload["agent_summaries"] if isinstance(payload, dict) else payload
    if len(summaries) != 4:
        raise ValueError("Gemini response must contain exactly four agent summaries.")

    return [
        {
            "name": str(summary["name"]),
            "responsibility": str(summary["responsibility"]),
            "finding": str(summary["finding"]),
        }
        for summary in summaries
    ]


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def _serialize_item(item: object) -> dict[str, Any]:
    return {
        "label": str(getattr(item, "label", "")),
        "status": str(getattr(item, "status", "")),
        "evidence": list(getattr(item, "evidence", ())),
        "next_step": str(getattr(item, "next_step", "")),
    }


def _serialize_security_summary(summary: object) -> dict[str, Any]:
    if summary is None:
        return {"status": "unknown", "findings": []}
    return {
        "status": str(getattr(summary, "status", "unknown")),
        "findings": [
            {
                "status": str(getattr(finding, "status", "")),
                "category": str(getattr(finding, "category", "")),
                "path": str(getattr(finding, "path", "")),
                "message": str(getattr(finding, "message", "")),
                "remediation": str(getattr(finding, "remediation", "")),
            }
            for finding in getattr(summary, "findings", ())
        ],
    }
