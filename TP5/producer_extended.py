import json
import random
import time
from datetime import datetime, timezone
from kafka import KafkaProducer

TOPIC = "campus-sensors-extended"
EVENT_COUNT = 100
INTERVAL = 1

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    acks="all",
)

try:
    for event_id in range(1, EVENT_COUNT + 1):
        event = {
            "event_id": event_id,
            "sensor_id": f"sensor-{random.randint(1, 4):02d}",
            "temperature_c": round(random.uniform(18, 42), 2),
            "humidity_pct": round(random.uniform(25, 85), 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "campus_building": random.choice(["Science", "Library", "Engineering"]),
        }
        producer.send(TOPIC, value=event)
        print("Sent:", event)
        time.sleep(INTERVAL)
    producer.flush()
finally:
    producer.close()
