from pathlib import Path
import tempfile
import unittest

from kaggle_capstone_coach.security import scan_repository_security, safe_read_text


class SecurityScannerTests(unittest.TestCase):
    def test_safe_repository_has_pass_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "README.md").write_text("No credentials here.", encoding="utf-8")

            summary = scan_repository_security(repo_root)

        self.assertEqual(summary.status, "pass")
        self.assertEqual(summary.findings, ())

    def test_likely_secret_is_flagged_without_exposing_value(self):
        secret_value = "sk-test-" + "abcdefghijklmnopqrstuvwxyz" + "123456"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "settings.py").write_text(
                f"OPENAI_API_KEY = '{secret_value}'",
                encoding="utf-8",
            )

            summary = scan_repository_security(repo_root)

        self.assertEqual(summary.status, "fail")
        self.assertEqual(len(summary.findings), 1)
        finding = summary.findings[0]
        self.assertEqual(finding.category, "likely-secret")
        self.assertEqual(finding.path, "settings.py")
        self.assertNotIn(secret_value, finding.message)
        self.assertIn("OPENAI_API_KEY", finding.message)

    def test_risky_env_file_is_warned_but_env_example_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".env").write_text("GOOGLE_API_KEY=\n", encoding="utf-8")
            (repo_root / ".env.example").write_text("GOOGLE_API_KEY=\n", encoding="utf-8")

            summary = scan_repository_security(repo_root)

        self.assertEqual(summary.status, "warn")
        self.assertEqual(len(summary.findings), 1)
        finding = summary.findings[0]
        self.assertEqual(finding.category, "risky-env-file")
        self.assertEqual(finding.path, ".env")

    def test_safe_read_text_rejects_paths_outside_repo_root(self):
        with tempfile.TemporaryDirectory() as repo_dir:
            repo_root = Path(repo_dir)
            inside = repo_root / "notes.md"
            inside.write_text("safe", encoding="utf-8")

            with tempfile.TemporaryDirectory() as outside_dir:
                outside = Path(outside_dir) / "secret.txt"
                outside.write_text("do not read", encoding="utf-8")

                self.assertEqual(safe_read_text(repo_root, inside), "safe")
                with self.assertRaises(ValueError):
                    safe_read_text(repo_root, outside)


if __name__ == "__main__":
    unittest.main()
