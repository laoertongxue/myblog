-- SQLite；所有时间均为 Asia/Shanghai 本地时间，固定到秒。
-- 参数由 runner 创建的 params 表提供，起点包含、终点不包含。
-- 原始输入先经 runner 校验；冲突身份、孤儿引用等问题阻断整次运行。
CREATE VIEW eligible_orders AS
SELECT o.* FROM orders o, params p
WHERE o.status='valid' AND o.due_at >= p.start_at
  AND o.due_at < p.end_at AND o.due_at <= p.as_of;

-- 相同 event_id 且全部字段相同的重复上报已校验，DISTINCT 只消除重传。
-- 不同 event_id 的合法分批验收保留，先汇总到订单行再关联。
CREATE VIEW receipt_unique AS SELECT DISTINCT * FROM receipts;
CREATE VIEW line_on_time AS
SELECT l.scenario,l.line_id,l.order_id,l.sku_id,l.ordered_qty,
       COALESCE(SUM(CASE WHEN r.received_at<=o.due_at
                          AND r.received_at<=p.as_of THEN r.qualified_qty ELSE 0 END),0) AS on_time_qty
FROM lines l JOIN eligible_orders o
  ON l.scenario=o.scenario AND l.order_id=o.order_id
CROSS JOIN params p
LEFT JOIN receipt_unique r ON r.scenario=l.scenario AND r.line_id=l.line_id
GROUP BY l.scenario,l.line_id,l.order_id,l.sku_id,l.ordered_qty;

-- 保留封顶量和行达标标记，方便逐行审计。
CREATE VIEW line_result AS
SELECT *,MIN(on_time_qty,ordered_qty) AS credited_qty,
 CASE WHEN on_time_qty>=ordered_qty THEN 1 ELSE 0 END AS passed
FROM line_on_time;

-- 1. 整单 OTIF：全部有效行达到承诺数量，订单才记 1。
CREATE VIEW order_result AS
SELECT o.scenario,o.site_id,o.order_id,
       MIN(CASE WHEN l.on_time_qty>=l.ordered_qty THEN 1 ELSE 0 END) AS passed
FROM eligible_orders o JOIN line_result l
 ON o.scenario=l.scenario AND o.order_id=l.order_id
GROUP BY o.scenario,o.site_id,o.order_id;
CREATE VIEW metric_otif AS
SELECT s.scenario,s.site_id,COALESCE(SUM(o.passed),0) AS numerator,
 COUNT(o.order_id) AS denominator,
 1.0*SUM(o.passed)/NULLIF(COUNT(o.order_id),0) AS ratio
FROM sites s LEFT JOIN order_result o
 ON s.scenario=o.scenario AND s.site_id=o.site_id
GROUP BY s.scenario,s.site_id;

-- 2. 数量满足率：逐行封顶，再按 SKU 和单位汇总；不能跨单位相加。
CREATE VIEW metric_fill AS
SELECT s.scenario,s.sku_id,s.unit,
 COALESCE(SUM(MIN(l.on_time_qty,l.ordered_qty)),0) AS numerator,
 COALESCE(SUM(l.ordered_qty),0) AS denominator,
 1.0*SUM(MIN(l.on_time_qty,l.ordered_qty))/NULLIF(SUM(l.ordered_qty),0) AS ratio
FROM skus s LEFT JOIN line_result l
 ON s.scenario=l.scenario AND s.sku_id=l.sku_id
GROUP BY s.scenario,s.sku_id,s.unit;

-- 3. 快照缺货率：零库存 / 有效快照；负值与未知值不进入分母。
-- expected_grid 明确每日 18:00 一次，共 14 天；缺行另计，不能补零。
CREATE VIEW snapshot_result AS
SELECT g.*,s.on_hand,
 CASE WHEN s.snapshot_at IS NULL THEN 'missing'
      WHEN s.on_hand IS NULL THEN 'unknown'
      WHEN s.on_hand<0 THEN 'negative' ELSE 'valid' END AS quality
FROM expected_grid g LEFT JOIN snapshots s
 ON g.scenario=s.scenario AND g.site_id=s.site_id
 AND g.sku_id=s.sku_id AND g.snapshot_at=s.snapshot_at;
CREATE VIEW metric_stockout AS
SELECT scenario,site_id,sku_id,
 SUM(CASE WHEN quality='valid' AND on_hand=0 THEN 1 ELSE 0 END) AS numerator,
 SUM(CASE WHEN quality='valid' THEN 1 ELSE 0 END) AS denominator,
 1.0*SUM(CASE WHEN quality='valid' AND on_hand=0 THEN 1 ELSE 0 END)
 /NULLIF(SUM(CASE WHEN quality='valid' THEN 1 ELSE 0 END),0) AS ratio,
 COUNT(*) AS expected_count,
 SUM(CASE WHEN quality='missing' THEN 1 ELSE 0 END) AS missing_count,
 SUM(CASE WHEN quality='unknown' THEN 1 ELSE 0 END) AS unknown_count,
 SUM(CASE WHEN quality='negative' THEN 1 ELSE 0 END) AS negative_count,
 1.0*SUM(CASE WHEN quality='valid' THEN 1 ELSE 0 END)/COUNT(*) AS coverage
FROM snapshot_result GROUP BY scenario,site_id,sku_id;
