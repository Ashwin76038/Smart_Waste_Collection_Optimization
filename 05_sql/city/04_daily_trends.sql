-- BUSINESS PURPOSE: monitor city-specific changes without mixing cities in windows.
SELECT city_id,city_name,service_date_local,mean_fill_pct,overflow_slot_pct,generated_l_per_bin_day,
 lag(generated_l_per_bin_day) OVER(PARTITION BY city_id ORDER BY service_date_local) AS previous_day_l_per_bin,
 avg(generated_l_per_bin_day) OVER(PARTITION BY city_id ORDER BY service_date_local ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling7_l_per_bin
FROM city_daily_metrics WHERE ($city_id IS NULL OR city_id=$city_id)
ORDER BY city_id,service_date_local;
