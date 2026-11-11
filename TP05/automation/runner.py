"""Optional run/report automation, separate from the code studied for the exam."""
import ast
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid

from .report import write_report, write_overview

ROOT = Path(__file__).resolve().parents[1]
MODES = {
    "teacher": ("Teacher's original example", "producer.py", "consumer.py", 30),
    "extended": ("Extended monitoring exercise", "producer_extended.py", "consumer_extended.py", 100),
    "csv": ("Combined monitoring and CSV", "producer_extended.py", "consumer_extended_csv.py", 100),
}
CSV_FIELDS = ["event_id", "sensor_id", "temperature_c", "humidity_pct", "timestamp"]


def defaults(path):
    """Read simple constants without executing a producer or consumer."""
    values = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return values


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, folder, name, timeout=90):
    if os.environ.get("TP05_NATIVE_EVIDENCE") == "1" and name in {
        "producer.txt", "docker-status.txt", "topic-description.txt"
    }:
        from .terminal import command as terminal_command
        return terminal_command(args, folder, name, timeout, ROOT)
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            env={**os.environ, "MSYS_NO_PATHCONV": "1", "PYTHONIOENCODING": "utf-8"})
    (folder / name).write_text("$ " + subprocess.list2cmdline(args) + "\n" +
                               result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Command failed. See {name}.")
    return result.stdout


def signature(event):
    return json.dumps(event, sort_keys=True)


def run(mode):
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    title, producer_name, consumer_name, expected = MODES[mode]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    folder = ROOT / "reports" / mode / run_id
    folder.mkdir(parents=True)
    producer_path, consumer_path = ROOT / producer_name, ROOT / consumer_name
    hashes = {name: fingerprint(ROOT / name) for name in [producer_name, consumer_name]}
    result = {
        "mode": mode, "title": title, "run_id": run_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FAILED", "producer": producer_name, "consumer": consumer_name,
        "python": sys.version.split()[0], "expected_events": expected,
        "checks": [], "events": [], "source_sha256": hashes,
        "artifacts": [],
        "automation_scope": "Fresh events only. A unique report group seeks to the topic end positions captured before this run. An 8-second idle timeout lets the consumer finish. Student source files are not edited. CSV is written inside this run folder.",
    }
    process = None
    admin = None
    reader = None
    started = time.monotonic()
    print(f"{title}: starting. Reports: {folder}", flush=True)
    try:
        if not (3, 10) <= sys.version_info[:2] < (3, 12):
            raise RuntimeError("Use Python 3.10 or 3.11 for the teacher's kafka-python==2.0.2 pin.")
        try:
            from kafka import KafkaAdminClient, KafkaConsumer, TopicPartition
            from kafka.admin import NewTopic
            from kafka.errors import KafkaError, TopicAlreadyExistsError
        except ImportError as error:
            raise RuntimeError("Install requirements.txt in the Python 3.11 environment, then rerun.") from error
        p_settings, c_settings = defaults(producer_path), defaults(consumer_path)
        topic = p_settings["TOPIC"]
        if c_settings["TOPIC"] != topic:
            raise ValueError("Producer and consumer TOPIC values must match before running the report.")
        csv_name = c_settings.get("CSV_FILE")
        if csv_name and (Path(csv_name).name != csv_name or "/" in csv_name or "\\" in csv_name):
            raise ValueError("For report runs, CSV_FILE must be a filename without directories.")
        result.update(topic=topic, group_id="tp05-report-" + mode + "-" + run_id,
                      building=c_settings.get("BUILDING"), csv_file=csv_name,
                      interval_seconds=p_settings.get("INTERVAL", 1))
        command(["docker", "compose", "up", "-d"], folder, "docker-start.txt")
        deadline = time.monotonic() + 90
        while True:
            try:
                admin = KafkaAdminClient(bootstrap_servers="localhost:9092")
                break
            except KafkaError:
                if time.monotonic() > deadline:
                    raise RuntimeError("Kafka did not become ready within 90 seconds.")
                time.sleep(2)
        try:
            admin.create_topics([NewTopic(topic, num_partitions=3, replication_factor=1)])
        except TopicAlreadyExistsError:
            pass
        command(["docker", "compose", "ps"], folder, "docker-status.txt")
        command(["docker", "exec", "tp05-kafka", "/opt/kafka/bin/kafka-topics.sh",
                 "--bootstrap-server", "localhost:9092", "--describe", "--topic", topic],
                folder, "topic-description.txt")
        reader = KafkaConsumer(bootstrap_servers="localhost:9092", group_id=None,
                               enable_auto_commit=False,
                               value_deserializer=lambda value: json.loads(value.decode("utf-8")))
        partitions = reader.partitions_for_topic(topic)
        if not partitions:
            raise RuntimeError("Kafka returned no partitions for the selected topic.")
        assigned = [TopicPartition(topic, number) for number in sorted(partitions)]
        reader.assign(assigned)
        starts = reader.end_offsets(assigned)
        result["start_offsets"] = {str(p.partition): offset for p, offset in starts.items()}
        ready = folder / "consumer-ready.txt"
        config = folder / "capture-config.json"
        config.write_text(json.dumps({"group_id": result["group_id"],
                                      "start_offsets": result["start_offsets"],
                                      "ready_file": str(ready)}, indent=2), encoding="utf-8")
        print("Kafka ready. Starting the consumer before the producer.", flush=True)
        with (folder / "consumer.txt").open("w", encoding="utf-8") as output:
            consumer_args = [sys.executable, "-u", str(ROOT / "automation" / "execute_consumer.py"),
                             str(consumer_path), str(config)]
            if os.environ.get("TP05_NATIVE_EVIDENCE") == "1":
                # PowerShell owns its transcript writer; do not hold a competing file handle.
                output.close()
                from .terminal import launch
                process = launch(consumer_args, folder / "consumer.txt", folder / "consumer.png", folder)
            else:
                process = subprocess.Popen(
                    consumer_args, cwd=folder, stdout=output, stderr=subprocess.STDOUT,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )
            deadline = time.monotonic() + 60
            while not ready.exists():
                if process.poll() is not None:
                    raise RuntimeError("Consumer could not start. See consumer.txt.")
                if time.monotonic() > deadline:
                    raise TimeoutError("Consumer did not become ready within 60 seconds.")
                time.sleep(0.2)
            print(f"Sending {expected} events with the script's configured delay. See producer.txt for output.", flush=True)
            producer_output = command([sys.executable, "-u", str(producer_path)], folder,
                                      "producer.txt", timeout=max(90, int(expected * result["interval_seconds"]) + 90))
            process.wait(timeout=45)
            if process.returncode:
                raise RuntimeError("Consumer failed. See consumer.txt.")
            if os.environ.get("TP05_NATIVE_EVIDENCE") == "1":
                from .terminal import verify
                verify(folder / "consumer.png")
        print("Producer and consumer finished. Checking Kafka records and CSV.", flush=True)
        sent = [ast.literal_eval(line.split("Sent: ", 1)[1])
                for line in producer_output.splitlines() if line.startswith("Sent: ")]
        ends = reader.end_offsets(assigned)
        result["end_offsets"] = {str(p.partition): offset for p, offset in ends.items()}
        for partition in assigned:
            reader.seek(partition, starts[partition])
        received = []
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if all(reader.position(p) >= ends[p] for p in assigned):
                break
            for partition, batch in reader.poll(timeout_ms=500).items():
                received.extend(message.value for message in batch if message.offset < ends[partition])
        else:
            raise TimeoutError("Could not verify the complete captured Kafka offset range.")
        reader.close()
        reader = None
        consumer_output = (folder / "consumer.txt").read_text(encoding="utf-8")
        building = result["building"]
        displayed = [event for event in received if building is None or event.get("campus_building") == building]
        alerts = sum(event["temperature_c"] >= 35 for event in displayed)
        average = sum(event["temperature_c"] for event in received) / len(received) if received else None
        result.update(produced=len(sent), verified_in_kafka=len(received), displayed=len(displayed),
                      alerts=alerts, average_temperature_c=round(average, 2) if average is not None else None,
                      events=sorted(received, key=lambda event: event["event_id"]))
        result["checks"] = [
            {"name": "Requested event count", "passed": len(sent) == expected},
            {"name": "Kafka records equal producer output", "passed": Counter(map(signature, sent)) == Counter(map(signature, received))},
            {"name": "Displayed readings match building filter", "passed": consumer_output.count(" | T=") == len(displayed)},
            {"name": "High-temperature alerts match displayed readings", "passed": consumer_output.count("ALERT:") == alerts},
        ]
        if mode != "teacher":
            result["checks"].extend([
                {"name": "Consumer counted every new event", "passed": f"Events received: {len(received)}" in consumer_output},
                {"name": "Running average matches all received events", "passed": f"Average temperature: {round(average, 2)}" in consumer_output if average is not None else False},
            ])
        if mode == "csv":
            with (folder / csv_name).open(encoding="utf-8", newline="") as file:
                csv_reader = csv.DictReader(file)
                rows = list(csv_reader)
                fields_match = csv_reader.fieldnames == CSV_FIELDS
            expected_rows = [{field: str(event[field]) for field in CSV_FIELDS} for event in displayed]
            result["csv_rows"] = len(rows)
            result["checks"].append({"name": "CSV has the five requested columns and exactly the displayed events", "passed": fields_match and Counter(map(signature, rows)) == Counter(map(signature, expected_rows))})
        result["checks"].append({"name": "Student source files remain unchanged", "passed": all(fingerprint(ROOT / name) == checksum for name, checksum in hashes.items())})
        command(["docker", "exec", "tp05-kafka", "/opt/kafka/bin/kafka-consumer-groups.sh",
                 "--bootstrap-server", "localhost:9092", "--describe", "--group", result["group_id"]],
                folder, "consumer-offsets.txt")
        result["status"] = "PASS" if all(check["passed"] for check in result["checks"]) else "FAILED"
    except (Exception, KeyboardInterrupt) as error:
        result["error"] = str(error) or type(error).__name__
        (folder / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        print(f"Run stopped: {result['error']}", flush=True)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=15)
        if reader is not None:
            reader.close()
        if admin is not None:
            admin.close()
        result["duration_seconds"] = round(time.monotonic() - started, 2)
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        result["artifacts"] = [p.name for p in folder.iterdir() if p.is_file() and p.suffix in [".txt", ".csv"]]
        (folder / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        write_report(result, folder)
        write_overview(ROOT)
    print(f"{result['status']}: {folder / 'report.html'}", flush=True)
    return 0 if result["status"] == "PASS" else 1
