-- BUSINESS PURPOSE: evaluate models fitted independently, with compatible horizon/time splits.
SELECT city_id,city_name,split,"group",model,n,mae_pct_points,rmse_pct_points,wape_pct,near_full_recall
FROM forecast_evaluation WHERE ($city_id IS NULL OR city_id=$city_id)
ORDER BY city_id,split,"group",mae_pct_points;
