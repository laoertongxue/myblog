-- Only run by run.py in a fresh in-memory SQLite database.
CREATE TABLE config(as_of TEXT NOT NULL);
INSERT INTO config VALUES ('2026-10-21T18:00:00+07:00');
CREATE TABLE candidate_orders(order_id TEXT PRIMARY KEY);
CREATE TABLE expected_slots(snapshot_date TEXT, store_id TEXT, sku TEXT,
  PRIMARY KEY(snapshot_date, store_id, sku));
CREATE TABLE original_lines(source_row_id TEXT PRIMARY KEY, origin_row_id TEXT,
  event_id TEXT, order_id TEXT, line_id TEXT, sku TEXT, unit TEXT,
  ordered_qty REAL, promise_at TEXT);
CREATE TABLE anomaly_lines AS SELECT * FROM original_lines WHERE 0;
CREATE TABLE original_receipts(source_row_id TEXT PRIMARY KEY, origin_row_id TEXT,
  event_id TEXT, line_id TEXT, accepted_qty REAL, accepted_at TEXT, qualified INTEGER);
CREATE TABLE anomaly_receipts AS SELECT * FROM original_receipts WHERE 0;
CREATE TABLE original_snapshots(source_row_id TEXT PRIMARY KEY, origin_row_id TEXT,
  snapshot_date TEXT, store_id TEXT, sku TEXT, inventory REAL);
CREATE TABLE anomaly_snapshots AS SELECT * FROM original_snapshots WHERE 0;
