-- Diagnostic subset only. BLOCKED means do not publish a full-scope KPI.
SELECT
  (SELECT COUNT(*) FROM candidate_orders) AS candidate_orders,
  COUNT(DISTINCT order_id) AS evaluated_orders,
  SUM(credited_qty) AS credited_qty,
  SUM(ordered_qty) AS planned_qty,
  1.0 * SUM(credited_qty) / NULLIF(SUM(ordered_qty), 0) AS fill_rate,
  CASE WHEN EXISTS (SELECT 1 FROM blocked_orders)
         OR EXISTS (SELECT 1 FROM orphan_receipts)
         OR EXISTS (SELECT 1 FROM event_conflicts)
         OR EXISTS (SELECT 1 FROM line_key_conflicts)
       THEN 'BLOCKED' ELSE 'READY' END AS formal_status
FROM diagnostic_line_result;
