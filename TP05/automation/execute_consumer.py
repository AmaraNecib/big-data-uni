"""Run a student consumer with an isolated group and bounded capture window."""
import json
from pathlib import Path
import runpy
import sys
import time

import kafka

config = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
original_consumer = kafka.KafkaConsumer


def capture_consumer(*topics, **options):
    # Do not change any existing group's offsets or edit the student's source.
    options["group_id"] = config["group_id"]
    options["consumer_timeout_ms"] = 8000
    consumer = original_consumer(*topics, **options)
    try:
        deadline = time.monotonic() + 45
        while not consumer.assignment():
            consumer.poll(timeout_ms=500)
            if time.monotonic() > deadline:
                raise TimeoutError("The report consumer could not join its group.")
        for partition in consumer.assignment():
            consumer.seek(partition, config["start_offsets"][str(partition.partition)])
        Path(config["ready_file"]).write_text("ready", encoding="utf-8")
        return consumer
    except BaseException:
        consumer.close()
        raise


kafka.KafkaConsumer = capture_consumer
runpy.run_path(sys.argv[1], run_name="__main__")
