"""
TP02 - compare the benchmark on two dataset sizes (6 GB vs 20 GB).

Reads  report/6gb/results.json  and  report/20gb/results.json
and writes  report/comparison.png  and  report/comparison.html

Run:  python compare.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "report"
RUNS = [
    ("6 GB", OUTPUT_DIR / "6gb" / "results.json"),
    ("20 GB", OUTPUT_DIR / "20gb" / "results.json"),
]
COLORS = {"6 GB": "#38bdf8", "20 GB": "#a78bfa"}


def load_results():
    return {label: json.loads(path.read_text(encoding="utf-8")) for label, path in RUNS}


def main():
    data = load_results()
    methods = [row["method"] for row in data["6 GB"]]
    positions = np.arange(len(methods))
    width = 0.38

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for index, (label, results) in enumerate(data.items()):
        shift = (index - 0.5) * width
        peak = [row["peak_mb"] / 1024 for row in results]
        times = [row["seconds"] for row in results]
        for bar in axes[0].bar(positions + shift, peak, width, label=label, color=COLORS[label]):
            axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8)
        for bar in axes[1].bar(positions + shift, times, width, label=label, color=COLORS[label]):
            axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f"{bar.get_height():.0f}", ha="center", va="bottom", fontsize=8)

    for ax, title, ylabel in [(axes[0], "Peak RAM usage", "GB"),
                              (axes[1], "Execution time", "seconds")]:
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(positions)
        ax.set_xticklabels(methods, rotation=12, ha="right")
        ax.grid(axis="y", alpha=0.25)
        ax.legend()
    fig.suptitle("TP02 - 6 GB vs 20 GB dataset", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "comparison.png", dpi=130)
    plt.close(fig)

    # --- table + html ---
    rows = ""
    for i, method in enumerate(methods):
        six, twenty = data["6 GB"][i], data["20 GB"][i]
        rows += (f"<tr><td>{method}</td>"
                 f"<td>{six['peak_mb']/1024:.2f} GB</td><td>{twenty['peak_mb']/1024:.2f} GB</td>"
                 f"<td>{six['seconds']:.1f} s</td><td>{twenty['seconds']:.1f} s</td>"
                 f"<td>x{twenty['seconds']/six['seconds']:.2f}</td></tr>")
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>TP02 - 6 GB vs 20 GB</title><style>
body{{font-family:Segoe UI,system-ui,sans-serif;background:#0b1017;color:#e8eef5;
padding:32px;max-width:1000px;margin:auto}} h1{{color:#38bdf8}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}
th,td{{border:1px solid #22303f;padding:10px;text-align:left}}
th{{background:#16232f;color:#93a3b5}} img{{max-width:100%;border-radius:12px;
border:1px solid #22303f;background:#fff;margin-top:10px}}</style></head><body>
<h1>TP02 - Big Data files: 6 GB vs 20 GB</h1>
<table><tr><th>Method</th><th>Peak 6 GB</th><th>Peak 20 GB</th>
<th>Time 6 GB</th><th>Time 20 GB</th><th>Time x</th></tr>{rows}</table>
<img src="comparison.png" alt="comparison"></body></html>"""
    (OUTPUT_DIR / "comparison.html").write_text(html, encoding="utf-8")

    print("comparison.png / comparison.html written to", OUTPUT_DIR)
    print("\nMethod                     | 6GB peak | 20GB peak | 6GB time | 20GB time")
    for i, method in enumerate(methods):
        six, twenty = data["6 GB"][i], data["20 GB"][i]
        print(f"{method:<26} | {six['peak_mb']/1024:>6.2f}G | {twenty['peak_mb']/1024:>7.2f}G "
              f"| {six['seconds']:>7.1f}s | {twenty['seconds']:>8.1f}s")


if __name__ == "__main__":
    main()
