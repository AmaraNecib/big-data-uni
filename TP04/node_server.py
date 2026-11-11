"""A small networking demonstration, not a distributed analytics engine."""
import csv
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

NODE_NAME = os.environ.get("NODE_NAME", "node")
DATASET = Path("/app/data/sales_6gb.csv")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return
        try:
            with DATASET.open(encoding="utf-8", newline="") as file:
                columns = next(csv.reader(file))
            result = {
                "node": NODE_NAME,
                "dataset": str(DATASET),
                "size_bytes": DATASET.stat().st_size,
                "columns": columns,
            }
        except (OSError, StopIteration) as error:
            self.send_error(503, str(error))
            return
        body = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


print(f"{NODE_NAME}: listening on port 8000")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
