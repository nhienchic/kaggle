from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
class ReadinessReport:
    title: str
    model_mode: str
    readiness_score: int
    agent_summaries: tuple[AgentSummary, ...]
    checklist: tuple[ChecklistItem, ...]
    gaps: tuple[str, ...]
    next_steps: tuple[str, ...]
    readme_draft: str
    writeup_draft: str
    video_script: str

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


def run_readiness_workflow(requirement_text: str, repo_root: Path | str) -> ReadinessReport:
    snapshot = _scan_repository(Path(repo_root))
    checklist = _build_checklist(requirement_text, snapshot)
    score = _score(checklist)
    gaps = tuple(
        f"{item.label}: {item.next_step}"
        for item in checklist
        if item.status != "present"
    )
    next_steps = tuple(item.next_step for item in checklist if item.status != "present")[:5]

    agent_summaries = (
        AgentSummary(
            "Requirement Analyst",
            "Extract hard submission assets and judging criteria from the brief.",
            "Detected required assets: Kaggle Writeup, Media Gallery, YouTube video, public project link, and at least three course concepts.",
        ),
        AgentSummary(
            "Repo Auditor",
            "Scan the repository for judge-visible evidence.",
            f"Scanned {len(snapshot.files)} files and mapped current evidence to the submission checklist.",
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

    return ReadinessReport(
        title="Kaggle Capstone Submission Coach Readiness Report",
        model_mode="deterministic",
        readiness_score=score,
        agent_summaries=agent_summaries,
        checklist=checklist,
        gaps=gaps,
        next_steps=next_steps,
        readme_draft=_readme_draft(checklist),
        writeup_draft=_writeup_draft(),
        video_script=_video_script(),
    )


def _scan_repository(root: Path) -> RepoSnapshot:
    ignored_dirs = {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}
    files: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        parts = relative.parts
        if any(part in ignored_dirs for part in parts):
            continue
        if any(part == "human" or part.startswith("human_") for part in parts):
            continue
        files.append(relative.as_posix())

    return RepoSnapshot(root=root, files=tuple(sorted(files)))


def _build_checklist(requirement_text: str, snapshot: RepoSnapshot) -> tuple[ChecklistItem, ...]:
    brief_present = snapshot.has_file("requirement.md") or "Submission Requirements" in requirement_text
    app_present = snapshot.has_file("app.py")
    tests_present = any(file_name.startswith("tests/") for file_name in snapshot.files)
    package_present = any(
        file_name.startswith("kaggle_capstone_coach/") for file_name in snapshot.files
    )

    return (
        _item(
            "Competition brief",
            brief_present,
            ("requirement.md",) if brief_present else (),
            "Add the competition requirements brief to requirement.md.",
        ),
        _item(
            "Runnable Streamlit app",
            app_present,
            ("app.py",) if app_present else (),
            "Create a Streamlit entrypoint that renders the readiness report.",
        ),
        _item(
            "Deterministic readiness workflow",
            package_present,
            ("kaggle_capstone_coach/workflow.py",) if package_present else (),
            "Add a tested workflow that returns a structured report without live model calls.",
        ),
        _item(
            "Workflow tests",
            tests_present,
            ("tests/",) if tests_present else (),
            "Add tests for the readiness workflow that do not require API keys.",
        ),
        _item(
            "Kaggle Writeup",
            snapshot.has_any_path_containing("writeup"),
            _matching(snapshot, "writeup"),
            "Draft the Kaggle Writeup and attach it to the submission.",
        ),
        _item(
            "Media Gallery",
            _has_media(snapshot),
            _media_files(snapshot),
            "Create a cover image and media assets for the Kaggle Writeup gallery.",
        ),
        _item(
            "YouTube video",
            snapshot.has_any_path_containing("youtube")
            or snapshot.has_any_path_containing("video", "script"),
            _matching(snapshot, "youtube") + _matching(snapshot, "video"),
            "Record and publish a five-minute or shorter YouTube demo video.",
        ),
        _item(
            "Public project link",
            snapshot.has_file("README.md"),
            ("README.md",) if snapshot.has_file("README.md") else (),
            "Publish a public repo or demo link with setup instructions.",
        ),
        _item(
            "README setup instructions",
            snapshot.has_file("README.md"),
            ("README.md",) if snapshot.has_file("README.md") else (),
            "Add a README with problem, solution, architecture, and local setup steps.",
        ),
        _item(
            "Course concept evidence",
            package_present,
            ("kaggle_capstone_coach/workflow.py",) if package_present else (),
            "Map at least three course concepts to code or video evidence.",
        ),
    )


def _item(
    label: str,
    present: bool,
    evidence: tuple[str, ...],
    next_step: str,
) -> ChecklistItem:
    return ChecklistItem(
        label=label,
        status="present" if present else "missing",
        evidence=evidence,
        next_step=next_step,
    )


def _matching(snapshot: RepoSnapshot, term: str) -> tuple[str, ...]:
    return tuple(file_name for file_name in snapshot.files if term.lower() in file_name.lower())


def _has_media(snapshot: RepoSnapshot) -> bool:
    return bool(_media_files(snapshot))


def _media_files(snapshot: RepoSnapshot) -> tuple[str, ...]:
    extensions = {".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".webm"}
    return tuple(
        file_name
        for file_name in snapshot.files
        if Path(file_name).suffix.lower() in extensions
    )


def _score(checklist: tuple[ChecklistItem, ...]) -> int:
    if not checklist:
        return 0
    present = sum(1 for item in checklist if item.status == "present")
    return round((present / len(checklist)) * 100)


def _readme_draft(checklist: tuple[ChecklistItem, ...]) -> str:
    missing = ", ".join(item.label for item in checklist if item.status != "present")
    return (
        "Describe the Kaggle Capstone Submission Coach, its multi-agent readiness "
        "workflow, how to run the Streamlit app, and the current submission gaps. "
        f"Priority gaps to document: {missing or 'none'}."
    )


def _writeup_draft() -> str:
    return (
        "Title: Kaggle Capstone Submission Coach\n\n"
        "Problem: capstone participants need a fast way to see whether their project "
        "has the assets and course-concept evidence required for submission.\n\n"
        "Solution: a Streamlit app runs specialist agents over the competition brief "
        "and repository snapshot, then returns a readiness score, evidence map, gap "
        "analysis, and draft submission artifacts."
    )


def _video_script() -> str:
    return (
        "1. State the submission-readiness problem.\n"
        "2. Show the Streamlit report generated from requirement.md and the repo.\n"
        "3. Explain the four specialist agents and deterministic fallback mode.\n"
        "4. Walk through missing assets and prioritized next steps.\n"
        "5. Close with planned MCP, security, and deployability evidence."
    )
