"""Expansion gates, including independent Coimbatore routing and preservation checks."""
from pathlib import Path
import json,hashlib,math
import duckdb,pandas as pd,numpy as np,pytest
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'cities/CBE'

@pytest.fixture(scope='module')
def combined():
    c=duckdb.connect(str(ROOT/'03_data/processed/two_city/two_city.duckdb'),read_only=True)
    yield c
    c.close()

def test_city_keys_and_event_reconciliation(combined):
    c=combined
    assert c.execute('SELECT city_id,count(*) FROM fact_bin_readings GROUP BY city_id ORDER BY city_id').fetchall()==[('CBE',2190000),('CHN',4380000)]
    assert c.execute('SELECT count(*),count(DISTINCT reading_key) FROM fact_bin_readings').fetchone()==(6570000,6570000)
    assert c.execute('SELECT count(*),count(DISTINCT bin_key) FROM dim_bin').fetchone()==(1500,1500)
    assert c.execute('SELECT count(*),count(DISTINCT zone_key) FROM dim_zone').fetchone()==(300,300)
    assert c.execute('SELECT count(*) FROM dim_city').fetchone()[0]==2
    assert c.execute('SELECT sum(scheduled_readings) FROM bin_daily_metrics').fetchone()[0]==6570000
    assert c.execute('SELECT sum(scheduled_readings) FROM city_daily_metrics').fetchone()[0]==6570000

def test_city_foreign_keys_and_no_join_fanout(combined):
    c=combined
    assert c.execute('''SELECT count(*) FROM fact_bin_readings r JOIN dim_bin b ON r.bin_key=b.bin_key AND r.city_id=b.city_id JOIN dim_zone z ON r.zone_key=z.zone_key AND r.city_id=z.city_id JOIN dim_city c ON r.city_id=c.city_id''').fetchone()[0]==6570000
    for name in ['fact_collections','fact_routes','fact_vehicle_operations','fact_weather','bin_daily_metrics','zone_daily_metrics','route_scenarios','forecast_evaluation']:
        assert c.execute(f'SELECT count(*) FROM {name} x LEFT JOIN dim_city c ON x.city_id=c.city_id WHERE c.city_id IS NULL').fetchone()[0]==0
    assert c.execute('SELECT count(*) FROM fact_collections e LEFT JOIN dim_bin b ON e.bin_key=b.bin_key AND e.city_id=b.city_id WHERE b.bin_key IS NULL').fetchone()[0]==0

def test_ranges_nulls_coordinates_and_independent_generation(combined):
    c=combined
    assert c.execute("SELECT count(*) FROM fact_bin_readings WHERE city_id IS NULL OR reading_key IS NULL OR data_origin<>'synthetic' OR fill_level_pct NOT BETWEEN 0 AND 100 OR battery_pct NOT BETWEEN 0 AND 100 OR (fill_level_pct IS NULL)<>(sensor_status='missing')").fetchone()[0]==0
    assert c.execute("SELECT count(*) FROM dim_bin WHERE (city_id='CBE' AND (latitude NOT BETWEEN 10.8 AND 11.3 OR longitude NOT BETWEEN 76.7 AND 77.3)) OR (city_id='CHN' AND (latitude NOT BETWEEN 12.7 AND 13.5 OR longitude NOT BETWEEN 80 AND 80.5))").fetchone()[0]==0
    gen=json.loads((BASE/'03_data/synthetic/csv/generation_report.json').read_text());assert gen['seed']==20260924 and gen['rows']==2190000
    equal=c.execute("SELECT avg((a.fill_level_pct=b.fill_level_pct)::INT) FROM fact_bin_readings a JOIN fact_bin_readings b ON a.bin_id=b.bin_id AND a.timestamp_utc=b.timestamp_utc WHERE a.city_id='CHN' AND b.city_id='CBE' AND a.month='01' AND b.month='01'").fetchone()[0]
    assert equal<.5

def test_coimbatore_reset_order_and_mass_balance(combined):
    c=combined
    result=c.execute("""WITH x AS (SELECT *,lag(inventory_l_true) OVER(PARTITION BY bin_key ORDER BY timestamp_utc) AS previous,lag(timestamp_utc) OVER(PARTITION BY bin_key ORDER BY timestamp_utc) AS prev_time FROM simulation_truth WHERE city_id='CBE') SELECT max(abs(previous+arrivals_l_true-inventory_l_true-overflow_l_true-removed_l_true)),count(*) FILTER(WHERE prev_time IS NOT NULL AND timestamp_utc-prev_time<>INTERVAL '2 hours') FROM x WHERE previous IS NOT NULL""").fetchone()
    assert result[0]<.001 and result[1]==0
    assert c.execute("SELECT count(*) FROM simulation_truth t JOIN fact_collections e ON t.reading_key=e.collection_key WHERE t.city_id='CBE' AND e.collection_status IN ('collected','partial') AND (t.removed_l_true<=0 OR t.inventory_l_true>=t.capacity_l)").fetchone()[0]==0

def test_coimbatore_forecast_availability_and_metrics():
    fc=BASE/'09_forecasting/phase4';d=pd.read_csv(fc/'dispatch_forecasts.csv');card=json.loads((fc/'model_card.json').read_text());p=pd.read_parquet(fc/'test_predictions.parquet');e=pd.read_csv(fc/'forecast_evaluation.csv')
    assert len(d)==500 and d.bin_id.is_unique and set(d.city_id)=={'CBE'}
    assert 'target_fill_pct' not in d and (pd.to_datetime(d.last_sensor_utc)<=pd.to_datetime(d.issue_time_utc)).all()
    assert '100 bins' in card['bin_holdout']
    assert card['refit_target_end']=='2026-08-31' and card['test_target_start']=='2026-09-01'
    assert ((p.bin_id%5==0)==p.group.eq('unseen_bins')).all()
    for group,part in p.groupby('group'):
        observed=abs(part.prediction_pct-part.target_fill_pct).mean();reported=e[(e.split=='test')&(e['group']==group)&(e.model==card['selected_model'])].iloc[0].mae_pct_points
        assert math.isclose(observed,reported,rel_tol=1e-10)

def test_coimbatore_network_routes_constraints_and_impact():
    geo=BASE/'08_geospatial/phase4';opt=BASE/'10_optimization/phase4'
    loc=pd.read_csv(geo/'matrix_locations.csv');edges=pd.read_parquet(geo/'directed_edges.parquet');nodes=pd.read_parquet(geo/'road_nodes.parquet');paths=json.loads((geo/'matrix_paths.json').read_text());m=np.load(geo/'road_matrix.npz')
    assert loc.latitude.between(10.8,11.3).all() and loc.longitude.between(76.7,77.3).all()
    assert nodes.latitude.between(10.8,11.3).all() and nodes.longitude.between(76.7,77.3).all()
    lookup={(r.u,r.v):(r.length_m,r.travel_seconds_assumed) for r in edges.itertuples()}
    for key,path in paths.items():
        a,b=map(int,key.split(','));assert path[0]==loc.iloc[a].routing_node_id and path[-1]==loc.iloc[b].routing_node_id
        assert math.isclose(sum(lookup[x,y][0] for x,y in zip(path,path[1:])),m['distance_m'][a,b],abs_tol=1e-6)
        assert math.isclose(sum(lookup[x,y][1] for x,y in zip(path,path[1:])),m['travel_seconds_assumed'][a,b],abs_tol=1e-6)
    solutions=json.loads((opt/'route_solutions.json').read_text());s=pd.read_csv(opt/'scenario_comparison.csv').set_index('scenario')
    for name,solution in solutions.items():
        for method in ['baseline','optimized']:
            if method=='baseline' and solution['baseline_unserved']:continue
            visits=[x for r in solution[method] for x in r[1:-1]]
            assert sorted(visits)==sorted(solution['required_matrix_indices']) and len(visits)==len(set(visits))
            km=0
            for r in solution[method]:
                assert r[0]==r[-1]==0
                load=sum(loc.iloc[k].capacity_l for k in r[1:-1]);assert load<=12000 and load*.12<=5000
                travel=sum(m['travel_seconds_assumed'][a,b] for a,b in zip(r,r[1:]));assert travel+max(0,len(r)-2)*240+(900 if len(r)>2 else 0)<=28800
                km+=sum(m['distance_m'][a,b] for a,b in zip(r,r[1:]))/1000
            assert math.isclose(km,s.loc[name,method+'_km'],rel_tol=1e-10)
    feasible=s[s.status=='feasible'];assert np.allclose(feasible.km_saved,feasible.baseline_km-feasible.optimized_km)
    assert np.allclose(feasible.fuel_cost_inr_saved_historical_proxy,feasible.km_saved/4.5*92.39*feasible.fuel_price_multiplier)
    replay=pd.read_csv(opt/'counterfactual_bin_results.csv');assert np.allclose(replay.initial_l+replay.arrivals_l,replay.terminal_l+replay.overflow_l+replay.collected_l,atol=1e-5)

def test_preserved_chennai_outputs():
    receipt=json.loads((ROOT/'14_outputs/reports/city_expansion/chennai_preservation.json').read_text())
    amendment=json.loads((ROOT/'14_outputs/reports/final_audit/preservation_amendment.json').read_text())
    assert amendment['path']=='14_outputs/tables/phase3_sql/query_manifest.json'
    for record in receipt['files']:
        if record['path']==amendment['path']:
            assert record['sha256']==amendment['prior_sha256']
            record=amendment
        p=ROOT/record['path'];assert p.stat().st_size==record['bytes'],record['path']
        h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
        assert h.hexdigest()==record['sha256'],record['path']

def test_city_filter_reconciliation_and_exports(combined):
    path=ROOT/'14_outputs/tables/city_comparison'
    both=pd.read_csv(path/'01_city_comparison_BOTH.csv')
    for cid in ['CHN','CBE']:
        one=pd.read_csv(path/f'01_city_comparison_{cid}.csv');assert len(one)==1
        pd.testing.assert_frame_equal(both[both.city_id==cid].reset_index(drop=True),one)
    for name in ['dim_city','dim_bin','city_daily_metrics','fact_routes','forecast_evaluation','collection_priority','fact_weather']:
        d=pd.read_csv(ROOT/'12_powerbi/two_city_data'/f'{name}.csv');assert set(d.city_id)=={'CHN','CBE'}
    plan=(ROOT/'14_outputs/reports/city_expansion/city_partition_query_plan.txt').read_text(encoding='utf-8');assert 'Total Files Read: 1' in plan
