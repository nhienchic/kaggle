from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping

from .mcp_tools import LocalMcpToolLayer
from .security import SecurityFinding, SecuritySummary


Status = str


@dataclass(frozen=True)
class ChecklistItem:
    label: str
    status: Status
    evidence: tuple[str, ...]
    next_step: str


@dataclass(frozen=True)
class AgentSummary:
    name: str
    responsibility: str
    finding: str


@dataclass(frozen=True)
class ReadinessArtifact:
    label: str
    filename: str
    content: str


@dataclass(frozen=True)
class DashboardItem:
    label: str
    status: Status
    evidence: tuple[str, ...]
    next_step: str
    score: int | None = None


@dataclass(frozen=True)
class ScoringDashboard:
    rubric_readiness: tuple[DashboardItem, ...]
    evidence_map: tuple[DashboardItem, ...]
    submission_assets: tuple[DashboardItem, ...]
    prioritized_next_steps: tuple[str, ...]


@dataclass(frozen=True)
class ReadinessReport:
    title: str
    model_mode: str
    readiness_score: int
    agent_summaries: tuple[AgentSummary, ...]
    checklist: tuple[ChecklistItem, ...]
    security_summary: SecuritySummary
    gaps: tuple[str, ...]
    next_steps: tuple[str, ...]
    readme_draft: str
    writeup_draft: str
    video_script: str
    model_error: str | None = None
    repo_files: tuple[str, ...] = ()

    def artifacts(self) -> tuple[ReadinessArtifact, ...]:
        return (
            ReadinessArtifact("README draft", "readme-draft.md", self.readme_draft),
            ReadinessArtifact(
                "Kaggle Writeup draft",
                "kaggle-writeup-draft.md",
                self.writeup_draft,
            ),
            ReadinessArtifact(
                "Five-minute video script",
                "five-minute-video-script.md",
                self.video_script,
            ),
            ReadinessArtifact(
                "Full readiness report",
                "submission-readiness-report.md",
                self.to_markdown(),
            ),
        )

    def scoring_dashboard(self) -> ScoringDashboard:
        submission_assets = _submission_asset_dashboard_items(self)
        evidence_map = _evidence_map_dashboard_items(self)
        rubric_readiness = _rubric_readiness_dashboard_items(
            self,
            submission_assets,
            evidence_map,
        )
        return ScoringDashboard(
            rubric_readiness=rubric_readiness,
            evidence_map=evidence_map,
            submission_assets=submission_assets,
            prioritized_next_steps=_judge_visible_next_steps(
                self,
                submission_assets,
                evidence_map,
                rubric_readiness,
            ),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"Model mode: {self.model_mode}",
            "",
            "## Readiness Score",
            "",
            f"{self.readiness_score}/100",
            "",
        ]
        if self.model_error:
            lines.extend(["## Model Error", "", self.model_error, ""])
        lines.extend(["## Agent Findings", ""])

        for agent in self.agent_summaries:
            lines.extend(
                [
                    f"### {agent.name}",
                    "",
                    f"Responsibility: {agent.responsibility}",
                    "",
                    agent.finding,
                    "",
                ]
            )

        lines.extend(["## Submission Checklist", ""])
        for item in self.checklist:
            evidence = "; ".join(item.evidence) if item.evidence else "No evidence found"
            lines.append(f"- **{item.label}**: {item.status} - {evidence}")

        lines.extend(["", "## Security Summary", ""])
        lines.append(f"Status: {self.security_summary.status}")
        if self.security_summary.findings:
            for finding in self.security_summary.findings:
                lines.append(
                    f"- **{finding.category}** ({finding.status}) in "
                    f"`{finding.path}`: {finding.message} "
                    f"Remediation: {finding.remediation}"
                )
        else:
            lines.append("- No likely committed secrets or risky environment files found.")

        lines.extend(["", "## Gaps", ""])
        for gap in self.gaps:
            lines.append(f"- {gap}")

        lines.extend(["", "## Prioritized Next Steps", ""])
        for index, step in enumerate(self.next_steps, start=1):
            lines.append(f"{index}. {step}")

        lines.extend(
            [
                "",
                "## README Draft",
                "",
                self.readme_draft,
                "",
                "## Kaggle Writeup Draft",
                "",
                self.writeup_draft,
                "",
                "## Five-Minute Video Script",
                "",
                self.video_script,
                "",
            ]
        )
        return "\n".join(lines)


@dataclass(frozen=True)
class RepoSnapshot:
    root: Path
    files: tuple[str, ...]

    def has_file(self, *names: str) -> bool:
        wanted = {name.lower() for name in names}
        return any(Path(file_name).name.lower() in wanted for file_name in self.files)

    def has_any_path_containing(self, *terms: str) -> bool:
        lowered = tuple(term.lower() for term in terms)
        return any(
            all(term in file_name.lower() for term in lowered)
            for file_name in self.files
        )


def run_readiness_workflow(
    requirement_text: str,
    repo_root: Path | str,
    environment: Mapping[str, str] | None = None,
    model_adapter: object | None = None,
) -> ReadinessReport:
    root = Path(repo_root)
    env = os.environ if environment is None else environment
    tools = LocalMcpToolLayer(root)
    snapshot = _snapshot_from_tool_output(
        root,
        tools.run_tool("scan_repository_files")["output"],
    )
    checklist = _checklist_from_tool_output(
        tools.run_tool(
            "produce_readiness_checklist",
            {"requirement_text": requirement_text},
        )["output"],
    )
    security_summary = _security_summary_from_tool_output(
        tools.run_tool("check_security_signals")["output"],
    )
    score = _score(checklist)
    gaps = tuple(
        f"{item.label}: {item.next_step}"
        for item in checklist
        if item.status != "present"
    )
    next_steps = tuple(item.next_step for item in checklist if item.status != "present")[:5]

    api_key_configured = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")
    model_mode = "model-backed" if api_key_configured and model_adapter else "deterministic"

    deterministic_summaries = (
        AgentSummary(
            "Requirement Analyst",
            "Extract hard submission assets and judging criteria from the brief.",
            "Detected required assets: Kaggle Writeup, Media Gallery, YouTube video, public project link, and at least three course concepts.",
        ),
        AgentSummary(
            "Repo Auditor",
            "Scan the repository for judge-visible evidence.",
            f"Scanned {len(snapshot.files)} files through the local MCP-compatible tool layer and mapped current evidence to the submission checklist. Security status: {security_summary.status}.",
        ),
        AgentSummary(
            "Submission Strategist",
            "Turn missing evidence into a prioritized build plan.",
            f"Current readiness is {score}/100; missing submission assets should be handled before optional integrations.",
        ),
        AgentSummary(
            "Communication Coach",
            "Draft public-facing submission material.",
            "Prepared README, Kaggle Writeup, and five-minute video script drafts from deterministic fallback content.",
        ),
    )
    agent_summaries = deterministic_summaries
    model_error = None
    if model_mode == "model-backed":
        try:
            agent_summaries = _agent_summaries_from_adapter(
                model_adapter,
                {
                    "requirement_text": requirement_text,
                    "repo_files": snapshot.files,
                    "checklist": checklist,
                    "security_summary": security_summary,
                    "deterministic_summaries": deterministic_summaries,
                },
            )
        except Exception as exc:
            model_mode = "model-error-fallback"
            model_error = str(exc)

    return ReadinessReport(
        title="Kaggle Capstone Submission Coach Readiness Report",
        model_mode=model_mode,
        readiness_score=score,
        agent_summaries=agent_summaries,
        checklist=checklist,
        security_summary=security_summary,
        gaps=gaps,
        next_steps=next_steps,
        readme_draft=_readme_draft(checklist),
        writeup_draft=_writeup_draft(),
        video_script=_video_script(),
        model_error=model_error,
        repo_files=snapshot.files,
    )


def _agent_summaries_from_adapter(
    model_adapter: object | None,
    context: dict[str, object],
) -> tuple[AgentSummary, ...]:
    if model_adapter is None or not hasattr(model_adapter, "build_agent_summaries"):
        raise ValueError("Model-backed mode requires an adapter with build_agent_summaries().")

    raw_summaries = model_adapter.build_agent_summaries(context)  # type: ignore[attr-defined]
    return tuple(
        summary
        if isinstance(summary, AgentSummary)
        else AgentSummary(
            name=str(summary["name"]),
            responsibility=str(summary["responsibility"]),
            finding=str(summary["finding"]),
        )
        for summary in raw_summaries
    )


def _snapshot_from_tool_output(root: Path, output: dict[str, object]) -> RepoSnapshot:
    return RepoSnapshot(root=root, files=tuple(output["files"]))  # type: ignore[arg-type]


def _checklist_from_tool_output(output: dict[str, object]) -> tuple[ChecklistItem, ...]:
    checklist = output["checklist"]
    return tuple(
        ChecklistItem(
            label=str(item["label"]),
            status=str(item["status"]),
            evidence=tuple(item["evidence"]),
            next_step=str(item["next_step"]),
        )
        for item in checklist  # type: ignore[union-attr]
    )


def _security_summary_from_tool_output(output: dict[str, object]) -> SecuritySummary:
    findings = tuple(
        SecurityFinding(
            status=str(finding["status"]),
            category=str(finding["category"]),
            path=str(finding["path"]),
            message=str(finding["message"]),
            remediation=str(finding["remediation"]),
        )
        for finding in output["findings"]  # type: ignore[union-attr]
    )
    return SecuritySummary(status=str(output["status"]), findings=findings)


def _score(checklist: tuple[ChecklistItem, ...]) -> int:
    if not checklist:
        return 0
    present = sum(1 for item in checklist if item.status == "present")
    return round((present / len(checklist)) * 100)


def _submission_asset_dashboard_items(report: ReadinessReport) -> tuple[DashboardItem, ...]:
    return (
        _asset_dashboard_item(
            report,
            "Kaggle Writeup",
            ("Generated Kaggle Writeup draft",) if report.writeup_draft else (),
            "Refine and publish the generated Kaggle Writeup draft in Kaggle.",
        ),
        _asset_dashboard_item(
            report,
            "Media Gallery",
            (),
            "Create a cover image and media assets for the Kaggle Writeup gallery.",
        ),
        _asset_dashboard_item(
            report,
            "YouTube video",
            ("Generated five-minute video script",) if report.video_script else (),
            "Record and publish the five-minute demo video, then attach it to the Writeup.",
        ),
        _asset_dashboard_item(
            report,
            "Public project link",
            ("Generated README draft for publishing setup instructions",)
            if report.readme_draft
            else (),
            "Publish a public repo or demo link with setup instructions.",
        ),
        _asset_dashboard_item(
            report,
            "README setup instructions",
            ("Generated README draft",) if report.readme_draft else (),
            "Move the generated README draft into the public README with setup steps.",
        ),
    )


def _asset_dashboard_item(
    report: ReadinessReport,
    label: str,
    partial_evidence: tuple[str, ...],
    partial_next_step: str,
) -> DashboardItem:
    checklist_item = _checklist_item(report, label)
    if checklist_item and checklist_item.status == "present":
        return DashboardItem(
            label=label,
            status="present",
            evidence=checklist_item.evidence,
            next_step=f"Keep {label} evidence visible in the final submission.",
        )

    evidence = partial_evidence
    status = "partial" if evidence else "missing"
    return DashboardItem(
        label=label,
        status=status,
        evidence=evidence,
        next_step=partial_next_step
        if status == "partial"
        else _checklist_next_step(checklist_item, partial_next_step),
    )


def _evidence_map_dashboard_items(report: ReadinessReport) -> tuple[DashboardItem, ...]:
    agent_evidence = _agent_role_evidence(report)
    workflow_evidence = _repo_matches(report.repo_files, "kaggle_capstone_coach/workflow.py")
    mcp_evidence = _repo_matches(report.repo_files, "kaggle_capstone_coach/mcp_tools.py")
    security_evidence = _repo_matches(report.repo_files, "kaggle_capstone_coach/security.py")
    deployment_evidence = _deployment_evidence(report.repo_files)
    local_run_evidence = _local_run_evidence(report.repo_files)

    return (
        DashboardItem(
            label="Multi-agent / ADK",
            status="present" if workflow_evidence and agent_evidence else "partial",
            evidence=workflow_evidence + agent_evidence,
            next_step="Show the multi-agent architecture in code, writeup, and video.",
        ),
        DashboardItem(
            label="MCP",
            status="present" if mcp_evidence else "partial",
            evidence=mcp_evidence
            or ("Generated submission drafts describe the MCP-compatible tool layer.",),
            next_step="Surface the MCP tool layer in code, writeup, and video.",
        ),
        _security_dashboard_item(report, security_evidence),
        DashboardItem(
            label="Deployability",
            status="present" if deployment_evidence else "partial",
            evidence=deployment_evidence
            or local_run_evidence
            or ("Generated submission drafts include deployability notes.",),
            next_step=(
                "Keep deployment evidence visible in the final submission."
                if deployment_evidence
                else "Document the public deployment path or demo fallback before submission."
            ),
        ),
    )


def _security_dashboard_item(
    report: ReadinessReport,
    security_evidence: tuple[str, ...],
) -> DashboardItem:
    if report.security_summary.status == "fail":
        finding_evidence = tuple(
            f"{finding.category} in {finding.path}"
            for finding in report.security_summary.findings
        )
        return DashboardItem(
            label="Security features",
            status="partial" if security_evidence else "missing",
            evidence=security_evidence + finding_evidence,
            next_step="Fix security findings before publishing judge-visible code.",
        )

    return DashboardItem(
        label="Security features",
        status="present" if security_evidence else "partial",
        evidence=security_evidence
        or (f"Security scan completed with status {report.security_summary.status}.",),
        next_step="Keep security evidence and clean scan status visible in the submission.",
    )


def _rubric_readiness_dashboard_items(
    report: ReadinessReport,
    submission_assets: tuple[DashboardItem, ...],
    evidence_map: tuple[DashboardItem, ...],
) -> tuple[DashboardItem, ...]:
    assets = {item.label: item for item in submission_assets}
    concepts = {item.label: item for item in evidence_map}
    return (
        _rubric_dashboard_item(
            "Pitch",
            (
                _checklist_dashboard_item(report, "Competition brief"),
                assets["Kaggle Writeup"],
                assets["YouTube video"],
                concepts["Multi-agent / ADK"],
            ),
        ),
        _rubric_dashboard_item(
            "Implementation",
            (
                _checklist_dashboard_item(report, "Runnable Streamlit app"),
                _checklist_dashboard_item(report, "Deterministic readiness workflow"),
                _checklist_dashboard_item(report, "Workflow tests"),
                _checklist_dashboard_item(report, "Course concept evidence"),
                concepts["MCP"],
                concepts["Security features"],
            ),
        ),
        _rubric_dashboard_item(
            "Documentation",
            (
                assets["README setup instructions"],
                assets["Public project link"],
                assets["Kaggle Writeup"],
                assets["Media Gallery"],
                concepts["Deployability"],
            ),
        ),
    )


def _rubric_dashboard_item(label: str, items: tuple[DashboardItem, ...]) -> DashboardItem:
    score = _status_score(items)
    return DashboardItem(
        label=label,
        status=_dashboard_status_from_score(score),
        score=score,
        evidence=tuple(f"{item.label}: {item.status}" for item in items),
        next_step=next(
            (item.next_step for item in items if item.status != "present"),
            f"Keep {label.lower()} evidence visible in the final submission.",
        ),
    )


def _checklist_dashboard_item(report: ReadinessReport, label: str) -> DashboardItem:
    item = _checklist_item(report, label)
    if item is None:
        return DashboardItem(
            label=label,
            status="missing",
            evidence=(),
            next_step=f"Add judge-visible evidence for {label}.",
        )
    return DashboardItem(
        label=label,
        status=item.status,
        evidence=item.evidence,
        next_step=item.next_step,
    )


def _judge_visible_next_steps(
    report: ReadinessReport,
    submission_assets: tuple[DashboardItem, ...],
    evidence_map: tuple[DashboardItem, ...],
    rubric_readiness: tuple[DashboardItem, ...],
) -> tuple[str, ...]:
    ordered_steps = [
        item.next_step
        for item in submission_assets + evidence_map + rubric_readiness
        if item.status != "present"
    ]
    ordered_steps.extend(report.next_steps)
    deduped = tuple(dict.fromkeys(step for step in ordered_steps if step))
    return deduped[:5] or ("Keep the current judge-facing evidence visible.",)


def _status_score(items: tuple[DashboardItem, ...]) -> int:
    if not items:
        return 0
    points = {"present": 1.0, "partial": 0.5, "missing": 0.0}
    return round(sum(points.get(item.status, 0.0) for item in items) / len(items) * 100)


def _dashboard_status_from_score(score: int) -> Status:
    if score == 100:
        return "present"
    if score > 0:
        return "partial"
    return "missing"


def _checklist_item(report: ReadinessReport, label: str) -> ChecklistItem | None:
    return next((item for item in report.checklist if item.label == label), None)


def _checklist_next_step(item: ChecklistItem | None, fallback: str) -> str:
    return item.next_step if item else fallback


def _agent_role_evidence(report: ReadinessReport) -> tuple[str, ...]:
    if not report.agent_summaries:
        return ()
    names = ", ".join(agent.name for agent in report.agent_summaries)
    return (f"{len(report.agent_summaries)} agent roles: {names}",)


def _repo_matches(files: tuple[str, ...], *names: str) -> tuple[str, ...]:
    wanted = {name.lower() for name in names}
    return tuple(file_name for file_name in files if file_name.lower() in wanted)


def _deployment_evidence(files: tuple[str, ...]) -> tuple[str, ...]:
    deployment_names = {"dockerfile", "procfile", "render.yaml"}
    return tuple(
        file_name
        for file_name in files
        if Path(file_name).name.lower() in deployment_names
        or "deploy" in file_name.lower()
    )


def _local_run_evidence(files: tuple[str, ...]) -> tuple[str, ...]:
    local_names = {"README.md", "requirements.txt", "app.py"}
    return tuple(file_name for file_name in files if Path(file_name).name in local_names)


def _readme_draft(checklist: tuple[ChecklistItem, ...]) -> str:
    missing = ", ".join(item.label for item in checklist if item.status != "present")
    return (
        "# Kaggle Capstone Submission Coach\n\n"
        "## Problem\n\n"
        "Capstone participants need a submission readiness check that turns the "
        "Kaggle competition brief and repository evidence into a clear build plan.\n\n"
        "## Solution\n\n"
        "A Streamlit app runs a deterministic multi-agent readiness workflow over "
        "the competition brief and current repository.\n\n"
        "## Architecture\n\n"
        "The workflow uses four specialist agents: Requirement Analyst, Repo Auditor, "
        "Submission Strategist, and Communication Coach. It preserves the same report "
        "contract for deterministic fallback and model-backed execution gated by "
        "`GEMINI_API_KEY` or `GOOGLE_API_KEY`.\n\n"
        "## MCP Evidence\n\n"
        "The project includes a local MCP-compatible tool layer for reading the "
        "competition brief, scanning repository files, producing checklist data, "
        "and checking security signals.\n\n"
        "## Security Evidence\n\n"
        "The workflow scans repository files for likely committed secrets, risky "
        "environment files, and guarded read-boundary behavior without exposing full "
        "secret values.\n\n"
        "## Deployability Evidence\n\n"
        "Placeholder: document local setup and the selected public deployment path.\n\n"
        "## Current Gaps\n\n"
        f"{missing or 'No required gaps detected by the deterministic workflow.'}"
    )


def _writeup_draft() -> str:
    return (
        "# Kaggle Capstone Submission Coach\n\n"
        "## Problem\n\n"
        "Kaggle AI Agents capstone submissions need strong communication, working "
        "code, and visible evidence for course concepts. Missing assets can weaken "
        "an otherwise useful project.\n\n"
        "## Solution\n\n"
        "This project uses a multi-agent readiness workflow to inspect the brief and "
        "repository, then produce a checklist, evidence map, prioritized next steps, "
        "and submission artifact drafts. The default path is deterministic, while a "
        "Gemini-backed adapter path is available when `GEMINI_API_KEY` or "
        "`GOOGLE_API_KEY` is configured.\n\n"
        "## Agent Architecture\n\n"
        "Requirement Analyst extracts the submission rules, Repo Auditor maps project "
        "evidence, Submission Strategist prioritizes gaps, and Communication Coach "
        "drafts judge-facing material. The orchestrator reports whether it used "
        "deterministic fallback or model-backed execution.\n\n"
        "## Course Concept Evidence\n\n"
        "- Multi-agent system: implemented by the deterministic readiness workflow.\n"
        "- MCP: local MCP-compatible tools expose requirement reading, repository scanning, checklist data, and security signals.\n"
        "- Security: likely-secret checks, risky env-file warnings, and safe read boundaries.\n"
        "- Deployability: placeholder for local setup and public hosting notes."
    )


def _video_script() -> str:
    return (
        "# Five-Minute Video Script\n\n"
        "1. Problem: explain why capstone submission readiness is difficult and why "
        "the Kaggle brief requires more than a prototype.\n"
        "2. Demo: show the Streamlit report generated from `requirement.md` and the "
        "current repository.\n"
        "3. Multi-agent architecture: explain the Requirement Analyst, Repo Auditor, "
        "Submission Strategist, and Communication Coach.\n"
        "4. Runtime mode: show whether the app used deterministic fallback or the "
        "Gemini-backed adapter gated by `GEMINI_API_KEY` or `GOOGLE_API_KEY`.\n"
        "5. MCP evidence: show the local MCP-compatible tools for requirement "
        "reading, repo scanning, checklist data, and security signals.\n"
        "6. Security evidence: show likely-secret scanning, risky env-file warnings, "
        "redacted findings, and safe read boundaries.\n"
        "7. Deployability evidence: show local run instructions and the planned public "
        "deployment path."
    )
