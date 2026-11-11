# TP05: real-time data streaming using Apache Kafka

Run: `20261110T200122Z-397186`. Status: **FAILED**.

## Scope and environment

A single Apache Kafka 3.9.1 broker runs in KRaft mode through Docker Compose. Python 3.11 and the teacher's kafka-python==2.0.2 client run synthetic campus sensor producers and consumers. The main topic has three partitions and replication factor 1. No ZooKeeper service or extra broker is involved.

Student scripts remain unchanged. The automation assigns unique consumer groups, captures starting offsets, and applies an eight-second idle timeout so each report covers only its new batch. No existing consumer group is reset. No topic, Docker volume, or stored record is deleted. Unique investigation topics remain available until Kafka retention removes their records.

## Required tasks and measured results

| Scenario | Produced | Independently verified | Displayed | Alerts | Mean temperature C | CSV rows | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| teacher | N/A | N/A | N/A | N/A | N/A | N/A | FAILED |

Teacher mode sends 30 readings at one-second intervals. Extended and CSV modes send 100 readings at one-second intervals. They are different random batches, so their mean temperatures and alert counts need not match. The larger batch takes longer to send. Extended processing calculates the running average across every received event before filtering. Science is the default displayed building. CSV contains only the displayed readings and the five requested columns: event_id, sensor_id, temperature_c, humidity_pct, timestamp.

- [teacher detailed report](../../reports/teacher/20261110T200122Z-0820ca/report.md)

## Consumer-group experiment

Not verified in this run. See the failure below and preserved evidence.

## Report questions

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

Required screenshots were not all verified in this run. See the failure and preserved logs.

## Evidence screenshots

## Problems encountered and solutions

The teacher's old client pin is incompatible with newer Python runtimes used on this computer. The runner uses the existing Python 3.11 environment instead of changing the teacher's dependency. The client has known denial-of-service advisories and is retained only for this trusted local classroom exercise.

Windows localhost can resolve to IPv6. Compose exposes loopback IPv4 and IPv6 so the supplied localhost bootstrap address works. KAFKA_LOG_DIRS points at the mounted data directory so broker storage survives container recreation.

Old retained messages and saved group offsets can make repeated classroom runs confusing. Report consumers use new groups and explicitly recorded starting offsets without resetting the original groups. The separate investigations deliberately read retained records to demonstrate group and offset behavior.

Earlier investigation evidence was deleted. This report uses only fresh results from its own complete run. Screenshots are native Windows console captures, not HTML drawings or synthetic terminal viewers. Capture requires an unlocked interactive desktop and briefly brings each console to the foreground. A capture failure fails the complete workflow rather than silently replacing a screenshot with a fabricated image.

## Verification checks

- FAIL: teacher scenario checks

## Failure

teacher scenario failed. See D:\projects\bigData\big-data-uni\TP05\reports\teacher\20261110T200122Z-0820ca

Inspect error.txt and the saved logs. A failed run is not proof of completion.

## Submission and cleanup

The runner prepares local evidence and the report. It does not log in, commit, push to GitHub, or submit a repository URL. Those submission actions remain pending. Include the TP05 source, compose.yaml, requirements.txt, README, this report, and its linked evidence. Do not upload a virtual environment, credentials, or unnecessary older generated runs.

Docker is left running so the results can be inspected. When finished, run docker compose down from TP05. Do not use down -v unless the stored Kafka data is no longer needed. A broker-failure experiment is not required by the listed further-investigation tasks, and this runner does not stop the broker during testing.
