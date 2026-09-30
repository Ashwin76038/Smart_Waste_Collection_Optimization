-- PREPARED ONLY: no cloud execution. Upload two_city_daily_upload.csv as a bounded sample.
-- Replace YOUR_PROJECT.YOUR_DATASET after confirming BigQuery Sandbox without billing.
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.YOUR_DATASET.city_daily_metrics` (
 city_id STRING, city_name STRING, service_date_local DATE, bins INT64,
 generated_l FLOAT64, overflow_l FLOAT64, successful_collections INT64,
 missed_collections INT64, collected_kg FLOAT64, scheduled_readings INT64,
 received_readings INT64, fill_sum_pct FLOAT64, mean_fill_pct FLOAT64,
 overflow_slots INT64, overflow_slot_pct FLOAT64, generated_l_per_bin_day FLOAT64,
 collections_per_bin_day FLOAT64, data_origin STRING
) PARTITION BY service_date_local CLUSTER BY city_id;
-- After upload: expect two rows of 365; grand total 730.
SELECT city_id, COUNT(*) AS city_days
FROM `YOUR_PROJECT.YOUR_DATASET.city_daily_metrics`
GROUP BY city_id;
-- Parameter city_id is CHN or CBE. Compare result with the local query exports.
SELECT city_id, SUM(generated_l)/SUM(bins) AS generated_l_per_bin_day,
 SUM(fill_sum_pct)/SUM(received_readings) AS average_fill_pct,
 100*SUM(overflow_slots)/SUM(scheduled_readings) AS overflow_slot_pct
FROM `YOUR_PROJECT.YOUR_DATASET.city_daily_metrics`
WHERE service_date_local BETWEEN DATE '2026-01-01' AND DATE '2026-12-31'
 AND city_id=@city_id
GROUP BY city_id;
