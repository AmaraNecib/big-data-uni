import csv
import json
from kafka import KafkaConsumer

TOPIC = "campus-sensors-extended"
GROUP_ID = "tp05-csv-export"
CSV_FILE = "sensor_events.csv"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=lambda value: json.loads(value.decode("utf-8")),
)

try:
    # Each run replaces the CSV file. Use a new filename to keep an old export.
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "event_id", "sensor_id", "temperature_c", "humidity_pct", "timestamp"
        ])

        for message in consumer:
            event = message.value
            writer.writerow([
                event["event_id"],
                event["sensor_id"],
                event["temperature_c"],
                event["humidity_pct"],
                event["timestamp"],
            ])
            csv_file.flush()
            print("Saved event:", event["event_id"])
except KeyboardInterrupt:
    print("Consumer stopped by user.")
finally:
    consumer.close()
