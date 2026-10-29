-- A replay can be folded only when its event identity AND entire business
-- payload agree. Different events with the same line key are not auto-replays.
CREATE VIEW event_payloads AS
SELECT DISTINCT event_id, order_id, line_id, sku, unit, ordered_qty, promise_at
FROM anomaly_lines;
CREATE VIEW event_conflicts AS
SELECT event_id FROM event_payloads GROUP BY event_id HAVING COUNT(*) > 1;
CREATE VIEW confirmed_replay_rows AS
SELECT a.* FROM anomaly_lines a
WHERE NOT EXISTS (SELECT 1 FROM event_conflicts c WHERE c.event_id = a.event_id)
  AND a.source_row_id <> (
    SELECT MIN(b.source_row_id) FROM anomaly_lines b WHERE b.event_id = a.event_id
  );
CREATE VIEW canonical_lines AS
SELECT a.* FROM anomaly_lines a
WHERE NOT EXISTS (SELECT 1 FROM event_conflicts c WHERE c.event_id = a.event_id)
  AND a.source_row_id = (
    SELECT MIN(b.source_row_id) FROM anomaly_lines b WHERE b.event_id = a.event_id
  );
CREATE VIEW line_key_conflicts AS
SELECT line_id FROM canonical_lines GROUP BY line_id HAVING COUNT(*) > 1;
CREATE VIEW blocked_orders AS
SELECT DISTINCT order_id FROM canonical_lines
WHERE ordered_qty <= 0 OR ordered_qty IS NULL
   OR promise_at IS NULL OR julianday(promise_at) IS NULL
UNION
SELECT DISTINCT order_id FROM canonical_lines
WHERE line_id IN (SELECT line_id FROM line_key_conflicts)
UNION
SELECT DISTINCT order_id FROM anomaly_lines
WHERE event_id IN (SELECT event_id FROM event_conflicts);
CREATE VIEW orphan_receipts AS
SELECT r.* FROM anomaly_receipts r
WHERE NOT EXISTS (SELECT 1 FROM anomaly_lines l WHERE l.line_id = r.line_id);

-- The 4-order candidate list is frozen before corrupting the copy. It is NOT
-- an inferred complete due-order population from the dirty promise dates.
CREATE VIEW diagnostic_lines AS
SELECT l.* FROM canonical_lines l JOIN candidate_orders c USING(order_id)
WHERE NOT EXISTS (SELECT 1 FROM blocked_orders b WHERE b.order_id = l.order_id)
  AND julianday(l.promise_at) <= julianday((SELECT as_of FROM config));
CREATE VIEW diagnostic_line_result AS
SELECT l.source_row_id, l.origin_row_id, l.order_id, l.line_id,
       l.ordered_qty,
       COALESCE(SUM(CASE WHEN r.qualified = 1
                         AND julianday(r.accepted_at) <= julianday(l.promise_at)
                         AND r.accepted_qty >= 0
                    THEN r.accepted_qty ELSE 0 END), 0) AS timely_qty,
       MIN(l.ordered_qty, COALESCE(SUM(CASE WHEN r.qualified = 1
                         AND julianday(r.accepted_at) <= julianday(l.promise_at)
                         AND r.accepted_qty >= 0
                    THEN r.accepted_qty ELSE 0 END), 0)) AS credited_qty
FROM diagnostic_lines l LEFT JOIN anomaly_receipts r USING(line_id)
GROUP BY l.source_row_id, l.origin_row_id, l.order_id, l.line_id, l.ordered_qty;

-- A left join starts from expected observation slots, not the received rows.
-- A NULL value and an absent row remain different observable states.
CREATE VIEW inventory_audit AS
SELECT e.snapshot_date, e.store_id, e.sku, s.source_row_id, s.origin_row_id,
       s.inventory,
       CASE WHEN s.source_row_id IS NULL THEN 'MISSING_ROW'
            WHEN s.inventory IS NULL THEN 'NULL_VALUE'
            WHEN s.inventory < 0 THEN 'NEGATIVE_VALUE'
            WHEN s.inventory = 0 THEN 'ZERO_OBSERVED'
            ELSE 'POSITIVE_OBSERVED' END AS state
FROM expected_slots e LEFT JOIN anomaly_snapshots s
  USING(snapshot_date, store_id, sku);
