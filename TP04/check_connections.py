"""Run inside each node to check its connections to the other two."""
import json
import os
import urllib.request

NODE_NAME = os.environ["NODE_NAME"]
NODES = ["node1", "node2", "node3"]

for other_node in NODES:
    if other_node == NODE_NAME:
        continue

    url = f"http://{other_node}:8000/health"
    with urllib.request.urlopen(url, timeout=5) as response:
        data = json.load(response)

    if data["node"] != other_node or data["size_bytes"] <= 0:
        raise RuntimeError(f"Unexpected response from {other_node}: {data}")

    print(
        f"PASS: {NODE_NAME} -> {other_node}:8000 | "
        f"dataset={data['dataset']} | bytes={data['size_bytes']}"
    )
