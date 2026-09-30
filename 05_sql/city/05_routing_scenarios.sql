-- BUSINESS PURPOSE: compare each city's matched baseline/optimized pair; not raw city km rankings.
SELECT city_id,city_name,scenario,status,required_bins,bins_serviced,
 baseline_km,optimized_km,km_saved,distance_reduction_pct,
 optimized_km/nullif(bins_serviced,0) AS optimized_km_per_served_bin,
 travel_hours_saved,fuel_l_saved_assumed,fuel_cost_inr_saved_historical_proxy,
 tailpipe_co2_kg_saved_proxy,price_scope,data_origin
FROM route_scenarios WHERE ($city_id IS NULL OR city_id=$city_id)
ORDER BY city_id,scenario;
