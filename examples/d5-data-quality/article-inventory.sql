-- Complete query: start from expected combinations, keep missing distinct from NULL.
WITH inventory_audit AS (
SELECT e.snapshot_date, e.store_id, e.sku, s.source_row_id, s.origin_row_id,
       s.inventory,
       CASE WHEN s.source_row_id IS NULL THEN 'MISSING_ROW'
            WHEN s.inventory IS NULL THEN 'NULL_VALUE'
            WHEN s.inventory < 0 THEN 'NEGATIVE_VALUE'
            WHEN s.inventory = 0 THEN 'ZERO_OBSERVED'
            ELSE 'POSITIVE_OBSERVED' END AS state
FROM expected_slots e LEFT JOIN anomaly_snapshots s
  USING(snapshot_date, store_id, sku)
)
SELECT COUNT(*) AS expected_slots,
       COUNT(source_row_id) AS reported_rows,
       SUM(CASE WHEN state = 'MISSING_ROW' THEN 1 ELSE 0 END) AS missing_rows,
       SUM(CASE WHEN state = 'NULL_VALUE' THEN 1 ELSE 0 END) AS null_values,
       SUM(CASE WHEN inventory >= 0 THEN 1 ELSE 0 END) AS valid_rows,
       SUM(CASE WHEN inventory = 0 THEN 1 ELSE 0 END) AS zero_rows,
       1.0 * SUM(CASE WHEN inventory >= 0 THEN 1 ELSE 0 END)
           / NULLIF(COUNT(*), 0) AS coverage,
       1.0 * SUM(CASE WHEN inventory = 0 THEN 1 ELSE 0 END)
           / NULLIF(SUM(CASE WHEN inventory >= 0 THEN 1 ELSE 0 END), 0)
           AS observed_zero_rate
FROM inventory_audit;
