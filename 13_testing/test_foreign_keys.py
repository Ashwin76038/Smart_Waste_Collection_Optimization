def test_readings_reference_bins(db):
    assert db.execute('SELECT COUNT(*) FROM fact_bin_readings r ANTI JOIN dim_bin b ON r.bin_id=b.bin_id').fetchone()[0]==0

def test_bins_reference_wards(db):
    assert db.execute('SELECT COUNT(*) FROM dim_bin b ANTI JOIN dim_zone_ward z ON b.zone_id=z.zone_id').fetchone()[0]==0

def test_collections_reference_readings(db):
    assert db.execute('SELECT COUNT(*) FROM collection_events c ANTI JOIN fact_bin_readings r ON c.collection_id=r.reading_id').fetchone()[0]==0
