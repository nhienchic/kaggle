from pathlib import Path
import tempfile
import unittest

from kaggle_capstone_coach.workflow import run_readiness_workflow


class ReadinessWorkflowTests(unittest.TestCase):
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

        report = build_default_report(repo_root)

        checklist = {item.label: item.status for item in report.checklist}
        self.assertEqual(report.model_mode, "deterministic")
        self.assertEqual(checklist["Competition brief"], "present")

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


if __name__ == "__main__":
    unittest.main()
