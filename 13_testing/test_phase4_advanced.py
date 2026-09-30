"""Independent saved-output reconciliations and consequential boundary tests."""
from pathlib import Path
import sys,json,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'06_python/scripts'))
from phase4_common import CFG,GEO,FC,OPT
import pandas as pd,numpy as np
from phase4_priority import prioritize
from phase4_counterfactual import replay

def test_forecast_dispatch_availability_and_holdout(db):
    d=pd.read_parquet(FC/'dispatch_forecasts.parquet');card=json.loads((FC/'model_card.json').read_text())
    assert len(d)==1000 and d.bin_id.is_unique and 'target_fill_pct' not in d
    assert (d.last_sensor_utc<=d.issue_time_utc).all()
    assert (d.last_service_utc<=d.issue_time_utc).all()
    assert ((d.target_time_utc-d.issue_time_utc).dt.total_seconds()==72000).all()
    assert pd.Timestamp(card['refit_target_end'])<d.issue_time_utc.min()
    assert not set(card['features'])&{'demand_factor','arrivals_l_true','inventory_l_true','target_fill_pct','bin_id','zone_id'}
    observed=db.execute("SELECT bin_id,arg_max(fill_level_pct,timestamp_utc) AS fill FROM fact_bin_readings WHERE service_date_local='2026-09-23' AND timestamp_utc<='2026-09-23 02:30:00' AND sensor_status='ok' GROUP BY bin_id").df()
    m=d.merge(observed,on='bin_id',validate='one_to_one');assert np.allclose(m.current_fill_pct,m['fill'])
    p=pd.read_parquet(FC/'test_predictions.parquet')
    assert ((p.bin_id%5==0)==p.group.eq('unseen_bins')).all()
    assert p.target_time_utc.min()>=pd.Timestamp('2026-08-31 22:30:00')

def test_forecast_metrics_recompute():
    p=pd.read_parquet(FC/'test_predictions.parquet');e=pd.read_csv(FC/'forecast_evaluation.csv');card=json.loads((FC/'model_card.json').read_text())
    for group,g in p.groupby('group'):
        r=e[(e.split=='test')&(e.group==group)&(e.model==card['selected_model'])].iloc[0]
        error=(g.prediction_pct-g.target_fill_pct).to_numpy()
        assert math.isclose(np.mean(abs(error)),r.mae_pct_points,rel_tol=1e-10)
        assert math.isclose(np.sqrt(np.mean(error**2)),r.rmse_pct_points,rel_tol=1e-10)
    coverage=((p.target_fill_pct>=p.lower90_pct)&(p.target_fill_pct<=p.upper90_pct)).mean()
    assert math.isclose(coverage,card['test_interval_coverage90'])

def test_priority_monotonicity_and_boundary():
    f=pd.read_csv(OPT/'collection_priority.csv')
    selected=[]
    for threshold in [70,80,90]:selected.append(set(prioritize(f,threshold).query('required').bin_id))
    assert selected[2]<=selected[1]<=selected[0]
    assert set(f.loc[f.required&~f.network_accessible,'dispatch_status'])=={'access_review'}
    x=f.head(4).copy();x['current_fill_pct']=[80,79,10,np.nan];x['upper90_pct']=[80,79,10,np.nan];x['hours_since_collection']=[2,2,48,2];x['sensor_age_hours']=0
    p=prioritize(x).set_index('bin_id')
    assert p.loc[x.iloc[0].bin_id,'required'] and not p.loc[x.iloc[1].bin_id,'required']
    assert p.loc[x.iloc[2].bin_id,'gap_trigger'] and p.loc[x.iloc[3].bin_id,'telemetry_trigger']

def test_spatial_keys_and_coverage():
    s=pd.read_parquet(GEO/'bin_spatial_features.parquet');loc=pd.read_csv(GEO/'matrix_locations.csv')
    assert len(s)==1000 and s.bin_id.is_unique and s.assigned_ward_matches_polygon.all()
    assert s.in_routing_pilot.sum()==60 and len(loc)==61 and loc.bin_id.is_unique
    assert s.loc[s.in_routing_pilot,'snap_m'].le(CFG['max_snap_m']).all()
    assert s.latitude.between(12,14).all() and s.longitude.between(79,81).all()

def test_directed_matrix_paths_independent_reconciliation():
    edges=pd.read_parquet(GEO/'directed_edges.parquet');paths=json.loads((GEO/'matrix_paths.json').read_text());loc=pd.read_csv(GEO/'matrix_locations.csv');m=np.load(GEO/'road_matrix.npz')
    lookup={(int(r.u),int(r.v)):(r.length_m,r.travel_seconds_assumed) for r in edges.itertuples()}
    assert not edges.duplicated(['u','v']).any() and edges.length_m.gt(0).all()
    for key,ids in paths.items():
        a,b=map(int,key.split(','));assert ids[0]==loc.iloc[a].routing_node_id and ids[-1]==loc.iloc[b].routing_node_id
        segments=[lookup[(u,v)] for u,v in zip(ids,ids[1:])]
        assert math.isclose(sum(x[0] for x in segments),m['distance_m'][a,b],abs_tol=1e-6)
        assert math.isclose(sum(x[1] for x in segments),m['travel_seconds_assumed'][a,b],abs_tol=1e-6)
    assert np.all(np.isfinite(m['distance_m'])) and np.all(m['distance_m']>=0)
    assert np.count_nonzero(abs(m['distance_m']-m['distance_m'].T)>1)>0

def test_routes_capacity_shift_depot_visits_and_published_totals():
    solutions=json.loads((OPT/'route_solutions.json').read_text());loc=pd.read_csv(GEO/'matrix_locations.csv');m=np.load(GEO/'road_matrix.npz');published=pd.read_csv(OPT/'scenario_comparison.csv').set_index('scenario')
    for name,solution in solutions.items():
        for method in ['baseline','optimized']:
            routes=solution[method];visits=[x for r in routes for x in r[1:-1]]
            assert sorted(visits)==sorted(solution['required_matrix_indices']) and len(visits)==len(set(visits))
            distance=duration=0
            for r in routes:
                assert r[0]==r[-1]==0
                load=sum(loc.iloc[x].capacity_l for x in r[1:-1])
                assert load<=CFG['truck_volume_l_assumed'] and load*CFG['density_kg_per_l_assumed']<=CFG['truck_payload_kg_assumed']
                drive=sum(m['travel_seconds_assumed'][a,b] for a,b in zip(r,r[1:]));service=(len(r)-2)*4*60+(15*60 if len(r)>2 else 0)
                assert drive+service<=480*60
                duration+=drive+service;distance+=sum(m['distance_m'][a,b] for a,b in zip(r,r[1:]))
            assert math.isclose(distance/1000,published.loc[name,method+'_km'])
            assert math.isclose(duration/3600,published.loc[name,method+'_vehicle_hours'])

def test_infeasible_scenarios_and_impact_factors():
    s=pd.read_csv(OPT/'scenario_comparison.csv')
    bad=s[s.status=='proven_infeasible_capacity']
    assert {'one_truck','two_trucks','truck_unavailable'}<=set(bad.scenario)
    assert (bad.full_capacity_l_required>bad.vehicles_available*CFG['truck_volume_l_assumed']).all()
    assert bad.km_saved.isna().all()
    good=s[s.status=='feasible'];saved=good.baseline_km-good.optimized_km
    assert np.allclose(saved,good.km_saved)
    assert np.allclose(saved/4.5*92.39*good.fuel_price_multiplier,good.fuel_cost_inr_saved_historical_proxy)
    assert np.allclose(saved/4.5*2.689,good.tailpipe_co2_kg_saved_proxy)
    assert abs(10.180/3.785411784-CFG['co2_kg_per_l_proxy'])<.001

def test_counterfactual_mass_balance_and_changed_trajectories():
    d=pd.read_csv(OPT/'counterfactual_bin_results.csv')
    assert np.allclose(d.initial_l+d.arrivals_l,d.terminal_l+d.overflow_l+d.collected_l,atol=1e-5)
    assert d.terminal_l.between(0,d.capacity_l+1e-6).all() and d.overflow_l.ge(0).all()
    assert d.groupby(['scenario','method']).size().eq(60).all()
    assert replay(100,100,[100],[0])==(100,5,95)
    assert replay(100,100,[100],[60])==(55,50,95)
    x=d[d.scenario=='base_3_trucks'].pivot(index='bin_id',columns='method',values='overflow_l')
    assert (abs(x.baseline-x.optimized)>1e-6).any()
