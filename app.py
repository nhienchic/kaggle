from __future__ import annotations

from pathlib import Path
from typing import Mapping

from kaggle_capstone_coach.workflow import ReadinessReport, run_readiness_workflow


def build_default_report(
    repo_root: Path | str | None = None,
    environment: Mapping[str, str] | None = None,
    model_adapter: object | None = None,
) -> ReadinessReport:
    root = Path(repo_root) if repo_root is not None else Path(__file__).parent
    requirement_text = (root / "requirement.md").read_text(encoding="utf-8")
    return run_readiness_workflow(
        requirement_text,
        root,
        environment=environment,
        model_adapter=model_adapter,
    )


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
    st.caption("Deterministic submission readiness report for the current repository.")

    score_col, mode_col = st.columns([1, 2])
    score_col.metric("Readiness score", f"{report.readiness_score}/100")
    mode_col.metric("Model mode", report.model_mode)
    st.progress(report.readiness_score / 100)

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
