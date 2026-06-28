from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Sequence

from kaggle_capstone_coach.gemini_adapter import GeminiModelAdapter
from kaggle_capstone_coach.workflow import (
    DashboardItem,
    ReadinessReport,
    run_readiness_workflow,
)


def _dashboard_rows(
    items: Sequence[DashboardItem],
    label_heading: str,
    include_score: bool = False,
) -> list[dict[str, str]]:
    rows = []
    for item in items:
        row = {
            label_heading: item.label,
            "Status": item.status,
            "Evidence": ", ".join(item.evidence) or "No evidence found",
            "Next step": item.next_step,
        }
        if include_score:
            row["Score"] = f"{item.score}/100"
        rows.append(row)
    return rows


def build_default_report(
    repo_root: Path | str | None = None,
    environment: Mapping[str, str] | None = None,
    model_adapter: object | None = None,
) -> ReadinessReport:
    root = Path(repo_root) if repo_root is not None else Path(__file__).parent
    env = os.environ if environment is None else environment
    adapter = model_adapter or _build_model_adapter(env)
    requirement_text = (root / "requirement.md").read_text(encoding="utf-8")
    return run_readiness_workflow(
        requirement_text,
        root,
        environment=env,
        model_adapter=adapter,
    )


def _build_model_adapter(environment: Mapping[str, str]) -> object | None:
    api_key = environment.get("GEMINI_API_KEY") or environment.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    return GeminiModelAdapter(api_key=api_key)


def main() -> None:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Streamlit is not installed. Run `python -m pip install -r requirements.txt`."
        ) from exc

    st.set_page_config(
        page_title="Kaggle Capstone Submission Coach",
        layout="wide",
    )

    report = build_default_report()

    st.title("Kaggle Capstone Submission Coach")
    st.caption("Submission readiness report for the current repository.")

    score_col, mode_col = st.columns([1, 2])
    score_col.metric("Readiness score", f"{report.readiness_score}/100")
    mode_col.metric("Model mode", report.model_mode)
    st.progress(report.readiness_score / 100)
    if report.model_error:
        st.warning(f"Model-backed analysis fell back to deterministic output: {report.model_error}")

    dashboard = report.scoring_dashboard()
    st.subheader("Judge evidence dashboard")
    tab_rubric, tab_concepts, tab_assets, tab_steps = st.tabs(
        ["Rubric", "Concept Evidence", "Submission Assets", "Next Steps"]
    )
    with tab_rubric:
        st.dataframe(
            _dashboard_rows(dashboard.rubric_readiness, "Category", include_score=True),
            use_container_width=True,
            hide_index=True,
        )
    with tab_concepts:
        st.dataframe(
            _dashboard_rows(dashboard.evidence_map, "Concept"),
            use_container_width=True,
            hide_index=True,
        )
    with tab_assets:
        st.dataframe(
            _dashboard_rows(dashboard.submission_assets, "Asset"),
            use_container_width=True,
            hide_index=True,
        )
    with tab_steps:
        for index, step in enumerate(dashboard.prioritized_next_steps, start=1):
            st.write(f"{index}. {step}")

    st.subheader("Agent findings")
    for agent in report.agent_summaries:
        with st.expander(agent.name, expanded=True):
            st.write(agent.responsibility)
            st.write(agent.finding)

    st.subheader("Submission checklist")
    st.dataframe(
        [
            {
                "Requirement": item.label,
                "Status": item.status,
                "Evidence": ", ".join(item.evidence) or "No evidence found",
                "Next step": item.next_step,
            }
            for item in report.checklist
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Security summary")
    st.metric("Security status", report.security_summary.status)
    if report.security_summary.findings:
        st.dataframe(
            [
                {
                    "Status": finding.status,
                    "Category": finding.category,
                    "Path": finding.path,
                    "Finding": finding.message,
                    "Remediation": finding.remediation,
                }
                for finding in report.security_summary.findings
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No likely committed secrets or risky environment files found.")

    artifacts = {artifact.label: artifact for artifact in report.artifacts()}
    tab_report, tab_readme, tab_writeup, tab_video = st.tabs(
        ["Report", "README Draft", "Writeup Draft", "Video Script"]
    )
    with tab_report:
        artifact = artifacts["Full readiness report"]
        st.markdown(artifact.content)
        st.download_button(
            "Download report",
            data=artifact.content,
            file_name=artifact.filename,
            mime="text/markdown",
        )
    with tab_readme:
        artifact = artifacts["README draft"]
        st.markdown(artifact.content)
        st.download_button(
            "Download README draft",
            data=artifact.content,
            file_name=artifact.filename,
            mime="text/markdown",
        )
    with tab_writeup:
        artifact = artifacts["Kaggle Writeup draft"]
        st.markdown(artifact.content)
        st.download_button(
            "Download Kaggle Writeup draft",
            data=artifact.content,
            file_name=artifact.filename,
            mime="text/markdown",
        )
    with tab_video:
        artifact = artifacts["Five-minute video script"]
        st.markdown(artifact.content)
        st.download_button(
            "Download video script",
            data=artifact.content,
            file_name=artifact.filename,
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
