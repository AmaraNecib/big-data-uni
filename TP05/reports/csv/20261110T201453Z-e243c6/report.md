# TP05: Combined monitoring and CSV

Status: **PASS**

Run: `20261110T201453Z-e243c6`

Started: 2026-11-10T20:14:53.858410+00:00

## What ran

- Producer: `producer_extended.py`
- Consumer: `consumer_extended_csv.py`
- Topic: `campus-sensors-extended`
- Report group: `tp05-report-csv-20261110T201453Z-e243c6`
- Python: `3.11.14`

Fresh events only. A unique report group seeks to the topic end positions captured before this run. An 8-second idle timeout lets the consumer finish. Student source files are not edited. CSV is written inside this run folder.

## Measurements

- Expected events: 100
- Printed by producer: 100
- Independently verified in Kafka: 100
- Displayed after filtering: 36
- Alerts for displayed events: 10

## Analysis

- Average across all received events, C: 29.86
- Building filter: Science
- CSV rows: 36
- Duration, seconds: 114.23

## Verification

- PASS: Requested event count
- PASS: Kafka records equal producer output
- PASS: Displayed readings match building filter
- PASS: High-temperature alerts match displayed readings
- PASS: Consumer counted every new event
- PASS: Running average matches all received events
- PASS: CSV has the five requested columns and exactly the displayed events
- PASS: Student source files remain unchanged

## Scope

This mode does not automatically repeat group comparisons, partition alterations, or broker-failure experiments. Source files are not edited. Existing groups, topics, and volumes are not reset or deleted.

## Report answers

### 1. What problem does Kafka solve?

It separates event producers from consumers, retains events, and lets applications read independently at their own pace.

### 2. Define the main terms.

A producer sends events. A consumer reads them. A broker stores and serves partitions. A topic names an event category. A partition is an ordered log. An offset is a position in one partition. A consumer group divides partition ownership and tracks progress.

### 3. How does a topic differ from a partition?

A topic is a logical category. Partitions divide its log and allow parallel consumption. Ordering is within a partition, not across the entire topic.

### 4. When does earliest apply?

Only when the group has no valid committed position for a partition. It does not rewind valid committed progress. The report runner explicitly seeks its unique capture group to positions recorded before this run.

### 5. What is the group ID for?

Members of one group share partition ownership. Different groups maintain independent progress and can read the same retained data. This report uses a unique group so existing groups are not changed.

### 6. Why JSON, and what is one limitation?

JSON is readable and maps easily to Python dictionaries. It does not enforce a schema; missing or incorrectly typed fields can break these simple consumers.

### 7. How does Compose help?

One configuration file defines Kafka's image, KRaft settings, ports, and persistent storage. Compose starts and inspects it without a manual host Java installation.

### 8. What are the limitations?

One broker and replication factor 1 provide no broker failover. This local lab has plaintext connections, no authentication, no backups, and no exactly-once guarantee for CSV side effects. acks=all acknowledges the only replica here; it does not confirm consumer processing.

### 9. Where is the evidence?

This run folder contains real producer/consumer logs, broker status, the topic description, verified results, and CSV when selected. Existing screenshots under TP05/screenshots belong to a separate run. This HTML is a report, not a live-terminal screenshot.

## Evidence

- [consumer-offsets.txt](consumer-offsets.txt)
- [consumer-ready.txt](consumer-ready.txt)
- [consumer.txt](consumer.txt)
- [docker-start.txt](docker-start.txt)
- [docker-status.txt](docker-status.txt)
- [producer.txt](producer.txt)
- [sensor_events_extended.csv](sensor_events_extended.csv)
- [topic-description.txt](topic-description.txt)

[Full HTML report](report.html) · [Verified data](results.json)
