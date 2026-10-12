"""
TP02 - How to Work with Big Data Files (+5GB)
Module: Big Data Analytics - Master 2 IA & Data Science - 2026/2027

One script, three methods, one report:

    Task 1  pd.read_csv()          -> the classic Out-Of-Memory (OOM) failure
    Task 2  pandas chunking        -> stream the file, constant memory
    Task 3  dask.dataframe         -> parallel + lazy evaluation

It prints a report, writes the metrics to report/results.csv, and draws
the charts (PNG) used in the written report.

Run:
    python generate_dataset.py --gb 6      # 1) create the 5GB+ dataset
    python tp02.py                         # 2) run the three tasks + report
"""
import argparse
import ctypes
import json
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no GUI, we only save images
import matplotlib.pyplot as plt
import pandas as pd
import psutil

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "sales_6gb.csv"
REPORT_DIR = BASE_DIR / "report"
CHUNK_SIZE = 100_000
NUMERIC_COLUMNS = ["quantity", "unit_price", "total_amount"]
TASK1_MEMORY_LIMIT_GB = 6  # cap used to reproduce the OOM on a big-RAM machine


# =====================================================================
#  memory tracking
# =====================================================================
class MemoryMonitor:
    """Sample the RSS (RAM) of a process in a background thread."""

    def __init__(self, pid=None, interval=0.05):
        self.pid = pid
        self.interval = interval
        self.samples = []            # list of (seconds, megabytes)
        self._stop = threading.Event()
        self._thread = None
        self._start = 0.0

    def _sample_loop(self):
        process = psutil.Process(self.pid) if self.pid else psutil.Process()
        while not self._stop.is_set():
            try:
                rss_mb = process.memory_info().rss / 1024 ** 2
            except psutil.Error:
                break
            self.samples.append((time.perf_counter() - self._start, rss_mb))
            time.sleep(self.interval)

    def __enter__(self):
        self._start = time.perf_counter()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    @property
    def peak_mb(self):
        return max((mb for _, mb in self.samples), default=0.0)


# =====================================================================
#  Task 1 - the traditional failure (OOM)
# =====================================================================
# On Windows we can cap a subprocess's memory with a Job Object, so the
# OOM is reproduced even on a machine with a lot of RAM + page file.
class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in
                ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _BASIC_LIMIT(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_void_p),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class _EXTENDED_LIMIT(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _BASIC_LIMIT),
                ("IoInfo", _IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


def _assign_memory_limit(process, limit_bytes):
    """Restrict a process to `limit_bytes` of memory (Windows Job Object)."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    job = kernel32.CreateJobObjectW(None, None)
    info = _EXTENDED_LIMIT()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY
    info.ProcessMemoryLimit = limit_bytes
    kernel32.SetInformationJobObject(
        job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        ctypes.byref(info), ctypes.sizeof(info))
    kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(int(process._handle)))


def _process_tree_rss_mb(pid):
    """Total RSS (MB) of a process and all of its children.

    On Windows the venv's python.exe is a small launcher, so the real
    interpreter is a child process - we must measure the whole tree.
    """
    try:
        parent = psutil.Process(pid)
        processes = [parent] + parent.children(recursive=True)
    except psutil.Error:
        return 0.0
    total = 0
    for process in processes:
        try:
            total += process.memory_info().rss
        except psutil.Error:
            pass
    return total / 1024 ** 2


def task1_oom():
    """Load the whole file with pd.read_csv() and document the failure."""
    size_gb = DATA_FILE.stat().st_size / 1024 ** 3
    print(f"\n[TASK 1] pd.read_csv() on a {size_gb:.2f} GB file")
    print(f"[TASK 1] memory capped at {TASK1_MEMORY_LIMIT_GB} GB to force the OOM")

    command = [sys.executable, str(Path(__file__).resolve()),
               "--task1-worker", "--data", str(DATA_FILE)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    if sys.platform == "win32":
        _assign_memory_limit(process, int(TASK1_MEMORY_LIMIT_GB * 1024 ** 3))

    start = time.perf_counter()
    samples = []
    while process.poll() is None:
        samples.append((time.perf_counter() - start, _process_tree_rss_mb(process.pid)))
        time.sleep(0.05)
    output = process.stdout.read()
    seconds = time.perf_counter() - start
    peak_mb = max((mb for _, mb in samples), default=0.0)

    message = output.strip().splitlines()[-1] if output.strip() else ""
    crashed = ("MemoryError" in output) or ("ArrayMemoryError" in output)
    status = "MemoryError (OOM)" if crashed else f"exit code {process.returncode}"

    print(f"[TASK 1] status={status}  time={seconds:.1f}s  peak={peak_mb/1024:.2f} GB")
    if message:
        print(f"[TASK 1] {message[:160]}")

    return {"method": "Standard Pandas (read_csv)", "peak_mb": peak_mb,
            "seconds": seconds, "status": status, "metrics": None,
            "samples": samples}


# =====================================================================
#  Task 2 - stream processing (pandas chunking)
# =====================================================================
def task2_chunking():
    """Process the file in chunks of 100,000 rows, incrementally."""
    print(f"\n[TASK 2] pandas chunking (chunksize={CHUNK_SIZE:,})")

    totals = {column: 0.0 for column in NUMERIC_COLUMNS}
    rows = 0
    chunks = 0

    with MemoryMonitor() as monitor:
        start = time.perf_counter()
        for chunk in pd.read_csv(DATA_FILE, chunksize=CHUNK_SIZE):
            rows += len(chunk)
            partial = chunk[NUMERIC_COLUMNS].sum()
            for column in NUMERIC_COLUMNS:
                totals[column] += float(partial[column])
            chunks += 1
        seconds = time.perf_counter() - start

    metrics = {
        "rows": rows,
        "total_amount_sum": round(totals["total_amount"], 2),
        "unit_price_mean": round(totals["unit_price"] / rows, 4),
        "quantity_mean": round(totals["quantity"] / rows, 4),
    }
    print(f"[TASK 2] {rows:,} rows in {chunks} chunks  time={seconds:.1f}s  "
          f"peak={monitor.peak_mb/1024:.2f} GB")
    print(f"[TASK 2] sum(total_amount)={metrics['total_amount_sum']:,}  "
          f"mean(unit_price)={metrics['unit_price_mean']}")

    return {"method": "Pandas Chunking", "peak_mb": monitor.peak_mb,
            "seconds": seconds, "status": "OK (constant memory)", "metrics": metrics,
            "samples": monitor.samples}


# =====================================================================
#  Task 3 - parallelized out-of-core compute (Dask)
# =====================================================================
def task3_dask():
    """Load with dask.dataframe: lazy graph, parallel execution."""
    import dask
    import dask.dataframe as dd

    print("\n[TASK 3] dask.dataframe (lazy evaluation + parallel)")

    # --- lazy part: nothing is read/computed here ---
    ddf = dd.read_csv(DATA_FILE)
    numeric = ddf[["total_amount", "unit_price", "quantity"]]
    print(f"[TASK 3] npartitions={ddf.npartitions}  graph tasks={len(ddf.dask)}")
    print("[TASK 3] .compute() not called yet -> no data has been processed (lazy)")

    with MemoryMonitor() as monitor:
        start = time.perf_counter()
        # sum + count in ONE graph: the file is read only once
        sums, counts = dask.compute(numeric.sum(), numeric.count())
        seconds = time.perf_counter() - start

    rows = int(counts["total_amount"])
    metrics = {
        "rows": rows,
        "total_amount_sum": round(float(sums["total_amount"]), 2),
        "unit_price_mean": round(float(sums["unit_price"] / counts["unit_price"]), 4),
        "quantity_mean": round(float(sums["quantity"] / counts["quantity"]), 4),
    }
    print(f"[TASK 3] .compute() done  time={seconds:.1f}s  peak={monitor.peak_mb/1024:.2f} GB")
    print(f"[TASK 3] sum(total_amount)={metrics['total_amount_sum']:,}  "
          f"mean(unit_price)={metrics['unit_price_mean']}")

    return {"method": "Dask DataFrame", "peak_mb": monitor.peak_mb,
            "seconds": seconds, "status": "OK (parallel)", "metrics": metrics,
            "samples": monitor.samples}


# =====================================================================
#  report (console + charts + csv/json/html)
# =====================================================================
def _bar_chart(ax, results, field, title, color_map, transform=lambda v: v, label=""):
    names = [r["method"] for r in results]
    values = [transform(r[field]) for r in results]
    bars = ax.barh(names, values, color=[color_map[r["method"]] for r in results])
    ax.set_title(title)
    ax.set_xlabel(label)
    ax.invert_yaxis()
    for bar, value in zip(bars, values):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f" {value:,.2f}", va="center", fontsize=9)
    ax.grid(axis="x", alpha=0.25)


def build_report(results):
    REPORT_DIR.mkdir(exist_ok=True)
    colors = {"Standard Pandas (read_csv)": "#e5484d",
              "Pandas Chunking": "#f5a524",
              "Dask DataFrame": "#30a46c"}

    # --- results.csv ---
    table = pd.DataFrame([{
        "Method": r["method"],
        "Status": r["status"],
        "Peak RAM (GB)": round(r["peak_mb"] / 1024, 3),
        "Execution time (s)": round(r["seconds"], 2),
    } for r in results])
    table.to_csv(REPORT_DIR / "results.csv", index=False, encoding="utf-8-sig")

    # --- chart 1 + 2 : peak memory and time ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    _bar_chart(axes[0], results, "peak_mb", "Peak RAM usage", colors,
               transform=lambda v: v / 1024, label="GB")
    _bar_chart(axes[1], results, "seconds", "Execution time", colors, label="seconds")
    fig.suptitle(f"TP02 - {DATA_FILE.name} ({DATA_FILE.stat().st_size/1024**3:.1f} GB): "
                 f"Pandas vs Chunking vs Dask", fontweight="bold")
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "benchmark.png", dpi=130)
    plt.close(fig)

    # --- chart 3 : memory over time ---
    fig, ax = plt.subplots(figsize=(11, 4.2))
    for r in results:
        if r["samples"]:
            xs = [s for s, _ in r["samples"]]
            ys = [mb / 1024 for _, mb in r["samples"]]
            ax.plot(xs, ys, label=r["method"], color=colors[r["method"]], linewidth=2)
    ax.set_title("RAM usage over time")
    ax.set_xlabel("seconds")
    ax.set_ylabel("GB")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "memory_timeline.png", dpi=130)
    plt.close(fig)

    # --- json ---
    clean = [{k: v for k, v in r.items() if k != "samples"} for r in results]
    (REPORT_DIR / "results.json").write_text(
        json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- html ---
    rows_html = "".join(
        f"<tr><td>{r['method']}</td><td>{r['status']}</td>"
        f"<td>{r['peak_mb']/1024:.2f} GB</td><td>{r['seconds']:.1f} s</td></tr>"
        for r in results)
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>TP02 report</title><style>
body{{font-family:Segoe UI,system-ui,sans-serif;background:#0b1017;color:#e8eef5;
padding:32px;max-width:1000px;margin:auto}}
h1{{color:#38bdf8}} table{{border-collapse:collapse;width:100%;margin:18px 0}}
th,td{{border:1px solid #22303f;padding:10px;text-align:left}}
th{{background:#16232f;color:#93a3b5}} img{{max-width:100%;border-radius:12px;
border:1px solid #22303f;margin:10px 0;background:#fff}}
.mem{{color:#93a3b5}}</style></head><body>
<h1>TP02 - How to Work with Big Data Files (+5GB)</h1>
<p class="mem">Method comparison: standard Pandas vs Pandas chunking vs Dask DataFrame.</p>
<table><tr><th>Method</th><th>Status</th><th>Peak RAM</th><th>Execution time</th></tr>
{rows_html}</table>
<h2>Benchmark</h2><img src="benchmark.png" alt="benchmark">
<h2>Memory over time</h2><img src="memory_timeline.png" alt="memory timeline">
</body></html>"""
    (REPORT_DIR / "report.html").write_text(html, encoding="utf-8")

    print(f"\nReport written to {REPORT_DIR}  (report.html, benchmark.png, results.csv)")


# =====================================================================
def main():
    global DATA_FILE, REPORT_DIR
    parser = argparse.ArgumentParser(description="TP02 solver")
    parser.add_argument("--data", default=str(DATA_FILE),
                        help="CSV file to process")
    parser.add_argument("--report", default=str(REPORT_DIR),
                        help="folder for the report output")
    parser.add_argument("--task1-worker", action="store_true",
                        help="internal: read the file with pd.read_csv (may OOM)")
    args = parser.parse_args()

    DATA_FILE = Path(args.data)
    REPORT_DIR = Path(args.report)

    if args.task1_worker:
        dataframe = pd.read_csv(DATA_FILE)
        print(f"LOADED {dataframe.shape}")
        return

    if not DATA_FILE.exists():
        raise SystemExit(f"Dataset not found: {DATA_FILE}\n"
                         f"Run: python generate_dataset.py --gb 6")

    print("=" * 66)
    print(f"TP02 - dataset: {DATA_FILE.name} "
          f"({DATA_FILE.stat().st_size/1024**3:.2f} GB)")
    print("=" * 66)

    results = [task1_oom(), task2_chunking(), task3_dask()]

    print("\n" + "=" * 66)
    print(f"{'Method':<30}{'Status':<24}{'Peak RAM':>10}{'Time':>10}")
    print("-" * 66)
    for r in results:
        print(f"{r['method']:<30}{r['status']:<24}"
              f"{r['peak_mb']/1024:>9.2f}G{r['seconds']:>9.1f}s")
    print("=" * 66)

    build_report(results)


if __name__ == "__main__":
    main()
