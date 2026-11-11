"""Rebuild saved HTML/Markdown reports without starting Docker or sending events."""
import json
from pathlib import Path

from automation.report import write_overview, write_report
from automation.full_report import write_full

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    results = sorted((root / "reports").glob("*/*/results.json"))
    if not results:
        raise SystemExit("No saved results. Run run_teacher.py, run_extended.py, or run_csv.py first.")
    for path in results:
        write_report(json.loads(path.read_text(encoding="utf-8")), path.parent)
    write_overview(root)
    complete = sorted((root / "submissions").glob("*/results.json"))
    for path in complete:
        write_full(json.loads(path.read_text(encoding="utf-8")), path.parent, root)
    print(f"Rebuilt {len(results)} scenario reports and {len(complete)} complete reports. Open {root / 'REPORT.html'}")
