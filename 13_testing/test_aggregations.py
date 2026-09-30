def test_daily_zone_reconciliation(db):
    a=db.execute('SELECT SUM(scheduled_readings),SUM(missing_readings),SUM(successful_collections),SUM(missed_collections) FROM bin_daily_metrics').fetchone()
    b=db.execute('SELECT SUM(scheduled_readings),SUM(missing_readings),SUM(successful_collections),SUM(missed_collections) FROM zone_daily_metrics').fetchone()
    assert a==b and a[0]==4_380_000

def test_collection_and_vehicle_reconciliation(db):
    a=db.execute('SELECT COUNT(*), SUM(collected_kg) FROM collection_events').fetchone()
    b=db.execute('SELECT SUM(service_attempts),SUM(collected_kg_simulated) FROM route_daily_metrics').fetchone()
    c=db.execute('SELECT SUM(service_attempts),SUM(collected_kg_simulated) FROM vehicle_daily_metrics').fetchone()
    assert a[0]==b[0]==c[0]
    assert abs(a[1]-b[1])<.01 and abs(b[1]-c[1])<.01
