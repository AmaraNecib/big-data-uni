# TP05 lab report

## Submitted code

`producer.py` and `consumer.py` are the teacher's original scripts. The extra exercises are now simple variations:

| File | Changes from the basic exercise |
| --- | --- |
| `producer_extended.py` | Sends 100 readings and adds a building field. |
| `consumer_extended.py` | Adds a sum, a count, an average, and a building filter. |
| `consumer_csv.py` | Writes the five requested columns to CSV. |
| `consumer_extended_csv.py` | Additional owner-requested option: monitoring and CSV in one script. |

Settings are ordinary variables at the top of each script. There are no argument parsers, classes, threads, or custom partition-routing rules in the submitted Python code. Optional testing and screenshot tools were removed from the submission folder and archived under `E:\TP05-runtime\development-tools`.

## Architecture

```text
Python producer
      |
      | JSON sensor readings
      v
Kafka broker, Docker, KRaft mode
      |
      | campus-sensors topic, three partitions
      v
Python consumer
      |
      +--> readings and high-temperature alerts
      +--> average and building filter in the extended exercise
      +--> CSV in the separate optional consumer
```

## Recreated screenshots

After the original screenshots and evidence were deleted, the unchanged teacher scripts were run again. The new run sent and received 30 events and produced 13 high-temperature alerts. The four recreated images are in `screenshots/`; complete output and verified counts are in [evidence/screenshot-run.json](evidence/screenshot-run.json). The images show a native viewer of saved actual output, not live terminals. Source code was not changed. Historical counts below describe the earlier run, not the recreated images. Deleted historical evidence was not recreated or invented.

## Original exercise results

| Check | Observed result |
| --- | --- |
| Kafka | Official image `apache/kafka:3.9.1`, single-node KRaft |
| Topic | `campus-sensors`, three partitions, replication factor 1 |
| Producer | 30 events sent |
| Consumer | 30 readings received, 12 temperature alerts |
| Group offsets | Partition end offsets 11, 9, 10 for partitions 0, 1, 2; lag 0 |

The 29 gaps between the first and last event spanned 29.145 seconds. The producer also sleeps after the final event, so total runtime is about 31 seconds including startup. Its final `flush()` waits for pending sends.

## Earlier investigation results

The following measurements come from the earlier comprehensive test run in [evidence/results.json](evidence/results.json). They were collected **before simplification**, using test utilities and the previous versions of the extra scripts. They are retained as historical results, not presented as output from the new simpler scripts.

### 100-event experiment

| Check | Result |
| --- | --- |
| Retained events | 100, IDs 1 through 100 |
| Average temperature | 30.77 C |
| High-temperature events | 37 |
| Science events and CSV rows | 43 |
| Topic | `campus-investigation-b20bc934` |

The earlier accelerated producer used a 0.01-second delay and explicit partition distribution for the test. The submitted simpler producer now uses the teacher's automatic partition selection and one-second delay. Sending 100 readings therefore takes about 101 seconds. New random readings will have different averages and alert counts.

### Consumer groups

Two same-group consumers divided the 100 records into 67 and 33. Two different groups each received all 100 records. Restarting a group after committing its offsets received zero old records. This shows that `earliest` does not rewind valid saved progress.

### Partition count

With one partition and 12 events, one group member received all 12 and the other was idle. After increasing to three partitions and sending 12 more events, both members could own partitions. A fresh group read the 24 retained records, split 4 and 20.

Old records stayed in their original partition. Increasing partitions did not add another broker, replication, or global ordering. Partition count cannot decrease in place.

### Broker stop and restart

Stopping the TP05 broker caused a new client to fail with `NoBrokersAvailable`. After restarting it, all 100 investigation events remained readable from the persistent volume. This demonstrates the tested stop/start recovery, not protection against losing the only disk or deleting the volume.

## Checks of the simpler code

The simplified scripts were checked separately. See [evidence/simplified-code-checks.txt](evidence/simplified-code-checks.txt) for the results and test scope. Existing event batches and screenshots were not overwritten.

The additional combined consumer was tested with simulated Kafka input. Checks covered the Science filter for both display and CSV, the average across all received readings, the alert at exactly 35 C, all-building mode, an empty stream, Ctrl+C cleanup, and CSV replacement on rerun. These checks passed without sending new events or changing the broker. This combined version is an additional personal exercise, not a separate file required by the teacher.

## Problems and fixes

### Python version

The teacher's exact `kafka-python==2.0.2` dependency is incompatible with Python 3.12 and later. Python 3.11.14 was installed in an isolated environment on E: so the teacher's source and dependency could remain unchanged.

The old client has known security issues. It is kept only for this trusted local classroom exercise. See [DEPENDENCIES.md](DEPENDENCIES.md).

### Kafka storage

The image initially wrote logs outside the PDF's mounted volume. Setting `KAFKA_LOG_DIRS=/var/lib/kafka/data` put them in persistent storage. Docker Desktop already stored its WSL data under `D:\docker\DockerDesktopWSL`.

### Windows networking

Python tried IPv6 for `localhost`. Binding both IPv4 and IPv6 loopback addresses fixed the connection without changing the teacher's Python scripts. PowerShell avoids Git Bash's rewriting of `/opt/kafka/...` paths.

### Disk space

C: initially had about 0.46 GB free. Disposable Docker build cache and pip download cache were cleared. Four large old temporary log files were moved to E:, not deleted. TP04 images and containers were preserved.

A later measurement reported C: 3.38 GB, D: 5.42 GB, and E: 6.88 GB free. These figures are snapshots, not reserved capacity. The recorded measurement is in `evidence/storage.txt`.

### Evidence capture

The four PNGs capture a native viewer displaying the saved actual execution output. They are explicitly labeled as saved output, not live-terminal screenshots. Complete logs accompany them. If the teacher requires live-terminal screenshots, run the README commands and capture those terminals.

## Report answers and submission

The nine requested answers and run instructions are in [README.md](README.md). Source files, Compose, requirements, screenshots, and evidence are included locally. No virtual environments, credentials, or broker volumes are included. GitHub upload remains to be done.
