# TP04: Docker deployment with three connected nodes

Run commands from this `TP04` directory. The Docker work now has its own folder. TP02 files and the original local dataset remain in `../TP2_big_data_files`; they were not moved or deleted.

## Start the network demonstration

1. Build the image once:

   ```powershell
   docker compose build node1
   ```

2. Start the three nodes and check every connection:

   ```powershell
   python run_network.py
   ```

   The launcher uses only Python's standard library on the host. It starts the existing image without rebuilding, waits for health checks, then executes `check_connections.py` inside each node. Allow about 30 to 90 seconds. A nonzero exit means a start or connection check failed.

3. Open the nodes from your host:

   ```text
   http://localhost:8001/health
   http://localhost:8002/health
   http://localhost:8003/health
   ```

Each endpoint returns the node name, dataset path, byte size, and CSV column names. It reads only the header, not the entire 6 GB file. Unknown paths return 404; a missing or unreadable dataset returns 503.

## How the network works

```text
Host localhost:8001 -> node1:8000
Host localhost:8002 -> node2:8000
Host localhost:8003 -> node3:8000

Inside the Compose network:
node1 -> http://node2:8000/health
node1 -> http://node3:8000/health
node2 -> node1 and node3
node3 -> node1 and node2
```

The user-defined bridge network is `tp04-local_nodes`. Docker DNS resolves the Compose service names `node1`, `node2`, and `node3`. Nodes use the internal port 8000, not the host ports 8001 to 8003. `localhost` inside one container means that same container, not a different node.

All three services use `tp04-local:1.0`. Separate Compose-generated names avoid collisions with earlier `tp04-node1` containers. Ports are published on loopback only. No SSH server, extra network package, or privileged container is required.

This is a connectivity demonstration. It does not split the TP02 file analysis across the three nodes and is not a distributed Dask cluster.

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile`, `.dockerignore` | Build the application image without sending the dataset to Docker. |
| `compose.yaml` | Define three nodes, network, read-only data mount, ports, and optional analysis. |
| `node_server.py` | Standard-library HTTP service on each node. |
| `check_connections.py`, `run_network.py` | Check peers from inside each node; orchestrate those checks from the host. |
| `tp02.py`, `requirements.txt` | Copy of the existing TP02 analysis and its dependency list. |

## Local dataset and space

All nodes mount the same directory read-only:

```text
Host:      ../TP2_big_data_files/data
Container: /app/data
CSV:       /app/data/sales_6gb.csv
```

The local CSV is 6,463,485,112 bytes. It is neither copied into this folder nor embedded in the image. The PDF explicitly uses a read-only data bind mount in Task 4. This setup follows that approach.

The image reuses the existing `amaranecib/sales-bigdata-tp04:1.0` Python environment, which already includes pandas, Dask, psutil, matplotlib, and PyArrow. It adds only the source files. This avoids downloading another environment and copying a 6 GB file while D: has about 1 GB free. The build context was about 19 KB, not 6 GB.

On a different machine, provide your local dataset directory before running Compose:

```powershell
$env:TP04_DATA_DIR = "E:/datasets/tp02"
python run_network.py
```

That directory must already contain `sales_6gb.csv`. Do not put large datasets in Git. The Compose mount refuses to create a missing host directory silently.

The default Dockerfile intentionally reuses an existing application image rather than reinstalling dependencies. `RUN` creates the report directory and sets permissions; the non-root `appuser` runs the application. `ENTRYPOINT []` clears the inherited analysis entrypoint, so the default `CMD` can start the node service.

## Run the actual data analysis

The three nodes stay lightweight. The full analysis is a separate opt-in Compose profile:

```powershell
docker compose --profile analysis run --rm --no-deps data-analysis
```

It runs the local 6 GB CSV through the copied `tp02.py` and writes its results to `TP04/report/`. Allow several minutes; runtime depends on CPU, RAM, disk, and other work. This command performs the Pandas chunking and Dask analyses, not just a connectivity check.

`--skip-oom` avoids the intentionally memory-intensive full-file read and its Windows-specific demonstration. It does not skip the chunking or Dask tasks. Do not run several full analyses at once on this disk-constrained computer.

The PDF's build-and-start form is also supported:

```powershell
docker compose up --build -d
```

By default it starts the three networking services. The analysis profile is opt-in so ordinary network tests do not unexpectedly scan 6 GB.

## Image push and pull required by the PDF

The new image was built locally. No new registry push is claimed. To publish it under your Docker Hub account:

```powershell
docker login
docker tag tp04-local:1.0 YOUR_USERNAME/sales-bigdata-tp04:local-network
docker push YOUR_USERNAME/sales-bigdata-tp04:local-network
docker pull YOUR_USERNAME/sales-bigdata-tp04:local-network
```

Replace `YOUR_USERNAME` with your account. Capture the real push and pull output for the submission. Login credentials must not be placed in the Dockerfile, Compose file, or Git repository. Pulling this code-only image does not download the dataset; the local bind mount is still required.

## Inspect and stop

```powershell
docker compose ps
docker compose logs --tail=30 node1 node2 node3
docker network inspect tp04-local_nodes
docker compose exec -T node1 python /app/check_connections.py
```

Stop only this project's services and network without deleting the host dataset:

```powershell
docker compose down
```

The setup does not remove TP02 data, TP05 Kafka, or earlier TP04 containers.

## Report answers

### What is Docker, and why use it for data science?

Docker packages an application runtime into an image and starts isolated containers from it. It helps reproduce the same Python environment across machines without installing every dependency on the host. Large local data can remain outside the image and be mounted when needed.

### Image versus container

An image is a reusable filesystem and startup configuration. A container is an instance created from that image. Our three nodes share one image but have separate processes, names, and network identities.

### FROM, WORKDIR, COPY, RUN, CMD

| Instruction | Use in this Dockerfile |
| --- | --- |
| `FROM` | Reuse the existing TP04 Python application environment. |
| `WORKDIR` | Set `/app` as the working directory. |
| `COPY` | Add analysis and networking scripts, not the CSV. |
| `RUN` | Create the report directory and set ownership during the build. |
| `CMD` | Start the HTTP node service by default. Compose can override it for analysis. |

### What problem does Compose solve?

It records services, image builds, data mounts, ports, health checks, and a shared network in one YAML file. The nodes can be started and stopped consistently without repeating long individual Docker commands.

### docker run versus docker compose up

`docker run` creates one container from command-line options. `docker compose up` reads the project configuration and creates its services and network together. Port publishing is for host access; the shared network provides container-to-container access.

### How could we add a database?

Add a database service to the same network with its own persistent volume. Nodes would connect using that service's DNS name and internal port. Keep credentials outside Git, and do not use the application's read-only CSV mount as the database's writable storage.

## Verification and submission

[evidence/network-check.txt](evidence/network-check.txt) records a real successful run: three healthy containers and all six directed HTTP connections. Every peer returned the same 6,463,485,112-byte dataset. This proves DNS/HTTP reachability and access to the shared local file, not distributed processing or image publication.

The full local 6 GB analysis also completed successfully. Pandas processed 75,000,000 rows in 491.3 seconds with about 0.18 GB peak RAM. Dask completed in 116.5 seconds with about 2.90 GB peak RAM. Both returned the same sum and mean. See [report/report.html](report/report.html), [report/results.json](report/results.json), and [evidence/analysis-run.txt](evidence/analysis-run.txt). These are results of this actual container run, not timings copied from TP02.

Upload this folder's source, small generated report, and README to GitHub. Add real screenshots for Docker installation, image push/pull, the three running containers, the network check, and an analysis run. Do not invent push evidence or include the dataset, credentials, or build cache. The older Arabic explanation copied into this folder is historical and may describe the earlier image approach; this README describes the current local-mount implementation.
