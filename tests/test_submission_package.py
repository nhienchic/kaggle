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
        youtube_checklist = (
            repo_root / "docs" / "submission" / "youtube-demo-checklist.md"
        ).read_text(encoding="utf-8")
        deployment_checklist = (
            repo_root / "docs" / "submission" / "deployment-checklist.md"
        ).read_text(encoding="utf-8")
        streamlit_config = (
            repo_root / ".streamlit" / "config.toml"
        ).read_text(encoding="utf-8")
        secrets_example = (
            repo_root / ".streamlit" / "secrets.toml.example"
        ).read_text(encoding="utf-8")
        gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
        media_dir = repo_root / "docs" / "submission" / "media-gallery"
        media_cover = media_dir / "cover.png"
        screenshot_names = (
            "streamlit-readiness-overview.png",
            "judge-evidence-dashboard.png",
            "mcp-tools-output.png",
            "security-and-downloads.png",
        )
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

        for expected in (
            "youtube title",
            "youtube description",
            "5 minutes",
            "python -m streamlit run app.py",
            "media gallery",
            "public",
        ):
            self.assertIn(expected, youtube_checklist.lower())
        self.assertIn("GOOGLE_API_KEY", youtube_checklist)

        for expected in (
            "streamlit community cloud",
            "app.py",
            "requirements.txt",
            "python -m streamlit run app.py",
            "secrets",
        ):
            self.assertIn(expected, deployment_checklist.lower())
        self.assertIn("GOOGLE_API_KEY", deployment_checklist)
        self.assertIn("GEMINI_API_KEY", deployment_checklist)
        self.assertIn("headless = true", streamlit_config)
        self.assertIn("GOOGLE_API_KEY = \"replace_me\"", secrets_example)
        self.assertIn(".streamlit/secrets.toml", gitignore)
        self.assertNotRegex(secrets_example, r"[A-Za-z0-9_-]{30,}")

        self.assertTrue(media_cover.exists())
        self.assertGreater(media_cover.stat().st_size, 100_000)
        self.assertIn("cover.png", media_readme)
        self.assertIn("dashboard", media_readme.lower())
        for screenshot_name in screenshot_names:
            screenshot = media_dir / screenshot_name
            self.assertTrue(screenshot.exists(), screenshot_name)
            self.assertGreater(screenshot.stat().st_size, 10_000)
            self.assertEqual(screenshot.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertIn(screenshot_name, media_readme)

        requirement_text = (repo_root / "requirement.md").read_text(encoding="utf-8")
        report = run_readiness_workflow(requirement_text, repo_root, environment={})
        checklist = {item.label: item.status for item in report.checklist}
        self.assertEqual(checklist["Media Gallery"], "present")


if __name__ == "__main__":
    unittest.main()
