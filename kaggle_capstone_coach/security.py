from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


SecurityStatus = str


@dataclass(frozen=True)
class SecurityFinding:
    status: SecurityStatus
    category: str
    path: str
    message: str
    remediation: str


@dataclass(frozen=True)
class SecuritySummary:
    status: SecurityStatus
    findings: tuple[SecurityFinding, ...]


def scan_repository_security(repo_root: Path | str) -> SecuritySummary:
    root = Path(repo_root).resolve()
    findings: list[SecurityFinding] = []

    for path in _iter_scannable_files(root):
        try:
            text = safe_read_text(root, path)
        except ValueError:
            # Runtime mounts such as Streamlit secrets can appear under the repo
            # while resolving outside it. Do not read or report their contents.
            continue
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(root).as_posix()
        findings.extend(_env_file_findings(relative))
        findings.extend(_secret_findings(relative, text))

    return SecuritySummary(status=_summary_status(tuple(findings)), findings=tuple(findings))


def safe_read_text(repo_root: Path | str, path: Path | str) -> str:
    root = Path(repo_root).resolve()
    candidate = Path(path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Refusing to read outside repository root: {candidate}")
    return candidate.read_text(encoding="utf-8")


def _summary_status(findings: tuple[SecurityFinding, ...]) -> SecurityStatus:
    if any(finding.status == "fail" for finding in findings):
        return "fail"
    if any(finding.status == "warn" for finding in findings):
        return "warn"
    return "pass"


def _iter_scannable_files(root: Path) -> tuple[Path, ...]:
    ignored_dirs = {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in ignored_dirs for part in relative.parts):
            continue
        if any(part == "human" or part.startswith("human_") for part in relative.parts):
            continue
        if path.stat().st_size > 500_000:
            continue
        files.append(path)
    return tuple(files)


def _secret_findings(relative_path: str, text: str) -> tuple[SecurityFinding, ...]:
    patterns = (
        re.compile(
            r"(?P<name>[A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)[A-Z0-9_]*)\s*[:=]\s*['\"]?(?P<value>[A-Za-z0-9_\-]{20,})",
            re.IGNORECASE,
        ),
    )
    findings: list[SecurityFinding] = []

    for pattern in patterns:
        for match in pattern.finditer(text):
            name = match.group("name")
            value = match.group("value")
            findings.append(
                SecurityFinding(
                    status="fail",
                    category="likely-secret",
                    path=relative_path,
                    message=f"{name} appears to contain a committed secret ({_redact(value)}).",
                    remediation="Move the value to an environment variable, rotate it if real, and remove it from git history before publishing.",
                )
            )

    return tuple(findings)


def _env_file_findings(relative_path: str) -> tuple[SecurityFinding, ...]:
    name = Path(relative_path).name.lower()
    if not name.startswith(".env"):
        return ()
    if name in {".env.example", ".env.sample", ".env.template"}:
        return ()

    return (
        SecurityFinding(
            status="warn",
            category="risky-env-file",
            path=relative_path,
            message=f"{relative_path} is a committed environment file.",
            remediation="Keep real environment files local, commit only example templates, and document required variables in README.",
        ),
    )


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}...{value[-3:]}"
