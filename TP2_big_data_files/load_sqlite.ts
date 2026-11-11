/**
 * Load the TP02 sales CSV into SQLite so you can query it with plain SQL.
 * Uses Bun's built-in SQLite (no install needed).
 *
 *   bun run load_sqlite.ts --limit 3000000          # fast trial run
 *   bun run load_sqlite.ts                          # full 6 GB, ~6 min
 *
 * Options:
 *   --csv   path to CSV        (default: data/sales_6gb.csv)
 *   --db    output .db file    (default: data/sales.db)
 *   --limit max rows to load   (default: all)
 */
import { Database } from "bun:sqlite";

const arg = (name: string, fallback: string) => {
  const i = process.argv.indexOf(`--${name}`);
  return i === -1 ? fallback : process.argv[i + 1];
};

const csvPath = arg("csv", "data/sales_6gb.csv");
const dbPath = arg("db", "data/sales.db");
const limit = Number(arg("limit", "0")) || Infinity;
const BATCH = 100_000;

const db = new Database(dbPath, { create: true });
db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA synchronous = OFF");

db.exec(`
  CREATE TABLE IF NOT EXISTS sales (
    order_id       INTEGER PRIMARY KEY,
    order_date     TEXT NOT NULL,   -- 'YYYY-MM-DD HH:MM:SS', ISO so substr() works
    customer_id    TEXT NOT NULL,
    product        TEXT NOT NULL,
    category       TEXT NOT NULL,
    region         TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    quantity       INTEGER NOT NULL,
    unit_price     REAL NOT NULL,
    total_amount   REAL NOT NULL,
    month          TEXT NOT NULL,   -- 'YYYY-MM', derived once at load time
    day            TEXT NOT NULL    -- 'YYYY-MM-DD'
  ) WITHOUT ROWID;
`);

const insert = db.prepare(`
  INSERT OR IGNORE INTO sales
  (order_id, order_date, customer_id, product, category, region,
   payment_method, quantity, unit_price, total_amount, month, day)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const file = Bun.file(csvPath);
const size = file.size;
if (!size) throw new Error(`missing or empty: ${csvPath}`);

const reader = file.stream().getReader();
const decoder = new TextDecoder();
let rest = "";
let rows = 0;
let headerSkipped = false;
const started = Date.now();

db.exec("BEGIN");
try {
  while (rows < limit) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = rest + decoder.decode(value, { stream: true });
    const lines = text.split("\n");
    rest = lines.pop() ?? "";

    for (const line of lines) {
      if (!line) continue;
      if (!headerSkipped) { headerSkipped = true; continue; }

      const c = line.split(",");
      insert.run(
        Number(c[0]), c[1], c[2], c[3], c[4], c[5], c[6],
        Number(c[7]), Number(c[8]), Number(c[9]),
        c[1].slice(0, 7), c[1].slice(0, 10),
      );
      rows++;
      if (rows % BATCH === 0) {
        db.exec("COMMIT");
        db.exec("BEGIN");
        const pct = ((rows / 75_000_000) * 100).toFixed(1);
        console.log(`${rows.toLocaleString()} rows | ${pct}% | ${((Date.now() - started) / 1000).toFixed(0)}s`);
      }
      if (rows >= limit) break;
    }
  }
  db.exec("COMMIT");
} catch (err) {
  db.exec("ROLLBACK");
  throw err;
}

db.exec("CREATE INDEX IF NOT EXISTS idx_sales_month ON sales(month)");
db.exec("CREATE INDEX IF NOT EXISTS idx_sales_price ON sales(unit_price)");
db.exec("ANALYZE");

const count = db.query("SELECT COUNT(*) AS n FROM sales").get() as { n: number };
console.log(`\ndone: ${dbPath}`);
console.log(`${count.n.toLocaleString()} rows in ${((Date.now() - started) / 1000).toFixed(0)}s`);
db.close();
