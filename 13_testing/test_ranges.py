def test_sensor_and_truth_ranges(db):
    bad=db.execute('''SELECT COUNT(*) FROM fact_bin_readings WHERE
        (fill_level_pct IS NOT NULL AND (fill_level_pct<0 OR fill_level_pct>100))
        OR battery_pct<0 OR battery_pct>100
        OR (sensor_status='missing' AND fill_level_pct IS NOT NULL)
        OR (sensor_status<>'missing' AND fill_level_pct IS NULL)
        OR data_origin<>'synthetic' ''').fetchone()[0]
    assert bad==0
    bad_truth=db.execute('''SELECT COUNT(*) FROM simulation_truth WHERE
        arrivals_l_true<0 OR inventory_l_true<0 OR overflow_l_true<0
        OR removed_l_true<0 OR inventory_l_true>capacity_l+0.001''').fetchone()[0]
    assert bad_truth==0

def test_no_negative_route_proxy(db):
    assert db.execute('SELECT COUNT(*) FROM route_daily_metrics WHERE distance_km_assumed<0 OR collected_kg_simulated<0').fetchone()[0]==0
