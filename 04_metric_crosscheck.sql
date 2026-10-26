USE user_growth_portfolio;
-- 独立用SQL核算最终日滚动活跃及全体成熟cohort留存，校对Python。
SELECT '2018-05-31' AS metric_date,
 COUNT(DISTINCT CASE WHEN start_ts >= '2018-05-31' THEN uid END) AS dau,
 COUNT(DISTINCT CASE WHEN start_ts >= '2018-05-25' THEN uid END) AS wau,
 COUNT(DISTINCT CASE WHEN start_ts >= '2018-05-02' THEN uid END) AS mau
FROM raw_visits WHERE start_ts >= '2017-06-01' AND start_ts < '2018-06-01';
WITH user_first AS (
 SELECT uid,DATE(MIN(start_ts)) AS first_date FROM raw_visits
 WHERE start_ts >= '2017-06-01' AND start_ts < '2018-06-01' GROUP BY uid
), user_day AS (
 SELECT DISTINCT uid,DATE(start_ts) AS visit_date FROM raw_visits
 WHERE start_ts >= '2017-06-01' AND start_ts < '2018-06-01'
), horizons AS (SELECT 1 AS n UNION ALL SELECT 7 UNION ALL SELECT 30)
SELECT h.n, COUNT(*) AS eligible, COUNT(d.uid) AS returned,
 COUNT(d.uid)/COUNT(*) AS retention
FROM user_first f CROSS JOIN horizons h
LEFT JOIN user_day d ON f.uid=d.uid AND d.visit_date=DATE_ADD(f.first_date, INTERVAL h.n DAY)
WHERE DATE_ADD(f.first_date,INTERVAL h.n DAY)<'2018-06-01'
GROUP BY h.n ORDER BY h.n;
