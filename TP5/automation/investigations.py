"""Fresh consumer-group and partition experiments on isolated temporary topics."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Event, Lock
import time


def consumer(topic, group, **options):
    from kafka import KafkaConsumer
    return KafkaConsumer(
        topic, bootstrap_servers="localhost:9092", group_id=group,
        auto_offset_reset="earliest", enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        **options,
    )


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def compare_shared(topic, partition_count, expected, group):
    """Keep both members polling; wait for stable assignments before replay."""
    start, stop = Event(), Event()
    lock = Lock()
    assignments = [set(), set()]
    joined = [False, False]
    received = [[], []]

    def worker(index):
        client = consumer(topic, group)
        reading = False
        try:
            while not stop.is_set():
                if start.is_set() and not reading:
                    if client.assignment():
                        client.seek_to_beginning(*client.assignment())
                    reading = True
                batches = client.poll(timeout_ms=200)
                with lock:
                    assignments[index] = set(client.assignment())
                    joined[index] = True
                    if reading:
                        for batch in batches.values():
                            received[index].extend((m.partition, m.offset, m.value) for m in batch)
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, index) for index in range(2)]
        try:
            deadline, stable_since = time.monotonic() + 70, None
            while time.monotonic() < deadline:
                for future in futures:
                    if future.done():
                        future.result()
                with lock:
                    stable = (all(joined) and len(assignments[0] | assignments[1]) == partition_count
                              and not assignments[0] & assignments[1]
                              and (partition_count == 1 or all(assignments)))
                stable_since = (stable_since or time.monotonic()) if stable else None
                if stable_since and time.monotonic() - stable_since >= 2:
                    break
                time.sleep(0.1)
            else:
                raise TimeoutError("Two consumer members did not reach stable assignments.")
            start.set()
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline:
                for future in futures:
                    if future.done():
                        future.result()
                with lock:
                    if sum(map(len, received)) >= expected:
                        break
                time.sleep(0.1)
        finally:
            stop.set()
        for future in futures:
            future.result()
    positions = [(partition, offset) for rows in received for partition, offset, _ in rows]
    require(len(positions) == expected == len(set(positions)), "Shared group lost or duplicated records.")
    return {
        "group_id": group,
        "assignments": [sorted(p.partition for p in parts) for parts in assignments],
        "counts": list(map(len, received)), "total": len(positions),
        "records": [[{"partition": p, "offset": o, "event": v} for p, o, v in rows] for rows in received],
    }


def independent(topic, group, expected):
    client = consumer(topic, group, consumer_timeout_ms=6000)
    try:
        records = list(client)
        require(len(records) == expected, f"Independent group received {len(records)}, expected {expected}.")
        client.commit()
        return {"group_id": group, "count": len(records),
                "positions": [[m.partition, m.offset] for m in records]}
    finally:
        client.close()


def run(folder, run_id):
    from kafka import KafkaProducer
    from kafka.admin import KafkaAdminClient, NewPartitions, NewTopic
    from .runner import command

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    summary = {"status": "FAILED", "run_id": run_id, "checks": [], "topics": []}
    admin = producer = None
    log = []

    def record(message):
        print(message, flush=True)
        log.append(message)
        (folder / "investigations.txt").write_text("\n".join(log) + "\n", encoding="utf-8")

    def check(name, passed):
        summary["checks"].append({"name": name, "passed": bool(passed)})
        require(passed, name)

    def send_batch(topic, count, partitions, first_id=1):
        # Deterministic fixtures exercise every partition; student producers are unchanged.
        sent = []
        for index in range(count):
            event = {"event_id": first_id + index, "sensor_id": "sensor-demo",
                     "temperature_c": 25 + index % 15, "humidity_pct": 50,
                     "timestamp": datetime.now(timezone.utc).isoformat(), "campus_building": "Science"}
            metadata = producer.send(topic, value=event, partition=index % partitions).get(timeout=20)
            sent.append({"partition": metadata.partition, "offset": metadata.offset, "event": event})
        return sent

    try:
        admin = KafkaAdminClient(bootstrap_servers="localhost:9092")
        topic, scale_topic = "tp05-groups-" + run_id.lower(), "tp05-partitions-" + run_id.lower()
        admin.create_topics([NewTopic(topic, 3, 1), NewTopic(scale_topic, 1, 1)])
        summary["topics"] = [topic, scale_topic]
        producer = KafkaProducer(bootstrap_servers="localhost:9092", acks="all",
                                 value_serializer=lambda value: json.dumps(value).encode("utf-8"))
        summary["group_sent"] = send_batch(topic, 30, 3)
        record(f"Fresh topic {topic}: 30 deterministic events across 3 partitions.")
        shared = compare_shared(topic, 3, 30, "tp05-shared-" + run_id)
        summary["same_group"] = shared
        check("Same-group members share partitions without duplicate records", shared["total"] == 30)
        record(f"Same group: counts={shared['counts']}; assignments={shared['assignments']}.")
        different = [independent(topic, "tp05-independent-" + suffix + run_id, 30) for suffix in ["a-", "b-"]]
        summary["different_groups"] = different
        check("Different groups each receive all 30 events", all(item["count"] == 30 for item in different))
        record("Different groups: each received 30 events from the same retained topic.")
        resumed = independent(topic, different[0]["group_id"], 0)
        summary["resumed"] = resumed
        check("Committed group resumes without replay despite earliest", resumed["count"] == 0)
        record("Restarted committed group: received 0 old events; earliest did not rewind it.")
        before = send_batch(scale_topic, 12, 1)
        summary["partition_sent_before"] = before
        command(["docker", "exec", "tp05-kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server",
                 "localhost:9092", "--describe", "--topic", scale_topic], folder, "one-partition.txt")
        one = compare_shared(scale_topic, 1, 12, "tp05-one-" + run_id)
        summary["one_partition"] = one
        check("One partition gives one active consumer and one idle consumer", sorted(one["counts"]) == [0, 12])
        record(f"One partition: counts={one['counts']}; assignments={one['assignments']}.")
        admin.create_partitions({scale_topic: NewPartitions(3)})
        deadline = time.monotonic() + 30
        while True:
            # A fresh client avoids relying on private metadata-cache internals.
            producer.close(timeout=10)
            producer = KafkaProducer(bootstrap_servers="localhost:9092", acks="all",
                                     value_serializer=lambda value: json.dumps(value).encode("utf-8"))
            if len(producer.partitions_for(scale_topic) or []) == 3:
                break
            if time.monotonic() > deadline:
                raise TimeoutError("Producer metadata did not observe 3 partitions.")
            time.sleep(0.5)
        after = send_batch(scale_topic, 12, 3, first_id=13)
        summary["partition_sent_after"] = after
        command(["docker", "exec", "tp05-kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server",
                 "localhost:9092", "--describe", "--topic", scale_topic], folder, "three-partitions.txt")
        three = compare_shared(scale_topic, 3, 24, "tp05-three-" + run_id)
        summary["three_partitions"] = three
        check("Three partitions allow both consumers to receive records", all(three["counts"]) and three["total"] == 24)
        old = [item for rows in three["records"] for item in rows if item["event"]["event_id"] <= 12]
        check("Existing records remain in partition 0 at unchanged offsets", sorted((r["partition"], r["offset"]) for r in old) == [(0, i) for i in range(12)])
        record(f"Three partitions: counts={three['counts']}; assignments={three['assignments']}.")
        record("Old records stayed in partition 0. Broker count and replication factor stayed at 1.")
        command(["docker", "exec", "tp05-kafka", "/opt/kafka/bin/kafka-consumer-groups.sh",
                 "--bootstrap-server", "localhost:9092", "--list"], folder, "consumer-groups.txt")
        command(["docker", "compose", "logs", "--tail=50", "kafka"], folder, "broker-logs.txt")
        summary["status"] = "PASS"
        record("PASS: group comparison, committed offsets, and partition growth verified.")
    except Exception as error:
        summary["error"] = str(error)
        record("FAILED: " + str(error))
        raise
    finally:
        if producer is not None:
            producer.close(timeout=10)
        if admin is not None:
            admin.close()
        (folder / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
