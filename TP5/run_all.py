"""Run all TP05 exercises, capture native terminal evidence, and build the report."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import traceback
import uuid

ROOT = Path(__file__).resolve().parent


def main():
    if not (3, 10) <= sys.version_info[:2] < (3, 12):
        # Reuse this computer's already installed compatible environment.
        existing = Path("E:/TP05-runtime/venv/Scripts/python.exe")
        if existing.is_file():
            return subprocess.call([str(existing), "-u", str(Path(__file__).resolve())])
        raise SystemExit("Use Python 3.10 or 3.11 with requirements.txt installed.")
    if os.name != "nt":
        raise SystemExit("The complete native screenshot workflow requires Windows and an unlocked desktop.")

    from automation.runner import run, fingerprint
    from automation.investigations import run as investigate
    from automation.terminal import capture
    from automation.full_report import write_full

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    folder = ROOT / "submissions" / run_id
    folder.mkdir(parents=True)
    screenshots = folder / "screenshots"
    screenshots.mkdir()
    result = {"run_id": run_id, "status": "FAILED", "scenarios": {}, "checks": [],
              "screenshots": [], "submission": "GitHub upload and submission remain pending",
              "started_utc": datetime.now(timezone.utc).isoformat()}
    source_names = ["producer.py", "consumer.py", "producer_extended.py", "consumer_extended.py", "consumer_extended_csv.py", "consumer_csv.py"]
    result["source_sha256"] = {name: fingerprint(ROOT / name) for name in source_names}
    previous_native = os.environ.get("TP05_NATIVE_EVIDENCE")
    previous_no_path = os.environ.get("MSYS_NO_PATHCONV")
    os.environ["MSYS_NO_PATHCONV"] = "1"
    print(f"Complete TP05 run: {run_id}\nReport folder: {folder}", flush=True)
    print("Keep this Windows desktop unlocked. Console windows will briefly come to the foreground.", flush=True)
    try:
        # Check the existing dependency, not install or upgrade it silently.
        import kafka
        if kafka.__version__ != "2.0.2":
            raise RuntimeError("Use the teacher's kafka-python==2.0.2 environment.")
        for index, mode in enumerate(["teacher", "extended", "csv"], 1):
            print(f"STEP {index}/5: {mode} scenario", flush=True)
            os.environ["TP05_NATIVE_EVIDENCE"] = "1" if mode == "teacher" else "0"
            before = set((ROOT / "reports" / mode).glob("*/results.json"))
            code = run(mode)
            created = set((ROOT / "reports" / mode).glob("*/results.json")) - before
            if len(created) != 1:
                raise RuntimeError("Expected one new scenario result. Do not run other TP05 launchers concurrently.")
            path = created.pop()
            data = json.loads(path.read_text(encoding="utf-8"))
            result["scenarios"][mode] = {"path": path.parent.relative_to(ROOT).as_posix(), "result": data}
            result["checks"].append({"name": mode + " scenario checks", "passed": code == 0 and data["status"] == "PASS"})
            if code:
                raise RuntimeError(f"{mode} scenario failed. See {path.parent}")
            if mode == "teacher":
                import shutil
                for source, target, label in [
                    ("docker-status.png", "01-compose-status.png", "Docker Compose status"),
                    ("topic-description.png", "02-topic-description.png", "Topic description"),
                    ("producer.png", "03-producer.png", "Producer output"),
                    ("consumer.png", "04-consumer.png", "Consumer output"),
                ]:
                    shutil.copy2(path.parent / source, screenshots / target)
                    result["screenshots"].append({"label": label, "path": "screenshots/" + target,
                                                   "kind": "Native console screenshot of the actual command execution"})
        print("STEP 4/5: fresh consumer-group and partition experiments", flush=True)
        result["investigations"] = investigate(folder / "investigations", run_id)
        result["checks"].extend(result["investigations"]["checks"])
        print("STEP 5/5: capture investigation consoles and generate English reports", flush=True)
        for source, target, label in [
            ("investigations.txt", "05-group-and-partition-checks.png", "Group and partition verification"),
            ("one-partition.txt", "06-one-partition.png", "One-partition description"),
            ("three-partitions.txt", "07-three-partitions.png", "Three-partition description"),
        ]:
            capture(folder / "investigations" / source, screenshots / target)
            result["screenshots"].append({"label": label, "path": "screenshots/" + target,
                                           "kind": "Native console displaying the saved, unedited investigation transcript"})
        result["checks"].append({"name": "Seven native terminal screenshots saved", "passed": len(result["screenshots"]) == 7})
        unchanged = all(fingerprint(ROOT / name) == checksum for name, checksum in result["source_sha256"].items())
        result["checks"].append({"name": "All six student scripts remain unchanged", "passed": unchanged})
        if not all(item["passed"] for item in result["checks"]):
            raise RuntimeError("A complete-run verification check failed.")
        result["status"] = "PASS"
    except (Exception, KeyboardInterrupt) as error:
        result["error"] = str(error) or type(error).__name__
        (folder / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        print("FAILED: " + result["error"], flush=True)
    finally:
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (folder / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        write_full(result, folder, ROOT)
        for key, old in [("TP05_NATIVE_EVIDENCE", previous_native), ("MSYS_NO_PATHCONV", previous_no_path)]:
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
    print(f"{result['status']}: {folder / 'report.html'}", flush=True)
    print("GitHub upload remains a separate student submission step. Kafka is left running.", flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
