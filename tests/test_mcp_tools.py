from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from kaggle_capstone_coach.mcp_tools import LocalMcpToolLayer


class LocalMcpToolLayerTests(unittest.TestCase):
    def test_tool_layer_lists_available_mcp_compatible_tools(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tools = LocalMcpToolLayer(Path(tmp_dir))

            names = {tool["name"] for tool in tools.list_tools()}

        self.assertEqual(
            names,
            {
                "read_competition_requirements",
                "scan_repository_files",
                "produce_readiness_checklist",
                "check_security_signals",
            },
        )

    def test_read_competition_requirements_tool_returns_requirement_text(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "requirement.md").write_text(
                "# Submission Requirements\n\nKaggle Writeup required.",
                encoding="utf-8",
            )

            result = LocalMcpToolLayer(repo_root).run_tool("read_competition_requirements")

        self.assertEqual(result["tool"], "read_competition_requirements")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["output"]["path"], "requirement.md")
        self.assertIn("Submission Requirements", result["output"]["text"])

    def test_scan_repository_files_tool_returns_visible_project_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "README.md").write_text("readme", encoding="utf-8")
            (repo_root / "__pycache__").mkdir()
            (repo_root / "__pycache__" / "ignored.pyc").write_bytes(b"cache")

            result = LocalMcpToolLayer(repo_root).run_tool("scan_repository_files")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["output"]["file_count"], 1)
        self.assertEqual(result["output"]["files"], ["README.md"])

    def test_produce_readiness_checklist_tool_reports_submission_assets(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            requirement_text = "Submission Requirements"
            (repo_root / "requirement.md").write_text(requirement_text, encoding="utf-8")
            (repo_root / "README.md").write_text("setup instructions", encoding="utf-8")

            result = LocalMcpToolLayer(repo_root).run_tool(
                "produce_readiness_checklist",
                {"requirement_text": requirement_text},
            )

        checklist = {item["label"]: item["status"] for item in result["output"]["checklist"]}
        self.assertEqual(result["status"], "ok")
        self.assertEqual(checklist["Competition brief"], "present")
        self.assertEqual(checklist["README setup instructions"], "present")
        self.assertEqual(checklist["Kaggle Writeup"], "missing")

    def test_check_security_signals_tool_returns_redacted_findings(self):
        fake_key = "abcdefghijklmnopqrstuvwxyz" + "123456"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "settings.py").write_text(
                f"GOOGLE_API_KEY='{fake_key}'",
                encoding="utf-8",
            )

            result = LocalMcpToolLayer(repo_root).run_tool("check_security_signals")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["output"]["status"], "fail")
        finding = result["output"]["findings"][0]
        self.assertEqual(finding["category"], "likely-secret")
        self.assertNotIn(fake_key, finding["message"])

    def test_tool_layer_cli_lists_tools_as_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "kaggle_capstone_coach.mcp_tools",
                    "list",
                    "--repo-root",
                    tmp_dir,
                ],
                capture_output=True,
                check=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        names = {tool["name"] for tool in payload["tools"]}
        self.assertIn("scan_repository_files", names)
        self.assertIn("check_security_signals", names)

    def test_tool_layer_cli_runs_checklist_tool_with_requirement_text(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "requirement.md").write_text(
                "Submission Requirements",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "kaggle_capstone_coach.mcp_tools",
                    "run",
                    "produce_readiness_checklist",
                    "--repo-root",
                    tmp_dir,
                    "--requirement-text",
                    "Submission Requirements",
                ],
                capture_output=True,
                check=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        checklist = {item["label"]: item["status"] for item in payload["output"]["checklist"]}
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(checklist["Competition brief"], "present")


if __name__ == "__main__":
    unittest.main()
