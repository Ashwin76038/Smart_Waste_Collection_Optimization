-- BUSINESS PURPOSE: distinguish conservative reserved volume from actual collected load.
SELECT city_id,city_name,scenario,method,vehicle_key,bins,volume_utilization_pct,payload_utilization_pct,
 duration_seconds/3600 AS shift_hours,distance_m/1000 AS route_km,
 CASE WHEN bins=0 THEN 'unused' WHEN volume_utilization_pct>=90 THEN 'near reserved volume limit' ELSE 'reserve available' END AS reserve_status
FROM fact_routes WHERE ($city_id IS NULL OR city_id=$city_id)
ORDER BY city_id,scenario,method,vehicle_key;
