-- BUSINESS PURPOSE: identify bins with frequent service and high gross fill demand.
SELECT d.city_id,d.city_name,d.bin_key,max(b.capacity_l) AS capacity_l,
 sum(d.successful_collections) AS annual_services,
 avg(d.arrivals_l_simulated/b.capacity_l*100) AS gross_capacity_pct_per_day,
 count(*) FILTER(WHERE d.overflow_l_simulated>0) AS overflow_days
FROM bin_daily_metrics d JOIN dim_bin b ON d.bin_key=b.bin_key AND d.city_id=b.city_id
WHERE ($city_id IS NULL OR d.city_id=$city_id)
GROUP BY d.city_id,d.city_name,d.bin_key HAVING sum(d.successful_collections)>0
ORDER BY d.city_id,annual_services DESC;
