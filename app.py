from __future__ import annotations

from pathlib import Path

from kaggle_capstone_coach.workflow import ReadinessReport, run_readiness_workflow


def build_default_report(repo_root: Path | str | None = None) -> ReadinessReport:
    root = Path(repo_root) if repo_root is not None else Path(__file__).parent
    requirement_text = (root / "requirement.md").read_text(encoding="utf-8")
    return run_readiness_workflow(requirement_text, root)


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
    markdown = report.to_markdown()

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

    tab_report, tab_readme, tab_writeup, tab_video = st.tabs(
        ["Report", "README Draft", "Writeup Draft", "Video Script"]
    )
    with tab_report:
        st.markdown(markdown)
    with tab_readme:
        st.markdown(report.readme_draft)
    with tab_writeup:
        st.markdown(report.writeup_draft)
    with tab_video:
        st.markdown(report.video_script)

    st.download_button(
        "Download Markdown report",
        data=markdown,
        file_name="submission-readiness-report.md",
        mime="text/markdown",
    )


if __name__ == "__main__":
    main()
