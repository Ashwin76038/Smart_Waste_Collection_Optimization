-- BUSINESS PURPOSE: compare normalized SIMULATION workloads, never municipal performance.
-- city_id parameter is NULL for both, CHN or CBE for independent filtering.
WITH daily AS (
 SELECT city_id,city_name,max(bins) AS bin_count,count(*) AS days,
 sum(scheduled_readings) AS scheduled_readings,sum(received_readings) AS received_readings,
 sum(fill_sum_pct)/sum(received_readings) AS average_observed_fill_pct,
 sum(generated_l) AS generated_l,sum(generated_l)/sum(bins) AS generated_l_per_bin_day,
 100.0*sum(overflow_slots)/sum(scheduled_readings) AS overflow_slot_pct,
 sum(overflow_l) AS overflow_l,sum(successful_collections) AS successful_collections,
 sum(successful_collections)*1.0/sum(bins) AS collections_per_bin_day,
 sum(collected_kg)/nullif(sum(successful_collections),0) AS collected_kg_per_success
 FROM city_daily_metrics WHERE ($city_id IS NULL OR city_id=$city_id) GROUP BY city_id,city_name
), timing AS (
 SELECT city_id,count(*) AS attempts,
 count(*) FILTER(WHERE collection_status IN ('collected','partial') AND pre_service_fill_pct<35) AS early_successes,
 count(*) FILTER(WHERE pre_service_fill_pct>=95 OR overflow_at_attempt) AS late_risk_attempts
 FROM collection_diagnostics GROUP BY city_id
)
SELECT d.*,t.attempts,t.early_successes,100.0*t.early_successes/d.successful_collections AS early_success_pct,
100.0*t.late_risk_attempts/t.attempts AS late_risk_attempt_pct,'synthetic' AS data_origin,
'Different seeded assumptions; normalized scenario comparison, not empirical city effect' AS interpretation
FROM daily d JOIN timing t USING(city_id) ORDER BY city_id;
