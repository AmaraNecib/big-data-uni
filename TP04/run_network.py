"""Start the three nodes and check every directed connection."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
DATASET = ROOT.parent / "TP2_big_data_files" / "data" / "sales_6gb.csv"


def run(command):
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    import os

    data_directory = Path(os.environ.get("TP04_DATA_DIR", str(DATASET.parent)))
    if not (data_directory / "sales_6gb.csv").is_file():
        raise SystemExit(f"Dataset missing: {data_directory / 'sales_6gb.csv'}")

    # Build once first using: docker compose build node1
    run(["docker", "compose", "up", "-d", "--no-build", "--wait", "--wait-timeout", "90"])
    run(["docker", "compose", "ps"])

    for node in ["node1", "node2", "node3"]:
        run(["docker", "compose", "exec", "-T", node, "python", "/app/check_connections.py"])

    print("PASS: all six directed connections succeeded. Nodes are left running.")
