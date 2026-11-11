/** Query the practice DB: bun run sql.ts "SELECT ..." */
import { Database } from "bun:sqlite";

const sql = process.argv.slice(2).join(" ").trim();
if (!sql) {
  console.log('usage: bun run sql.ts "SELECT month, COUNT(*) FROM sales GROUP BY 1"');
  process.exit(1);
}

const db = new Database("data/practice.db", { readonly: true });
const rows = db.query(sql).all() as Record<string, unknown>[];

if (rows.length === 0) {
  console.log("(no rows)");
  process.exit(0);
}

const cols = Object.keys(rows[0]!);
const cell = (v: unknown) => (v === null ? "NULL" : String(v));
const widths = cols.map((c) => Math.max(c.length, ...rows.map((r) => cell(r[c]).length)));
const pad = (s: string, w: number) => s + " ".repeat(Math.max(0, w - s.length));
const line = (xs: string[]) => xs.map((x, i) => pad(x, widths[i]!)).join("  ");

console.log(line(cols));
console.log(line(widths.map((w) => "-".repeat(w))));
for (const r of rows) console.log(line(cols.map((c) => cell(r[c]))));
console.log(`\n${rows.length.toLocaleString()} row(s)`);
