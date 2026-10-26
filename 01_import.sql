-- MySQL 8.0；独立数据库，原始表不删除重复行；首次运行。
CREATE DATABASE IF NOT EXISTS user_growth_portfolio CHARACTER SET utf8mb4;
USE user_growth_portfolio;
CREATE TABLE IF NOT EXISTS raw_visits (
 row_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 device VARCHAR(32), end_ts DATETIME, source_id INT, start_ts DATETIME,
 uid VARCHAR(32), INDEX ix_visit_user_time(uid,start_ts), INDEX ix_visit_time(start_ts)
);
CREATE TABLE IF NOT EXISTS raw_orders (
 row_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 buy_ts DATETIME, revenue DECIMAL(18,2), uid VARCHAR(32),
 INDEX ix_order_user_time(uid,buy_ts)
);
CREATE TABLE IF NOT EXISTS raw_costs (
 row_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 source_id INT, dt DATE, costs DECIMAL(18,2), INDEX ix_cost_source_date(source_id,dt)
);
-- 由 run_mysql.py 替换 ${RAW_DIR}；LOCAL 只在本次受控导入连接启用。
-- 导入器发现原始表非空即停止，防止重复导入；不自动清空已有数据。
LOAD DATA LOCAL INFILE '${RAW_DIR}/visits_log_us.csv' INTO TABLE raw_visits
 CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
 LINES TERMINATED BY '\n' IGNORE 1 LINES
 (device,@end_ts,source_id,@start_ts,@uid)
 SET end_ts=STR_TO_DATE(@end_ts,'%Y-%m-%d %H:%i:%s'),
 start_ts=STR_TO_DATE(@start_ts,'%Y-%m-%d %H:%i:%s'), uid=TRIM(TRAILING '\r' FROM @uid);
LOAD DATA LOCAL INFILE '${RAW_DIR}/orders_log_us.csv' INTO TABLE raw_orders
 CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
 LINES TERMINATED BY '\n' IGNORE 1 LINES
 (@buy_ts,revenue,@uid)
 SET buy_ts=STR_TO_DATE(@buy_ts,'%Y-%m-%d %H:%i:%s'), uid=TRIM(TRAILING '\r' FROM @uid);
LOAD DATA LOCAL INFILE '${RAW_DIR}/costs_us.csv' INTO TABLE raw_costs
 CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
 LINES TERMINATED BY '\n' IGNORE 1 LINES
 (source_id,@dt,@costs)
 SET dt=STR_TO_DATE(@dt,'%Y-%m-%d'), costs=TRIM(TRAILING '\r' FROM @costs);
