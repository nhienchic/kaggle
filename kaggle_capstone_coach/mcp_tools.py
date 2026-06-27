from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .security import safe_read_text, scan_repository_security


class LocalMcpToolLayer:
    """MCP-compatible local tools with JSON-serializable inputs and outputs."""

    def __init__(self, repo_root: Path | str):
        self.repo_root = Path(repo_root).resolve()

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "read_competition_requirements",
                "description": "Read the local Kaggle competition brief from requirement.md.",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "scan_repository_files",
                "description": "List visible repository files used as submission evidence.",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "produce_readiness_checklist",
                "description": "Produce submission checklist data from requirements and repository evidence.",
                "input_schema": {
                    "type": "object",
                    "properties": {"requirement_text": {"type": "string"}},
                },
            },
            {
                "name": "check_security_signals",
                "description": "Scan for likely secrets, risky env files, and security remediation signals.",
                "input_schema": {"type": "object", "properties": {}},
            },
        ]

    def run_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if name == "read_competition_requirements":
            return self._tool_result(name, self._read_competition_requirements())
        if name == "scan_repository_files":
            return self._tool_result(name, self._scan_repository_files())
        if name == "produce_readiness_checklist":
            return self._tool_result(
                name,
                self._produce_readiness_checklist(str(arguments.get("requirement_text", ""))),
            )
        if name == "check_security_signals":
            return self._tool_result(name, self._check_security_signals())
        return {
            "tool": name,
            "status": "error",
            "output": {"message": f"Unknown tool: {name}"},
        }

    def _read_competition_requirements(self) -> dict[str, Any]:
        path = self.repo_root / "requirement.md"
        text = safe_read_text(self.repo_root, path)
        return {
            "path": "requirement.md",
            "text": text,
            "character_count": len(text),
        }

    def _scan_repository_files(self) -> dict[str, Any]:
        ignored_dirs = {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}
        files: list[str] = []
        for path in self.repo_root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.repo_root)
            if any(part in ignored_dirs for part in relative.parts):
                continue
            if any(part == "human" or part.startswith("human_") for part in relative.parts):
                continue
            files.append(relative.as_posix())

        return {
            "file_count": len(files),
            "files": sorted(files),
        }

    def _produce_readiness_checklist(self, requirement_text: str) -> dict[str, Any]:
        files = self._scan_repository_files()["files"]
        checklist = _build_checklist(requirement_text, files)
        return {"checklist": checklist}

    def _check_security_signals(self) -> dict[str, Any]:
        summary = scan_repository_security(self.repo_root)
        return {
            "status": summary.status,
            "findings": [
                {
                    "status": finding.status,
                    "category": finding.category,
                    "path": finding.path,
                    "message": finding.message,
                    "remediation": finding.remediation,
                }
                for finding in summary.findings
            ],
        }

    def _tool_result(self, name: str, output: dict[str, Any]) -> dict[str, Any]:
        return {
            "tool": name,
            "status": "ok",
            "output": output,
        }


def _build_checklist(requirement_text: str, files: list[str]) -> list[dict[str, Any]]:
    file_names = {Path(file_name).name.lower() for file_name in files}
    package_present = any(file_name.startswith("kaggle_capstone_coach/") for file_name in files)
    brief_present = "requirement.md" in file_names or "Submission Requirements" in requirement_text
    tests_present = any(file_name.startswith("tests/") for file_name in files)

    return [
        _item(
            "Competition brief",
            brief_present,
            ["requirement.md"] if brief_present else [],
            "Add the competition requirements brief to requirement.md.",
        ),
        _item(
            "Runnable Streamlit app",
            "app.py" in file_names,
            ["app.py"] if "app.py" in file_names else [],
            "Create a Streamlit entrypoint that renders the readiness report.",
        ),
        _item(
            "Deterministic readiness workflow",
            package_present,
            ["kaggle_capstone_coach/workflow.py"] if package_present else [],
            "Add a tested workflow that returns a structured report without live model calls.",
        ),
        _item(
            "Workflow tests",
            tests_present,
            ["tests/"] if tests_present else [],
            "Add tests for the readiness workflow that do not require API keys.",
        ),
        _item(
            "Kaggle Writeup",
            _has_path_containing(files, "writeup"),
            _matching(files, "writeup"),
            "Draft the Kaggle Writeup and attach it to the submission.",
        ),
        _item(
            "Media Gallery",
            bool(_media_files(files)),
            _media_files(files),
            "Create a cover image and media assets for the Kaggle Writeup gallery.",
        ),
        _item(
            "YouTube video",
            _has_path_containing(files, "youtube") or _has_path_containing(files, "video", "script"),
            _matching(files, "youtube") + _matching(files, "video"),
            "Record and publish a five-minute or shorter YouTube demo video.",
        ),
        _item(
            "Public project link",
            "readme.md" in file_names,
            ["README.md"] if "readme.md" in file_names else [],
            "Publish a public repo or demo link with setup instructions.",
        ),
        _item(
            "README setup instructions",
            "readme.md" in file_names,
            ["README.md"] if "readme.md" in file_names else [],
            "Add a README with problem, solution, architecture, and local setup steps.",
        ),
        _item(
            "Course concept evidence",
            package_present,
            ["kaggle_capstone_coach/workflow.py"] if package_present else [],
            "Map at least three course concepts to code or video evidence.",
        ),
    ]


def _item(label: str, present: bool, evidence: list[str], next_step: str) -> dict[str, Any]:
    return {
        "label": label,
        "status": "present" if present else "missing",
        "evidence": evidence,
        "next_step": next_step,
    }


def _has_path_containing(files: list[str], *terms: str) -> bool:
    lowered = tuple(term.lower() for term in terms)
    return any(all(term in file_name.lower() for term in lowered) for file_name in files)


def _matching(files: list[str], term: str) -> list[str]:
    return [file_name for file_name in files if term.lower() in file_name.lower()]


def _media_files(files: list[str]) -> list[str]:
    extensions = {".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".webm"}
    return [
        file_name
        for file_name in files
        if Path(file_name).suffix.lower() in extensions
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect local MCP-compatible tools.")
    parser.add_argument("command", choices=("list", "run"))
    parser.add_argument("tool", nargs="?")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--arguments-json", default="{}")
    parser.add_argument("--requirement-text")
    args = parser.parse_args(argv)

    tools = LocalMcpToolLayer(args.repo_root)
    if args.command == "list":
        print(json.dumps({"tools": tools.list_tools()}, indent=2))
        return 0

    if not args.tool:
        parser.error("run requires a tool name")
    arguments = json.loads(args.arguments_json)
    if args.requirement_text is not None:
        arguments["requirement_text"] = args.requirement_text
    print(json.dumps(tools.run_tool(args.tool, arguments), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
