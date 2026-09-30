-- Phase 3 DuckDB business questions. ALL operational observations are synthetic.
-- Units: arrivals/overflow in litres; simulated mass = litres * assumed 0.12 kg/L.
-- Current-ward Census joins, measured route savings and observed Chennai claims are excluded.

-- query_id: 01_zone_generation
-- BUSINESS PURPOSE: Identify the highest simulated waste-generation burden, normalized
-- per hypothetical bin to avoid rewarding zones merely for having more bins.
WITH zone_year AS (
  SELECT zone_id, COUNT(*) AS observed_days, MAX(bins) AS bins,
         SUM(arrivals_l_simulated) * 0.12 AS generated_kg_simulated,
         SUM(arrivals_l_simulated) / SUM(bins) AS litres_per_bin_day,
         SUM(overflow_l_simulated) AS overflow_l_simulated
  FROM zone_daily_metrics
  WHERE service_date_local BETWEEN DATE '2026-01-01' AND DATE '2026-12-31'
  GROUP BY zone_id
  HAVING COUNT(*) >= 300
)
SELECT *, RANK() OVER (ORDER BY litres_per_bin_day DESC) AS per_bin_rank
FROM zone_year ORDER BY per_bin_rank, zone_id LIMIT 25;

-- query_id: 02_fastest_bins
-- BUSINESS PURPOSE: Locate hypothetical bins with high gross daily arrivals relative
-- to capacity; collection resets make observed fill slope a biased growth measure.
WITH bin_year AS (
  SELECT d.bin_id, d.zone_id, b.capacity_l, COUNT(*) AS days,
         SUM(d.arrivals_l_simulated) / COUNT(*) AS mean_arrival_l_day,
         100.0 * SUM(d.arrivals_l_simulated) / (COUNT(*) * b.capacity_l) AS gross_capacity_pct_day,
         QUANTILE_CONT(d.arrivals_l_simulated, 0.90) AS p90_arrival_l_day,
         AVG(d.mean_observed_fill_pct) AS mean_observed_fill_pct
  FROM bin_daily_metrics d JOIN dim_bin b USING (bin_id)
  GROUP BY d.bin_id, d.zone_id, b.capacity_l
  HAVING COUNT(*) >= 300
)
SELECT *, RANK() OVER (ORDER BY gross_capacity_pct_day DESC) AS fill_rate_rank
FROM bin_year ORDER BY fill_rate_rank, bin_id LIMIT 25;

-- query_id: 03_overflow_bins
-- BUSINESS PURPOSE: Prioritize bins with recurrent simulated physical overflow,
-- reporting both event-day frequency and volume instead of clipped sensor fill.
WITH risk AS (
  SELECT bin_id, zone_id, COUNT(*) AS days,
         COUNT(*) FILTER (WHERE overflow_l_simulated > 0) AS overflow_days,
         SUM(overflow_l_simulated) AS overflow_l_simulated,
         SUM(missed_collections) AS missed_attempts
  FROM bin_daily_metrics GROUP BY bin_id, zone_id
)
SELECT *, ROUND(100.0 * overflow_days / days, 2) AS overflow_day_pct,
       RANK() OVER (ORDER BY overflow_days DESC, overflow_l_simulated DESC) AS risk_rank
FROM risk WHERE overflow_days > 0 ORDER BY risk_rank, bin_id LIMIT 25;

-- query_id: 04_collection_timing
-- BUSINESS PURPOSE: Assess potential too-early/too-late service in the simulator.
-- Pre-service fill uses latent truth (post-service inventory + removed volume) and
-- is a diagnostic only; a live dispatch system would need a pre-service observation.
WITH attempts AS (
  SELECT e.zone_id, e.bin_id, e.collection_status,
         100.0 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l AS pre_service_fill_pct_true,
         t.overflow_l_true,
         CASE WHEN e.collection_status IN ('collected', 'partial')
                    AND 100.0 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l < 35
              THEN 1 ELSE 0 END AS early_success,
         CASE WHEN 100.0 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l >= 95
                    OR t.overflow_l_true > 0 THEN 1 ELSE 0 END AS near_full_or_overflow
  FROM collection_events e JOIN simulation_truth t ON e.collection_id = t.reading_id
)
SELECT zone_id, COUNT(*) AS attempts,
       SUM(early_success) AS early_successes_lt35_pct,
       SUM(near_full_or_overflow) AS late_risk_attempts_ge95_pct_or_overflow,
       COUNT(*) FILTER (WHERE collection_status = 'missed') AS missed_attempts,
       ROUND(100.0 * SUM(early_success) / COUNT(*), 2) AS early_attempt_pct,
       ROUND(100.0 * SUM(near_full_or_overflow) / COUNT(*), 2) AS late_risk_attempt_pct
FROM attempts GROUP BY zone_id HAVING COUNT(*) >= 100
ORDER BY late_risk_attempt_pct DESC, zone_id LIMIT 25;

-- query_id: 05_hourly_generation
-- BUSINESS PURPOSE: Characterize assumed intraday arrivals in local Chennai time.
-- These are generated latent arrivals, not an observed hourly waste meter.
WITH local_slots AS (
  SELECT EXTRACT(HOUR FROM timestamp_utc + INTERVAL '5 hours 30 minutes')::INTEGER AS local_hour,
         arrivals_l_true, overflow_l_true
  FROM simulation_truth WHERE year = 2026
)
SELECT local_hour, COUNT(*) AS scheduled_bin_slots,
       AVG(arrivals_l_true) AS mean_arrival_l_per_bin_slot,
       SUM(arrivals_l_true) * 0.12 AS generated_kg_simulated,
       COUNT(*) FILTER (WHERE overflow_l_true > 0) AS overflow_slots
FROM local_slots GROUP BY local_hour HAVING COUNT(*) > 0
ORDER BY mean_arrival_l_per_bin_slot DESC, local_hour;

-- query_id: 06_daily_trend
-- BUSINESS PURPOSE: Separate short-run demand changes from a seven-day moving
-- reference; LAG exposes changes without treating them as forecasts.
WITH city_day AS (
  SELECT service_date_local AS service_date, SUM(arrivals_l_simulated) * 0.12 AS generated_kg_simulated,
         SUM(overflow_l_simulated) AS overflow_l_simulated,
         SUM(successful_collections) AS successful_collections,
         SUM(missed_collections) AS missed_collections
  FROM zone_daily_metrics GROUP BY service_date_local
)
SELECT service_date, generated_kg_simulated, overflow_l_simulated,
       successful_collections, missed_collections,
       LAG(generated_kg_simulated) OVER (ORDER BY service_date) AS prior_day_kg,
       LEAD(generated_kg_simulated) OVER (ORDER BY service_date) AS next_day_kg,
       AVG(generated_kg_simulated) OVER (ORDER BY service_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS trailing_7day_kg
FROM city_day ORDER BY service_date;

-- query_id: 07_weekday_pattern
-- BUSINESS PURPOSE: Compare simulated daily generation and overflow by local
-- weekday; the weekend multiplier is a documented generator input.
WITH city_day AS (
  SELECT service_date_local AS service_date,
         SUM(arrivals_l_simulated) * 0.12 AS generated_kg_simulated,
         SUM(overflow_l_simulated) AS overflow_l_simulated
  FROM zone_daily_metrics GROUP BY service_date_local
)
SELECT DATE_PART('isodow', service_date) AS iso_weekday,
       CASE WHEN DATE_PART('isodow', service_date) >= 6 THEN 'weekend' ELSE 'weekday' END AS day_type,
       COUNT(*) AS days, AVG(generated_kg_simulated) AS mean_generated_kg_day,
       MEDIAN(generated_kg_simulated) AS median_generated_kg_day,
       AVG(overflow_l_simulated) AS mean_overflow_l_day
FROM city_day GROUP BY iso_weekday, day_type ORDER BY iso_weekday;

-- query_id: 08_service_frequency
-- BUSINESS PURPOSE: Show which hypothetical wards need the most successful
-- collections per bin-week, with missed attempts and overflow as guardrails.
SELECT zone_id, MAX(bins) AS bins, COUNT(*) AS days,
       SUM(successful_collections) AS successful_collections,
       SUM(missed_collections) AS missed_attempts,
       7.0 * SUM(successful_collections) / SUM(bins) AS collections_per_bin_week,
       SUM(overflow_l_simulated) / SUM(bins) AS overflow_l_per_bin_day
FROM zone_daily_metrics GROUP BY zone_id HAVING COUNT(*) >= 300
ORDER BY collections_per_bin_week DESC, zone_id LIMIT 25;

-- query_id: 09_route_proxy
-- BUSINESS PURPOSE: Screen low-stop vehicle-days, while explicitly avoiding an
-- efficiency claim: distance is mechanically 5 + 0.35 km per successful stop.
WITH daily AS (
  SELECT vehicle_id, service_date_local, successful_stops, missed_stops,
         collected_kg_simulated, distance_km_assumed,
         CASE WHEN successful_stops < 4 THEN 'low_stop_proxy' ELSE 'other' END AS proxy_flag,
         successful_stops / NULLIF(distance_km_assumed, 0) AS stops_per_assumed_km
  FROM route_daily_metrics WHERE distance_origin = 'assumption'
)
SELECT vehicle_id, COUNT(*) AS active_days,
       COUNT(*) FILTER (WHERE proxy_flag = 'low_stop_proxy') AS low_stop_days,
       AVG(successful_stops) AS mean_successful_stops_day,
       AVG(stops_per_assumed_km) AS mean_stops_per_assumed_km,
       SUM(collected_kg_simulated) AS collected_kg_simulated,
       SUM(distance_km_assumed) AS distance_km_assumed
FROM daily GROUP BY vehicle_id HAVING COUNT(*) >= 300
ORDER BY low_stop_days DESC, vehicle_id LIMIT 25;

-- query_id: 10_local_anomalies
-- BUSINESS PURPOSE: Flag unusually high zone-days relative to the prior 28
-- zone-days for investigation, not declare a real incident or cause.
WITH history AS (
  SELECT zone_id, service_date_local, arrivals_l_simulated,
         AVG(arrivals_l_simulated) OVER (
           PARTITION BY zone_id ORDER BY service_date_local
           ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS prior_28day_mean_l,
         STDDEV_SAMP(arrivals_l_simulated) OVER (
           PARTITION BY zone_id ORDER BY service_date_local
           ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS prior_28day_sd_l,
         COUNT(*) OVER (
           PARTITION BY zone_id ORDER BY service_date_local
           ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS history_days
  FROM zone_daily_metrics
), scored AS (
  SELECT *, (arrivals_l_simulated - prior_28day_mean_l)
                  / NULLIF(prior_28day_sd_l, 0) AS prior_window_z
  FROM history WHERE history_days = 28
)
SELECT zone_id, service_date_local, arrivals_l_simulated,
       prior_28day_mean_l, prior_window_z,
       CASE WHEN ABS(prior_window_z) >= 3 THEN 'investigate' ELSE 'within_reference' END AS review_flag
FROM scored WHERE ABS(prior_window_z) >= 3
ORDER BY ABS(prior_window_z) DESC, zone_id, service_date_local LIMIT 50;

-- query_id: 13_early_bins
-- BUSINESS PURPOSE: Find the few hypothetical bins with repeated low-fill
-- successful collection attempts. Uses latent pre-service truth for audit only.
WITH attempted AS (
  SELECT e.bin_id, e.zone_id, e.collection_status,
         100.0 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l AS pre_service_fill_pct_true
  FROM collection_events e JOIN simulation_truth t ON e.collection_id = t.reading_id
), flagged AS (
  SELECT bin_id, zone_id, COUNT(*) AS attempts,
         COUNT(*) FILTER (WHERE collection_status IN ('collected','partial')
                            AND pre_service_fill_pct_true < 35) AS early_successes_lt35_pct,
         MEDIAN(pre_service_fill_pct_true) AS median_pre_service_fill_pct_true
  FROM attempted GROUP BY bin_id, zone_id
  HAVING COUNT(*) FILTER (WHERE collection_status IN ('collected','partial')
                            AND pre_service_fill_pct_true < 35) > 0
)
SELECT *, RANK() OVER (ORDER BY early_successes_lt35_pct DESC) AS early_rank
FROM flagged ORDER BY early_rank, bin_id LIMIT 25;

-- query_id: 14_late_bins
-- BUSINESS PURPOSE: Identify hypothetical bins with the highest share of
-- near-full/overflow service attempts, with a minimum-attempt denominator.
WITH attempted AS (
  SELECT e.bin_id, e.zone_id, e.collection_status,
         CASE WHEN 100.0 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l >= 95
                    OR t.overflow_l_true > 0 THEN 1 ELSE 0 END AS late_risk
  FROM collection_events e JOIN simulation_truth t ON e.collection_id = t.reading_id
), summarized AS (
  SELECT bin_id, zone_id, COUNT(*) AS attempts, SUM(late_risk) AS late_risk_attempts,
         COUNT(*) FILTER (WHERE collection_status='missed') AS missed_attempts,
         100.0 * SUM(late_risk) / COUNT(*) AS late_risk_attempt_pct
  FROM attempted GROUP BY bin_id, zone_id HAVING COUNT(*) >= 100
)
SELECT *, RANK() OVER (ORDER BY late_risk_attempt_pct DESC) AS late_rank
FROM summarized ORDER BY late_rank, bin_id LIMIT 25;

-- query_id: 11_monthly_seasonality
-- BUSINESS PURPOSE: Compare the scenario's monthly demand and overflow after
-- normalizing for days/month. The cosine seasonality was specified, not learned.
WITH city_day AS (
  SELECT service_date_local AS service_date, SUM(arrivals_l_simulated) * 0.12 AS generated_kg_simulated,
         SUM(overflow_l_simulated) AS overflow_l_simulated,
         SUM(successful_collections) AS successful_collections
  FROM zone_daily_metrics GROUP BY service_date_local
)
SELECT DATE_TRUNC('month', service_date)::DATE AS service_month, COUNT(*) AS days,
       AVG(generated_kg_simulated) AS mean_generated_kg_day,
       AVG(overflow_l_simulated) AS mean_overflow_l_day,
       AVG(successful_collections) AS mean_successful_collections_day
FROM city_day GROUP BY service_month ORDER BY service_month;

-- query_id: 12_reconciliation
-- BUSINESS PURPOSE: Tie mart counts and litres back to the scheduled fact and
-- latent simulation truth before reporting any downstream result.
SELECT (SELECT COUNT(*) FROM fact_bin_readings) AS fact_scheduled_readings,
       (SELECT COUNT(*) FROM simulation_truth) AS truth_scheduled_readings,
       (SELECT SUM(scheduled_readings) FROM bin_daily_metrics) AS bin_mart_scheduled_readings,
       (SELECT SUM(scheduled_readings) FROM zone_daily_metrics) AS zone_mart_scheduled_readings,
       (SELECT COUNT(*) FROM collection_events) AS collection_attempts,
       (SELECT SUM(successful_collections + missed_collections) FROM bin_daily_metrics) AS bin_mart_attempts,
       (SELECT SUM(arrivals_l_true) FROM simulation_truth) AS truth_arrivals_l,
       (SELECT SUM(arrivals_l_simulated) FROM bin_daily_metrics) AS bin_mart_arrivals_l,
       (SELECT SUM(arrivals_l_simulated) FROM zone_daily_metrics) AS zone_mart_arrivals_l;
