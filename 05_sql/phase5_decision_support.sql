-- BUSINESS PURPOSE: identify within-city wards for a field audit using
-- synthetic overflow litres per bin-day. Do not compare ward polygons/vintages
-- across cities or treat these as observed municipal hotspot rates.
WITH ward_days AS (
 SELECT city_id,zone_key,COUNT(*) AS observed_days,
        SUM(bins) AS bin_days,SUM(arrivals_l_simulated) AS generated_l,
        SUM(overflow_l_simulated) AS overflow_l,
        SUM(successful_collections) AS completed
 FROM zone_daily_metrics GROUP BY city_id,zone_key
), dispatch AS (
 SELECT city_id,zone_key,COUNT(*) FILTER(WHERE required) AS required_bins,
        COUNT(*) FILTER(WHERE NOT network_accessible) AS access_review_bins
 FROM collection_priority GROUP BY city_id,zone_key
), ranked AS (
 SELECT z.city_id,z.zone_key,z.observed_days,z.bin_days,
        z.generated_l/z.bin_days AS generated_l_per_bin_day,
        z.overflow_l/z.bin_days AS overflow_l_per_bin_day,
        z.completed/z.bin_days AS completed_per_bin_day,
        d.required_bins,d.access_review_bins,
        RANK() OVER(PARTITION BY z.city_id ORDER BY z.overflow_l/z.bin_days DESC) AS city_overflow_rank
 FROM ward_days z LEFT JOIN dispatch d USING(city_id,zone_key)
)
SELECT r.*,w.boundary_version,w.source_id,w.data_origin AS boundary_origin
FROM ranked r JOIN dim_zone w USING(city_id,zone_key)
WHERE city_overflow_rank<=5 ORDER BY city_id,city_overflow_rank,zone_key;

-- BUSINESS PURPOSE: compare dispatch thresholds in a matched pilot, preserving
-- feasibility and the isolated spill tradeoff rather than ranking raw route km.
SELECT s.city_id,s.scenario,s.status,s.required_bins,s.bins_serviced,
       s.baseline_km,s.optimized_km,s.km_saved,s.distance_reduction_pct,
       o.overflow_l_avoided_modelled,
       s.fuel_l_saved_assumed,s.fuel_cost_inr_saved_historical_proxy,s.price_scope
FROM route_scenarios s LEFT JOIN overflow_comparison o USING(city_id,scenario_key)
WHERE s.scenario IN ('base_3_trucks','trigger_70','trigger_90')
ORDER BY s.city_id,s.scenario;
