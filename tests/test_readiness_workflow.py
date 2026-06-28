from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kaggle_capstone_coach.workflow import run_readiness_workflow


class ReadinessWorkflowTests(unittest.TestCase):
    def test_missing_google_api_key_uses_deterministic_fallback(self):
        class FakeModelAdapter:
            def build_agent_summaries(self, context):
                raise AssertionError("adapter should not be called without GOOGLE_API_KEY")

        repo_root = Path(__file__).resolve().parents[1]
        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")

        report = run_readiness_workflow(
            requirement_text,
            repo_root,
            environment={},
            model_adapter=FakeModelAdapter(),
        )

        self.assertEqual(report.model_mode, "deterministic")

    def test_configured_google_api_key_uses_model_adapter(self):
        class FakeModelAdapter:
            def __init__(self):
                self.context = None

            def build_agent_summaries(self, context):
                self.context = context
                return [
                    {
                        "name": "Requirement Analyst",
                        "responsibility": "Model-backed requirement analysis.",
                        "finding": "Fake Gemini analysis referenced the Kaggle Writeup requirement.",
                    },
                    {
                        "name": "Repo Auditor",
                        "responsibility": "Model-backed repo audit.",
                        "finding": "Fake Gemini audit inspected repository evidence.",
                    },
                    {
                        "name": "Submission Strategist",
                        "responsibility": "Model-backed submission planning.",
                        "finding": "Fake Gemini strategy prioritized missing media assets.",
                    },
                    {
                        "name": "Communication Coach",
                        "responsibility": "Model-backed communication drafting.",
                        "finding": "Fake Gemini coach drafted judge-facing language.",
                    },
                ]

        repo_root = Path(__file__).resolve().parents[1]
        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")
        adapter = FakeModelAdapter()

        report = run_readiness_workflow(
            requirement_text,
            repo_root,
            environment={"GOOGLE_API_KEY": "configured"},
            model_adapter=adapter,
        )

        self.assertEqual(report.model_mode, "model-backed")
        self.assertIsNotNone(adapter.context)
        self.assertIn("Fake Gemini analysis", report.agent_summaries[0].finding)

    def test_configured_gemini_api_key_uses_model_adapter(self):
        class FakeModelAdapter:
            def build_agent_summaries(self, context):
                return context["deterministic_summaries"]

        repo_root = Path(__file__).resolve().parents[1]
        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")

        report = run_readiness_workflow(
            requirement_text,
            repo_root,
            environment={"GEMINI_API_KEY": "configured"},
            model_adapter=FakeModelAdapter(),
        )

        self.assertEqual(report.model_mode, "model-backed")

    def test_model_adapter_error_falls_back_to_deterministic_report(self):
        class FailingModelAdapter:
            def build_agent_summaries(self, context):
                raise RuntimeError("Gemini quota exceeded")

        repo_root = Path(__file__).resolve().parents[1]
        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")

        report = run_readiness_workflow(
            requirement_text,
            repo_root,
            environment={"GEMINI_API_KEY": "configured"},
            model_adapter=FailingModelAdapter(),
        )

        self.assertEqual(report.model_mode, "model-error-fallback")
        self.assertIn("Gemini quota exceeded", report.model_error)
        self.assertIn("Model Error", report.to_markdown())

    def test_minimal_repo_produces_submission_readiness_report(self):
        repo_root = Path(__file__).resolve().parents[1]
        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmp_dir:
            minimal_repo = Path(tmp_dir)
            (minimal_repo / "requirement.md").write_text(requirement_text, encoding="utf-8")

            report = run_readiness_workflow(requirement_text, minimal_repo)

        markdown = report.to_markdown()

        self.assertEqual(
            report.title,
            "Kaggle Capstone Submission Coach Readiness Report",
        )
        self.assertEqual(report.model_mode, "deterministic")
        self.assertGreaterEqual(len(report.agent_summaries), 4)

        checklist = {item.label: item.status for item in report.checklist}
        self.assertEqual(checklist["Competition brief"], "present")
        self.assertEqual(checklist["Kaggle Writeup"], "missing")
        self.assertEqual(checklist["YouTube video"], "missing")
        self.assertEqual(checklist["README setup instructions"], "missing")

        self.assertIn("## Readiness Score", markdown)
        self.assertIn("Kaggle Writeup", markdown)
        self.assertIn("## Prioritized Next Steps", markdown)

    def test_app_entrypoint_builds_default_report_from_requirement_file(self):
        from app import build_default_report

        repo_root = Path(__file__).resolve().parents[1]

        report = build_default_report(repo_root, environment={})

        checklist = {item.label: item.status for item in report.checklist}
        self.assertEqual(report.model_mode, "deterministic")
        self.assertEqual(checklist["Competition brief"], "present")

    def test_app_entrypoint_can_report_model_backed_mode(self):
        from app import build_default_report

        class FakeModelAdapter:
            def build_agent_summaries(self, context):
                return context["deterministic_summaries"]

        repo_root = Path(__file__).resolve().parents[1]

        report = build_default_report(
            repo_root,
            environment={"GOOGLE_API_KEY": "configured"},
            model_adapter=FakeModelAdapter(),
        )

        self.assertEqual(report.model_mode, "model-backed")

    def test_app_entrypoint_builds_gemini_adapter_from_environment(self):
        from app import build_default_report

        class FakeGeminiModelAdapter:
            def __init__(self, api_key):
                self.api_key = api_key

            def build_agent_summaries(self, context):
                return context["deterministic_summaries"]

        repo_root = Path(__file__).resolve().parents[1]

        with patch("app.GeminiModelAdapter", FakeGeminiModelAdapter):
            report = build_default_report(
                repo_root,
                environment={"GEMINI_API_KEY": "configured"},
            )

        self.assertEqual(report.model_mode, "model-backed")

    def test_report_exposes_downloadable_submission_artifacts(self):
        repo_root = Path(__file__).resolve().parents[1]
        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")

        report = run_readiness_workflow(requirement_text, repo_root)
        artifacts = {artifact.filename: artifact.content for artifact in report.artifacts()}

        self.assertEqual(
            set(artifacts),
            {
                "readme-draft.md",
                "kaggle-writeup-draft.md",
                "five-minute-video-script.md",
                "submission-readiness-report.md",
            },
        )
        for content in artifacts.values():
            self.assertIn("multi-agent", content.lower())
            self.assertIn("mcp", content.lower())
            self.assertIn("security", content.lower())
            self.assertIn("deployability", content.lower())

    def test_report_includes_security_summary_and_remediation(self):
        requirement_text = "Submission Requirements"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "requirement.md").write_text(requirement_text, encoding="utf-8")
            fake_key = "abcdefghijklmnopqrstuvwxyz" + "123456"
            (repo_root / "settings.py").write_text(
                f"GOOGLE_API_KEY='{fake_key}'",
                encoding="utf-8",
            )

            report = run_readiness_workflow(requirement_text, repo_root)

        markdown = report.to_markdown()

        self.assertEqual(report.security_summary.status, "fail")
        self.assertIn("## Security Summary", markdown)
        self.assertIn("likely-secret", markdown)
        self.assertIn("rotate it if real", markdown)
        self.assertNotIn(fake_key, markdown)


if __name__ == "__main__":
    unittest.main()
