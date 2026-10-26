USE user_growth_portfolio;
-- 日期范围采用半开区间；访问按开始时间归属，不拆分跨夜会话。
CREATE OR REPLACE VIEW v_visits AS
 SELECT row_id,uid,device,source_id,start_ts,end_ts FROM raw_visits;
CREATE OR REPLACE VIEW v_orders AS
 SELECT row_id,uid,buy_ts,revenue FROM raw_orders;
CREATE OR REPLACE VIEW v_costs AS
 SELECT row_id,source_id,dt,costs FROM raw_costs;
-- 先在各表聚合，再按用户关联，防止访问×订单放大收入。
-- 同时刻首访按 source_id、device、row_id 排序；只是确定性归因规则。
CREATE OR REPLACE VIEW v_user_acquisition AS
WITH ranked_visits AS (
 SELECT *, ROW_NUMBER() OVER(PARTITION BY uid ORDER BY start_ts,source_id,device,row_id) AS rn
 FROM raw_visits WHERE start_ts >= '2017-06-01' AND start_ts < '2018-06-01'
), acquisition AS (
 SELECT uid,start_ts AS first_visit,source_id AS first_source,device AS first_device
 FROM ranked_visits WHERE rn=1
), visit_summary AS (
 SELECT uid,MAX(start_ts) AS last_visit,COUNT(*) AS visit_count
 FROM ranked_visits GROUP BY uid
), order_summary AS (
 SELECT a.uid,MIN(o.buy_ts) AS first_purchase,COUNT(*) AS order_count,SUM(o.revenue) AS revenue
 FROM acquisition a JOIN raw_orders o ON a.uid=o.uid
 AND o.buy_ts>=a.first_visit AND o.buy_ts < '2018-06-01'
 GROUP BY a.uid
)
SELECT a.*,v.last_visit,v.visit_count,o.first_purchase,
 COALESCE(o.order_count,0) AS order_count,COALESCE(o.revenue,0) AS revenue
FROM acquisition a JOIN visit_summary v ON a.uid=v.uid
LEFT JOIN order_summary o ON a.uid=o.uid;
