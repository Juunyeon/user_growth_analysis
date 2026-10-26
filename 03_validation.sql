USE user_growth_portfolio;
SELECT 'visits' AS dataset,COUNT(*) AS row_count FROM raw_visits
UNION ALL SELECT 'orders',COUNT(*) FROM raw_orders
UNION ALL SELECT 'costs',COUNT(*) FROM raw_costs;
SELECT MIN(start_ts),MAX(start_ts),COUNT(DISTINCT uid) FROM raw_visits;
SELECT COUNT(*) AS invalid_duration FROM raw_visits WHERE end_ts<start_ts;
SELECT COUNT(*) AS unmatched_orders FROM raw_orders o
LEFT JOIN (SELECT DISTINCT uid FROM raw_visits) v ON o.uid=v.uid WHERE v.uid IS NULL;
SELECT COUNT(*) AS orders_outside_window,COALESCE(SUM(revenue),0) AS revenue
FROM raw_orders WHERE buy_ts < '2017-06-01' OR buy_ts >= '2018-06-01';
SELECT COUNT(*) AS users,SUM(order_count) AS linked_orders,SUM(revenue) AS linked_revenue
FROM v_user_acquisition;
SELECT source_id,dt,COUNT(*) AS row_count FROM raw_costs
GROUP BY source_id,dt HAVING COUNT(*)>1;
-- 未执行利润 ROI：缺乏毛利、退款、履约及完整运营成本。
