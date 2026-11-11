"""Focused tests for optional automation, not part of the Kafka exercise."""
import ast
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

from .report import write_report, write_overview, chart
from .runner import defaults, signature


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in ["meta", "br", "hr", "link", "input"]:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise AssertionError(f"Invalid closing tag: {tag}")


class ReportTests(unittest.TestCase):
    def fixture(self):
        return {
            "mode": "teacher", "title": "Test <not executable>", "run_id": "test-only",
            "status": "PASS", "started_utc": "2026-01-01T00:00:00Z",
            "finished_utc": "2026-01-01T00:00:01Z", "expected_events": 1,
            "producer": "producer.py", "consumer": "consumer.py", "python": "3.11",
            "source_sha256": {"producer.py": "abc"}, "artifacts": ["producer.txt"],
            "automation_scope": "Simulated data in a temporary test directory only.",
            "checks": [{"name": "Test check", "passed": True}],
            "events": [{"event_id": 1, "sensor_id": "sensor-01", "temperature_c": 35,
                        "humidity_pct": 50, "timestamp": "2026-01-01T00:00:00Z"}],
        }

    def test_html_markdown_and_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "teacher" / "test-only"
            folder.mkdir(parents=True)
            write_report(self.fixture(), folder)
            page = (folder / "report.html").read_text(encoding="utf-8")
            parser = Tags()
            parser.feed(page)
            self.assertEqual(parser.stack, [])
            self.assertIn("Test &lt;not executable&gt;", page)
            self.assertNotIn("Test <not executable>", page)
            self.assertIn("<svg", page)
            self.assertTrue((folder / "report.md").exists())
            self.assertIn("test-only/report.html", (folder.parent / "index.html").read_text())

    def test_failed_run_is_not_presented_as_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "csv" / "failed-test"
            folder.mkdir(parents=True)
            result = self.fixture()
            result.update(status="FAILED", error="Kafka unavailable <example>", events=[], checks=[])
            write_report(result, folder)
            page = (folder / "report.html").read_text(encoding="utf-8")
            self.assertIn("FAILED", page)
            self.assertIn("Kafka unavailable &lt;example&gt;", page)
            self.assertIn("No verification checks completed", page)
            self.assertNotIn("class='series'", page)

    def test_index_preserves_old_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name in ["a", "b"]:
                folder = Path(temporary) / "teacher" / name
                folder.mkdir(parents=True)
                write_report(self.fixture(), folder)
            index = (folder.parent / "index.html").read_text()
            self.assertIn("a/report.html", index)
            self.assertIn("b/report.html", index)

    def test_overview_uses_saved_measured_results(self):
        import json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "reports" / "teacher" / "test-only"
            folder.mkdir(parents=True)
            result = self.fixture()
            result.update(verified_in_kafka=1, displayed=1, duration_seconds=2)
            (folder / "results.json").write_text(json.dumps(result), encoding="utf-8")
            write_overview(root)
            page = (root / "REPORT.html").read_text(encoding="utf-8")
            parser = Tags()
            parser.feed(page)
            self.assertEqual(parser.stack, [])
            self.assertIn("reports/teacher/test-only/report.html", page)
            self.assertIn("Test &lt;not executable&gt;", page)
            self.assertTrue((root / "REPORT.md").exists())

    def test_empty_chart(self):
        self.assertIn("No verified event series", chart([]))

    def test_constants_without_running_script(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(defaults(root / "producer_extended.py")["EVENT_COUNT"], 100)
        self.assertEqual(defaults(root / "consumer_extended_csv.py")["BUILDING"], "Science")

    def test_event_comparison_ignores_dictionary_order(self):
        self.assertEqual(signature({"a": 1, "b": 2}), signature({"b": 2, "a": 1}))

    def test_all_automation_python_parses(self):
        for file in Path(__file__).parent.glob("*.py"):
            ast.parse(file.read_text(encoding="utf-8"), filename=str(file))


if __name__ == "__main__":
    unittest.main()
