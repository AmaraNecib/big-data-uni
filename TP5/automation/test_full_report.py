"""Focused checks for complete-report generation; no broker or screenshot needed."""
from pathlib import Path
import tempfile
import unittest

from .full_report import write_full
from .investigations import require
from .report import QUESTIONS
from .terminal import verify
from . import test_report


class FullReportTests(unittest.TestCase):
    def test_failed_report_does_not_claim_screenshots_or_investigations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "submissions" / "failed"
            folder.mkdir(parents=True)
            result = {"run_id": "failed", "status": "FAILED", "error": "Missing <console>",
                      "scenarios": {}, "screenshots": [], "checks": []}
            write_full(result, folder, root)
            page = (folder / "report.html").read_text(encoding="utf-8")
            self.assertIn("FAILED", page)
            self.assertIn("Missing &lt;console&gt;", page)
            self.assertIn("Required screenshots were not all verified", page)
            self.assertIn("Not verified in this run", page)
            self.assertNotIn("The screenshots linked below show", page)
            parser = test_report.Tags()
            parser.feed(page)
            self.assertFalse(parser.stack)

    def test_all_report_questions_and_relative_entry_points(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "submissions" / "test"
            folder.mkdir(parents=True)
            scenario = test_report.ReportTests().fixture()
            result = {"run_id": "test", "status": "PASS", "screenshots": [], "checks": [],
                      "scenarios": {"teacher": {"path": "reports/teacher/test", "result": scenario}}}
            write_full(result, folder, root)
            markdown = (folder / "report.md").read_text(encoding="utf-8")
            for index, (question, _) in enumerate(QUESTIONS, 1):
                self.assertIn(f"### {index}. {question}", markdown)
            self.assertIn("../../reports/teacher/test/report.md", markdown)
            self.assertIn("submissions/test/report.html", (root / "REPORT.html").read_text(encoding="utf-8"))
            self.assertIn("GitHub", markdown)
            self.assertIn("remain pending", markdown)
            self.assertIn("<svg", (folder / "report.html").read_text(encoding="utf-8"))

    def test_missing_capture_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                verify(Path(temporary) / "missing.png")

    def test_failed_capture_is_rejected_even_with_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.png"
            path.write_bytes(b"not a real screenshot")
            Path(str(path) + ".status").write_text("No console window", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "No console window"):
                verify(path)

    def test_verification_is_not_disabled_by_optimized_python(self):
        with self.assertRaisesRegex(RuntimeError, "bad record count"):
            require(False, "bad record count")
        require(True, "must not fail")


if __name__ == "__main__":
    unittest.main()
