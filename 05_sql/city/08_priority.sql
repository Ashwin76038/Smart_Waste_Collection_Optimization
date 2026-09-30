-- BUSINESS PURPOSE: surface all due bins and access/out-of-pilot exceptions by city.
SELECT city_id,city_name,bin_key,zone_key,current_fill_pct,prediction_pct,risk_upper_pct,
 reasons,dispatch_status,priority_rank
FROM collection_priority WHERE required AND ($city_id IS NULL OR city_id=$city_id)
ORDER BY city_id,priority_rank;
