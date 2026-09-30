def test_reading_primary_key_and_count(db):
    row=db.execute('SELECT COUNT(*), COUNT(DISTINCT reading_id), COUNT(DISTINCT bin_id) FROM fact_bin_readings').fetchone()
    assert row==(4_380_000,4_380_000,1000)

def test_dimension_keys(db):
    assert db.execute('SELECT COUNT(*)=COUNT(DISTINCT bin_id) FROM dim_bin').fetchone()[0]
    assert db.execute('SELECT COUNT(*)=COUNT(DISTINCT zone_id) FROM dim_zone_ward').fetchone()[0]
