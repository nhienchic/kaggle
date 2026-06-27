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
            "## Agent Findings",
            "",
        ]

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

    model_mode = "model-backed" if env.get("GOOGLE_API_KEY") and model_adapter else "deterministic"

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
    if model_mode == "model-backed":
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
        "`GOOGLE_API_KEY`.\n\n"
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
        "model-backed adapter path is available when `GOOGLE_API_KEY` is configured.\n\n"
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
        "model-backed adapter gated by `GOOGLE_API_KEY`.\n"
        "5. MCP evidence: show the local MCP-compatible tools for requirement "
        "reading, repo scanning, checklist data, and security signals.\n"
        "6. Security evidence: show likely-secret scanning, risky env-file warnings, "
        "redacted findings, and safe read boundaries.\n"
        "7. Deployability evidence: show local run instructions and the planned public "
        "deployment path."
    )
