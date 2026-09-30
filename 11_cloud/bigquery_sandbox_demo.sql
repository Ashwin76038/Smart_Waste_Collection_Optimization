-- BigQuery Sandbox demonstration. NOT EXECUTED in this project.
-- Create dataset smart_waste_demo in a no-billing Sandbox project in the console first.
-- Use the local file 11_cloud/zone_daily_sample.csv, and use the stated schema.
-- Replace YOUR_PROJECT_ID only after confirming Sandbox status.
CREATE TABLE `YOUR_PROJECT_ID.smart_waste_demo.zone_daily_sample` (
  zone_id STRING,
  service_date_local DATE,
  scheduled_readings INT64,
  received_readings INT64,
  missing_readings INT64,
  collected_kg_simulated FLOAT64,
  overflow_l_simulated FLOAT64,
  data_origin STRING
)
PARTITION BY service_date_local
CLUSTER BY zone_id;

-- The console upload may create the table itself with the same schema. Do not run
-- CREATE TABLE again if the upload flow already created it.
SELECT COUNT(*) AS rows,
       SUM(scheduled_readings) AS scheduled_readings,
       SUM(received_readings) AS received_readings,
       SUM(collected_kg_simulated) AS collected_kg_simulated
FROM `YOUR_PROJECT_ID.smart_waste_demo.zone_daily_sample`
WHERE service_date_local BETWEEN DATE '2026-01-01' AND DATE '2026-01-31';

SELECT zone_id, service_date_local, collected_kg_simulated,
       SUM(collected_kg_simulated) OVER
       (PARTITION BY zone_id ORDER BY service_date_local
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS trailing_7day_kg
FROM `YOUR_PROJECT_ID.smart_waste_demo.zone_daily_sample`
WHERE service_date_local BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'
ORDER BY zone_id, service_date_local;
