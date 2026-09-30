-- BUSINESS PURPOSE: rank service demand WITHIN each city; ward geography vintages differ.
WITH workload AS (
 SELECT city_id,city_name,zone_key,sum(arrivals_l_simulated)/sum(bins) AS litres_per_bin_day,
 sum(successful_collections)*1.0/sum(bins) AS services_per_bin_day
 FROM zone_daily_metrics WHERE ($city_id IS NULL OR city_id=$city_id)
 GROUP BY ALL HAVING sum(bins)>=365
)
SELECT *,rank() OVER(PARTITION BY city_id ORDER BY litres_per_bin_day DESC) AS within_city_rank
FROM workload ORDER BY city_id,within_city_rank;
