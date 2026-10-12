"""
TP02 - Step 0: create the big data file (5 GB+).

Downloading a real 5 GB+ CSV is very slow, so this script generates a
realistic *sales* dataset with a controlled size. The result is the
"5GB+ dataset" used by the three TP02 tasks (OOM / chunking / Dask).

It has mixed types on purpose:
  - numeric columns (quantity, unit_price, total_amount) -> mean / sum
  - string columns (customer_id, product, ...) -> they also make the
    in-memory DataFrame much bigger than the file, which helps show the OOM.

Usage:
    python generate_dataset.py            # ~6 GB
    python generate_dataset.py --gb 8     # ~8 GB
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
CSV_FILE = DATA_DIR / "sales_big.csv"
ROWS_PER_CHUNK = 1_000_000

PRODUCTS = np.array(["Laptop", "Smartphone", "Tablet", "Monitor", "Keyboard",
                     "Mouse", "Headset", "Camera", "Printer", "Router"])
CATEGORIES = np.array(["Computers", "Accessories", "Audio", "Imaging", "Network"])
REGIONS = np.array(["North", "South", "East", "West", "Center"])
PAYMENTS = np.array(["Card", "Cash", "Transfer", "Wallet"])


def build_chunk(rng, start_id, n):
    """Build one chunk of n rows as a DataFrame."""
    quantity = rng.integers(1, 11, n)
    unit_price = np.round(rng.uniform(5, 2500, n), 2)
    return pd.DataFrame({
        "order_id": np.arange(start_id, start_id + n, dtype=np.int64),
        "order_date": pd.to_datetime(rng.integers(1_577_836_800, 1_767_225_600, n), unit="s"),
        "customer_id": "C" + pd.Series(rng.integers(10_000_000, 99_999_999, n)).astype(str),
        "product": rng.choice(PRODUCTS, n),
        "category": rng.choice(CATEGORIES, n),
        "region": rng.choice(REGIONS, n),
        "payment_method": rng.choice(PAYMENTS, n),
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": np.round(quantity * unit_price, 2),
    })


def main():
    parser = argparse.ArgumentParser(description="Generate the TP02 sales dataset.")
    parser.add_argument("--gb", type=float, default=6.0, help="target size in GB")
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    target_bytes = args.gb * 1024 ** 3
    rng = np.random.default_rng(42)

    rows = 0
    chunk = 0
    with open(CSV_FILE, "w", encoding="utf-8", newline="") as handle:
        while CSV_FILE.stat().st_size < target_bytes:
            df = build_chunk(rng, rows, ROWS_PER_CHUNK)
            df.to_csv(handle, header=(chunk == 0), index=False)
            handle.flush()
            rows += ROWS_PER_CHUNK
            chunk += 1
            size_gb = CSV_FILE.stat().st_size / 1024 ** 3
            print(f"chunk {chunk:>3} | rows={rows:>12,} | size={size_gb:.2f} GB")

    final_gb = CSV_FILE.stat().st_size / 1024 ** 3
    print(f"\nDone: {CSV_FILE}")
    print(f"{rows:,} rows, {final_gb:.2f} GB")


if __name__ == "__main__":
    main()
