from pathlib import Path
import unittest


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


if __name__ == "__main__":
    unittest.main()
