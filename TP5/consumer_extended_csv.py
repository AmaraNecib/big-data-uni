import csv
import json
from kafka import KafkaConsumer

TOPIC = "campus-sensors-extended"
GROUP_ID = "tp05-extended-csv-monitor"
BUILDING = "Science"  # Use None to display and save all buildings.
CSV_FILE = "sensor_events_extended.csv"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=lambda value: json.loads(value.decode("utf-8")),
)

total_temperature = 0
event_count = 0

print(f"Listening to topic: {TOPIC}")
try:
    # Each run replaces the CSV file. Change CSV_FILE to keep an old export.
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "event_id", "sensor_id", "temperature_c", "humidity_pct", "timestamp"
        ])

        for message in consumer:
            event = message.value
            temperature = event["temperature_c"]

            # The average includes every received reading, before the filter.
            total_temperature += temperature
            event_count += 1
            average = total_temperature / event_count

            if BUILDING is not None and event["campus_building"] != BUILDING:
                continue

            print(
                f'{event["sensor_id"]} | {event["campus_building"]} | '
                f'T={temperature}°C | RH={event["humidity_pct"]}% | '
                f'Average={average:.2f}°C'
            )
            if temperature >= 35:
                print("ALERT: High temperature detected!")

            writer.writerow([
                event["event_id"],
                event["sensor_id"],
                event["temperature_c"],
                event["humidity_pct"],
                event["timestamp"],
            ])
            csv_file.flush()
except KeyboardInterrupt:
    print("Consumer stopped by user.")
finally:
    consumer.close()
    print("Events received:", event_count)
    if event_count > 0:
        print("Average temperature:", round(total_temperature / event_count, 2))
