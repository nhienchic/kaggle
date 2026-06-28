from pathlib import Path
import unittest

from kaggle_capstone_coach.workflow import run_readiness_workflow


class SubmissionPackageTests(unittest.TestCase):
    def test_repository_contains_complete_submission_package(self):
        repo_root = Path(__file__).resolve().parents[1]

        readme = (repo_root / "README.md").read_text(encoding="utf-8").lower()
        env_example = (repo_root / ".env.example").read_text(encoding="utf-8")
        writeup = (
            repo_root / "docs" / "submission" / "kaggle-writeup-draft.md"
        ).read_text(encoding="utf-8")
        video_script = (
            repo_root / "docs" / "submission" / "five-minute-video-script.md"
        ).read_text(encoding="utf-8")
        media_cover = repo_root / "docs" / "submission" / "media-gallery" / "cover.png"
        media_readme = (
            repo_root / "docs" / "submission" / "media-gallery" / "README.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "problem",
            "solution",
            "multi-agent",
            "mcp",
            "security",
            "setup",
            "python -m streamlit run app.py",
            "python -m unittest discover -s tests",
            "streamlit community cloud",
        ):
            self.assertIn(expected, readme)

        self.assertIn("GOOGLE_API_KEY=", env_example)
        self.assertNotRegex(env_example, r"[A-Za-z0-9_-]{30,}")

        combined_submission = f"{writeup}\n{video_script}".lower()
        for expected in (
            "kaggle capstone submission coach",
            "streamlit",
            "multi-agent",
            "mcp",
            "security",
            "gemini",
            "deployability",
        ):
            self.assertIn(expected, combined_submission)

        self.assertTrue(media_cover.exists())
        self.assertGreater(media_cover.stat().st_size, 100_000)
        self.assertIn("cover.png", media_readme)
        self.assertIn("dashboard", media_readme.lower())

        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")
        report = run_readiness_workflow(requirement_text, repo_root, environment={})
        checklist = {item.label: item.status for item in report.checklist}
        self.assertEqual(checklist["Media Gallery"], "present")


if __name__ == "__main__":
    unittest.main()
