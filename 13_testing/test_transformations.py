from pathlib import Path
import csv,hashlib
ROOT=Path(__file__).resolve().parents[1]
def test_csv_to_parquet_sample_and_origin(db):
    p=ROOT/'03_data/synthetic/csv/readings_2026_01.csv'
    with p.open(newline='',encoding='utf-8') as f: first=next(csv.DictReader(f))
    row=db.execute('SELECT bin_id, fill_level_pct, collection_status, data_origin FROM fact_bin_readings WHERE reading_id=?',[int(first['reading_id'])]).fetchone()
    assert row[0]==int(first['bin_id']) and row[2:]==(first['collection_status'],'synthetic')
    assert abs(row[1]-float(first['fill_level_pct']))<.001 if first['fill_level_pct'] else row[1] is None

def test_collection_reset_mass_balance_sample(db):
    row=db.execute('''WITH x AS (
      SELECT bin_id, reading_id, inventory_l_true, arrivals_l_true, overflow_l_true, removed_l_true,
             LAG(inventory_l_true) OVER (PARTITION BY bin_id ORDER BY reading_id) AS prev_inventory
      FROM simulation_truth WHERE bin_id<=20)
      SELECT MAX(ABS(prev_inventory+arrivals_l_true-overflow_l_true-removed_l_true-inventory_l_true)),
             COUNT(*) FILTER (WHERE removed_l_true>0)
      FROM x WHERE prev_inventory IS NOT NULL''').fetchone()
    assert row[0]<.001 and row[1]>0

def test_timestamp_order_and_regular_schedule(db):
    row=db.execute('''WITH x AS (
      SELECT bin_id, timestamp_utc,
             LAG(timestamp_utc) OVER (PARTITION BY bin_id ORDER BY reading_id) AS previous_at
      FROM fact_bin_readings WHERE bin_id<=20)
      SELECT COUNT(*) FILTER (WHERE previous_at IS NOT NULL
                                   AND timestamp_utc-previous_at<>INTERVAL '2 hours'),
             COUNT(*) FROM x''').fetchone()
    assert row==(0,20*365*12)

def test_successful_collection_reduces_inventory(db):
    violations=db.execute('''SELECT COUNT(*) FROM simulation_truth t
      JOIN collection_events e ON t.reading_id=e.collection_id
      WHERE e.collection_status IN ('collected','partial')
        AND (t.removed_l_true<=0 OR t.inventory_l_true>=t.capacity_l)''').fetchone()[0]
    assert violations==0

def test_raw_snapshots_match_manifest():
    import csv
    m=ROOT/'02_research/acquisition_manifest.csv'
    with m.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            p=ROOT/row['local_path']
            assert p.exists() and p.stat().st_size==int(row['bytes'])
            digest=hashlib.sha256()
            with p.open('rb') as source:
                for block in iter(lambda:source.read(1024*1024),b''):
                    digest.update(block)
            assert digest.hexdigest()==row['sha256']
