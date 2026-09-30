def test_readings_truth_one_to_one(db):
    row=db.execute('''SELECT COUNT(*), COUNT(DISTINCT r.reading_id)
                      FROM fact_bin_readings r JOIN simulation_truth t USING (reading_id)''').fetchone()
    assert row==(4_380_000,4_380_000)

def test_daily_grain(db):
    row=db.execute('SELECT COUNT(*), COUNT(DISTINCT (bin_id,service_date_local)), SUM(scheduled_readings) FROM bin_daily_metrics').fetchone()
    assert row==(365_000,365_000,4_380_000)
