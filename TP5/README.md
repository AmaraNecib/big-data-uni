# TP5: Apache Kafka

Start with `producer.py` and `consumer.py`. These are the teacher's original Python scripts. The extra exercises are small variations of those scripts, with ordinary variables and loops.

Run commands from the `TP5` directory. Docker must be running.

For an Arabic explanation of the Kafka settings and oral-exam practice, open [Kafka-exam-guide-ar.html](Kafka-exam-guide-ar.html). It works offline and includes light/dark modes.

## Complete assignment in one run

From PowerShell in `TP5`, run:

```powershell
python run_all.py
```

On this computer, the launcher automatically uses the existing Python 3.11 environment on E: if the default Python is too new. You can also select it explicitly:

```powershell
& E:\TP05-runtime\venv\Scripts\python.exe run_all.py
```

Allow about **6 to 10 minutes**. Docker Desktop must be available. Keep the Windows desktop unlocked; real console windows briefly appear for screenshot capture. Run only one TP05 launcher at a time and do not send unrelated messages to its topics during verification. This complete screenshot workflow requires Windows; the simpler producer/consumer scripts are still portable.

The command performs these five stages:

1. Run and verify the teacher's 30-event example, with actual console screenshots for status, topic description, producer, and consumer.
2. Run and verify the 100-event average/building-filter exercise.
3. Run and verify the combined CSV exercise and its five required columns.
4. Create fresh investigation topics and compare same-group consumers, different groups, committed offsets, and one versus three partitions.
5. Save seven native console screenshots and generate the complete **English** `report.html`, `report.md`, and `results.json` manifest.

Each complete run has a separate `submissions/<run-id>/` folder. Open [REPORT.html](REPORT.html) to reach the latest complete report. It links the scenario reports under `reports/`, full logs, screenshots, measured results, all nine report answers, and problems/solutions. Keep the linked scenario folders when submitting; the complete report is not a standalone file without its evidence. The HTML works offline and has a Print/PDF button.

The first four screenshots capture the actual commands executing in native Windows console windows. Investigation screenshots show the actual saved transcripts in native consoles and are labelled as such. Capture targets the console window itself, so an unrelated foreground window is not accepted as terminal evidence. No fake terminal images are generated. A screenshot error fails the complete run rather than silently omitting evidence.

Investigation consumers use separate Kafka clients polling concurrently in automation threads. Deterministic fixture events are explicitly distributed across partitions so the ownership comparison is repeatable. The actual teacher and extended producer scripts are unchanged. No existing group is reset, no topic or volume is deleted, and Kafka is left running. Fresh investigation topics remain for inspection and are subject to broker retention.

**Still manual:** commit/push the required files and the chosen complete run's linked evidence to your GitHub repository, then submit its URL. The launcher does not handle credentials or upload anything. Do not include virtual environments, credentials, or unnecessary older generated runs. Broker-stop testing and automatic data deletion are not required steps and are not performed.

## Individual scenario launchers

Open [REPORT.html](REPORT.html) for the most recently generated report entry point. [REPORT.md](REPORT.md) is the Markdown version. The previous hand-written report is preserved as `REPORT-history.md`; it is historical, not the source of the new results.

Choose **one** command in PowerShell from the `TP5` directory:

| Scenario | Command on this computer | Approximate time |
| --- | --- | --- |
| Teacher's original 30-event example | `& E:\TP05-runtime\venv\Scripts\python.exe run_teacher.py` | 70 seconds |
| Our 100-event average/filter exercise | `& E:\TP05-runtime\venv\Scripts\python.exe run_extended.py` | 140 seconds |
| Your combined average/filter/CSV version | `& E:\TP05-runtime\venv\Scripts\python.exe run_csv.py` | 140 seconds |

Each launcher starts the Compose service if needed, creates the topic if absent, starts the consumer, runs the producer, waits for the consumer to finish, and writes a new report folder. You do not need two terminals for these automatic runs. Docker Desktop must already be available. No packages are installed automatically.

Reports go to `reports/teacher/<run-id>/`, `reports/extended/<run-id>/`, or `reports/csv/<run-id>/`. Each contains `report.html`, `report.md`, `results.json`, and the actual command logs. CSV mode also contains its CSV file. The run prints the exact report path when finished. The top-level `REPORT.html` is updated automatically.

The launchers use the unchanged student scripts. A separate automation wrapper gives the consumer a unique group, seeks to the topic end positions captured before the run, and adds an eight-second idle timeout. This isolates each new batch from old messages and existing groups. CSV is written in the new run folder, so earlier exports are not overwritten. The report states these adjustments rather than pretending they are settings in the teacher's original script.

Run one launcher at a time and do not send other events to its topic while it captures the batch. Concurrent senders can make the verification fail. If a run fails or is interrupted, keep its report and logs, fix the stated cause, then rerun to create a new folder. A failed run may already have sent some events; the new run captures a fresh range rather than resending into the old report.

These three individual launchers do **not** automatically repeat the group-comparison or partition-change investigations; use `run_all.py` for those. The manual steps below still cover those. They also do not generate new live-terminal screenshots or stop/delete the Kafka volume. The short root launchers are optional convenience tools, not the code to study for the exam. Their implementation is under `automation/`.

### Rebuild the HTML without rerunning Kafka

If the saved `results.json` files still exist, run:

```powershell
& E:\TP05-runtime\venv\Scripts\python.exe generate_reports.py
```

This recreates scenario and complete-run HTML/Markdown from saved JSON, then restores the latest complete-run entry point. It does not recapture screenshots, send events, start Docker, or repeat the checks. If all saved results were deleted, run the desired launcher to collect a new batch.

On another computer, activate the Python 3.11 environment described below and use `python run_teacher.py`, `python run_extended.py`, or `python run_csv.py`.

## Files to study

| File | What it does |
| --- | --- |
| `producer.py` | Teacher's code: sends 30 sensor events. |
| `consumer.py` | Teacher's code: prints readings and high-temperature alerts. |
| `producer_extended.py` | Sends 100 events and adds `campus_building`. |
| `consumer_extended.py` | Calculates the average and filters a building. |
| `consumer_csv.py` | Optional exercise: saves events to CSV. |
| `consumer_extended_csv.py` | Combines the extended consumer with CSV export. |

Your additional optional script, `consumer_extended_csv.py`, combines the extended consumer with CSV export. The teacher does not require this separate combined version.

`compose.yaml` starts Kafka. `requirements.txt` contains the teacher's exact dependency, `kafka-python==2.0.2`. Optional launch/report automation is separate under `automation/`; the six student producer/consumer scripts stay simple.

## Run the teacher's exercise

Python 3.11 and the dependency are already installed at `E:\TP05-runtime\venv` on this computer.

1. Start Kafka:

   ```powershell
   docker compose up -d
   docker compose ps
   docker compose logs --tail=50 kafka
   ```

   Wait for `Kafka Server started`. Allow about 10 to 30 seconds.

2. Create the topic:

   ```powershell
   docker exec tp05-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic campus-sensors --partitions 3 --replication-factor 1
   ```

3. Start the consumer in one PowerShell terminal:

   ```powershell
   & E:\TP05-runtime\venv\Scripts\python.exe consumer.py
   ```

4. Run the producer in another terminal:

   ```powershell
   & E:\TP05-runtime\venv\Scripts\python.exe producer.py
   ```

Thirty events take about 31 seconds. Stop the consumer with Ctrl+C after observing the readings and alerts. A temperature of 35 degrees Celsius or more produces an alert.

The original consumer group already has saved offsets from our completed run. It waits for new events rather than automatically replaying the old batch. Run the producer to send new events.

## Run the extra exercises

### 100 events and the building field

Create a separate topic so these events do not mix with the original exercise:

```powershell
docker exec tp05-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic campus-sensors-extended --partitions 3 --replication-factor 1
```

1. Start the extended consumer:

   ```powershell
   & E:\TP05-runtime\venv\Scripts\python.exe consumer_extended.py
   ```

2. Run the extended producer in another terminal:

   ```powershell
   & E:\TP05-runtime\venv\Scripts\python.exe producer_extended.py
   ```

It sends 100 events at one-second intervals, so allow about 101 seconds. Stop the consumer with Ctrl+C afterward.

The producer differs from the teacher's version in only a few places:

- `TOPIC` names the separate exercise topic.
- `EVENT_COUNT = 100` sets the number of events.
- `INTERVAL = 1` keeps the teacher's one-second delay.
- `campus_building` randomly selects Science, Library, or Engineering.

There are no command-line options, custom partition-routing rules, or extra functions. To change a setting, edit the variable near the top of the file.

### Running average and building filter

In `consumer_extended.py`:

```python
total_temperature += temperature
event_count += 1
average = total_temperature / event_count
```

`total_temperature` stores the sum. `event_count` stores how many readings arrived. Dividing the sum by the count gives the running average.

The filter is:

```python
if BUILDING is not None and event["campus_building"] != BUILDING:
    continue
```

`continue` skips the display of a reading from another building. The average is updated before this line, so it includes **all received events**, not only Science readings.

Set `BUILDING = "Science"` to show Science readings. Set `BUILDING = None` to show every building. The final count and average are printed when the consumer closes.

### Compare consumer groups

`GROUP_ID` is a plain variable at the top of `consumer_extended.py`.

1. Set `BUILDING = None` so filtering does not hide readings during this comparison.
2. Start two consumer terminals with the same `GROUP_ID`. They share the topic's partitions and divide the work.
3. Stop the second consumer. Change `GROUP_ID` to a new value, such as `"tp05-second-group"`, and restart that consumer. The already-running first consumer keeps its original group ID. The second group can read the retained events independently.

Different groups can each read the complete stream. Consumers in one group divide it. Reusing a group ID resumes its saved offsets; a new ID can replay retained events with `earliest`.

### Compare one partition with three

Use a separate topic for this experiment:

```powershell
docker exec tp05-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic campus-partition-demo --partitions 1 --replication-factor 1
```

1. Set `TOPIC = "campus-partition-demo"` in both extended scripts.
2. Run two consumers with the same new `GROUP_ID`, then run the producer. With one partition, only one consumer can receive records at a time.
3. Increase the topic to three partitions:

   ```powershell
   docker exec tp05-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --alter --topic campus-partition-demo --partitions 3
   ```

4. Run the producer again. Both consumers can now own partitions. Restore `TOPIC = "campus-sensors-extended"` in both scripts when finished.

Partition assignment can take a few seconds to rebalance. The producer chooses partitions automatically, just as in the teacher's script, so record counts need not be equal. Old records stay in their original partition. Kafka cannot decrease the partition count in place. Three partitions on one broker still provide no broker failover or global ordering.

### Optional CSV export

Run the separate CSV consumer:

```powershell
& E:\TP05-runtime\venv\Scripts\python.exe consumer_csv.py
```

It reads the extended topic and writes `sensor_events.csv` in the current directory. The columns are exactly the ones requested in the PDF: `event_id`, `sensor_id`, `temperature_c`, `humidity_pct`, and `timestamp`.

`csv.writer` creates CSV rows. `writer.writerow(...)` writes one row. `flush()` makes each row available on disk without waiting for the consumer to stop. The separate group ID lets this exporter read independently of the monitoring consumer.

Each run **replaces** the CSV file. Change `CSV_FILE` to keep an older export. For a complete replay into a new file, also choose a fresh `GROUP_ID`. Stop with Ctrl+C.

### Your optional combined consumer

`consumer_extended_csv.py` does the same monitoring as `consumer_extended.py` and also saves the displayed readings to `sensor_events_extended.csv`.

1. Start it instead of the other consumers:

   ```powershell
   & E:\TP05-runtime\venv\Scripts\python.exe consumer_extended_csv.py
   ```

2. Run `producer_extended.py` in another terminal:

   ```powershell
   & E:\TP05-runtime\venv\Scripts\python.exe producer_extended.py
   ```

Kafka must be running and the extended topic must exist, as described above. Stop the consumer with Ctrl+C.

With `BUILDING = "Science"`, only Science readings are displayed and saved. Set `BUILDING = None` to display and save all buildings. The running average still includes every received reading, before filtering. CSV contains the same five measurement columns as `consumer_csv.py`; averages and alerts are printed, not added as CSV columns.

This script has its own `GROUP_ID`, so it reads independently of the other consumers. Each run replaces its CSV file. To replay old readings into a new file, change both `GROUP_ID` and `CSV_FILE`.

## Inspect Kafka

```powershell
docker exec tp05-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic campus-sensors
docker exec tp05-kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
docker exec tp05-kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group tp05-campus-monitor
```

`CURRENT-OFFSET` is the next committed read position within a partition. `LOG-END-OFFSET` is the next position at the end of the partition. Their difference is consumer lag.

## Report answers

### 1. What problem does Kafka solve?

Kafka lets producers send continuous events without directly connecting to every consuming application. It stores events so consumers can read at their own pace and replay retained data. Our monitoring consumer does not need to wait for a static file.

### 2. Define the main terms

| Term | Meaning |
| --- | --- |
| Producer | Application that sends events to Kafka. |
| Consumer | Application that reads events from Kafka. |
| Broker | Kafka server that stores and serves partitions. |
| Topic | Named category of events, such as `campus-sensors`. |
| Partition | One ordered log within a topic. |

| Term | Meaning |
| --- | --- |
| Offset | A record's position within one partition. |
| Consumer group | Consumers sharing an ID that divide partition ownership and track their progress. |

### 3. Topic versus partition

A topic is the logical category. Partitions divide its stored records into separate ordered logs. One topic can contain several partitions. Ordering is guaranteed within a partition, not across the entire topic.

### 4. Why use `auto_offset_reset="earliest"`?

It starts from the earliest retained record when the group has no valid saved offset for a partition. It does not rewind a group that already has a valid saved position.

### 5. What does the group ID do?

It identifies shared partition ownership and saved read positions. The same group divides work between its consumers. A different group has independent positions and can read the same data again.

### 6. Why JSON? Give one limitation.

JSON is readable and easily converts between Python dictionaries and messages. It does not enforce a schema, so a missing field or wrong value type can break this simple consumer.

### 7. How does Docker Compose help?

Compose records the image, environment, ports, and volume in one file. One command starts Kafka without manually installing Java and configuring a server on the host.

### 8. What are the single-broker limitations?

One broker is a single point of failure. Replication factor 1 means there is no other replica to take over. Three partitions do not create three servers. This classroom setup also lacks authentication, TLS, backups, and production monitoring. `acks="all"` still waits for only one replica here, and CSV output is not automatically exactly-once.

### 9. Evidence

| Evidence | File |
| --- | --- |
| Running container | [screenshots/01-compose-status.png](screenshots/01-compose-status.png) |
| Topic description | [screenshots/02-topic-description.png](screenshots/02-topic-description.png) |
| Producer output | [screenshots/03-producer.png](screenshots/03-producer.png) |
| Consumer output and alerts | [screenshots/04-consumer.png](screenshots/04-consumer.png) |
| Recreated screenshot run | [evidence/screenshot-run.json](evidence/screenshot-run.json) |

The four PNGs were recreated from a fresh run of the unchanged teacher scripts: 30 events sent and received, with 13 high-temperature alerts. They show a native viewer of actual saved output, not live-terminal captures. Complete logs are in `evidence/`, and the checked counts are in `evidence/screenshot-run.json`. Earlier investigation results described in `REPORT-history.md` belong to a previous run; their deleted evidence has not been reconstructed. The new [REPORT.html](REPORT.html) is generated from separate, newly verified launcher runs.

## Setup on another computer

Use Python 3.10 or 3.11 for the teacher's exact client pin. The old client is not compatible with Python 3.12 and later.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

After activation, use `python producer.py` and `python consumer.py`. On Linux/macOS, create the environment with `python3.11 -m venv .venv` and activate it with `source .venv/bin/activate`.

The old dependency has known denial-of-service issues, including CVE-2026-10142 and CVE-2026-10143. Keep this exercise local and connect only to your trusted broker. The exact teacher pin is preserved for the classroom, not recommended for production.

Use PowerShell for the Docker commands. In Git Bash, prefix `docker exec` with `MSYS_NO_PATHCONV=1` so `/opt/kafka/...` is not rewritten as a Windows path.

## Local Compose adjustments

The Kafka image and KRaft configuration follow the teacher's PDF. Three adjustments make the lab work on this computer:

- Both IPv4 and IPv6 loopback mappings support the teacher's `localhost:9092` without exposing Kafka to the LAN.
- `KAFKA_LOG_DIRS` makes Kafka write to the mounted data volume instead of a temporary container directory.
- Heap and retention settings reduce memory use and disk growth. Retention is asynchronous, not a hard limit on total storage.

Docker data remains on D:. The Python environment is on E:. Neither belongs in the GitHub submission.

## Stop and submit

```powershell
docker compose down
```

This stops the service without deleting the volume. Adding `-v` also deletes the stored Kafka data, so do not use it while you still need your messages.

The complete `TP5` folder is uploaded on the `coursework/docker-kafka-labs` branch of https://github.com/AmaraNecib/big-data-uni. Virtual environments, credentials, and the TP02 dataset are excluded. Historical execution logs retain the original `TP05` path; current commands use `TP5`.

## References

- [Apache Kafka](https://kafka.apache.org/documentation/)
- [Official Kafka Docker image](https://hub.docker.com/r/apache/kafka)
- [kafka-python](https://kafka-python.readthedocs.io/en/master/)
- [Docker Compose](https://docs.docker.com/compose/)
