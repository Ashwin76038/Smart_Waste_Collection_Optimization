"""Export a small, auditable Power BI star model from the two-city DuckDB.

The source database and prior phase artifacts are read-only. This script writes
only 12_powerbi/phase5_model and its own QA receipt.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import duckdb
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'12_powerbi/phase5_model'
OUT.mkdir(parents=True,exist_ok=True)
DB=ROOT/'03_data/processed/two_city/two_city.duckdb'

QUERIES={
'dim_city':'''SELECT city_id,city_name,district,state,latitude,longitude,population_source,operational_data_origin
 FROM dim_city ORDER BY city_id''',
'dim_date':'''SELECT CAST(date AS DATE) AS service_date,year(date) AS calendar_year,month(date) AS month_number,
 strftime(date,'%B') AS month_name,year(date)*100+month(date) AS year_month_sort,dayofweek(date) AS weekday_sunday_zero,
 CASE WHEN dayofweek(date) IN (0,6) THEN TRUE ELSE FALSE END AS weekend
 FROM dim_date WHERE year(date)=2026 ORDER BY date''',
'dim_zone':'''SELECT zone_key,city_id,city_name,zone_id,
 city_name||' ward '||zone_id AS ward_label,admin_zone_name,boundary_version,source_id,data_origin,
 (min_lat+max_lat)/2 AS map_latitude,(min_lon+max_lon)/2 AS map_longitude
 FROM dim_zone ORDER BY city_id,zone_id''',
'dim_bin':'''SELECT bin_key,city_id,city_name,zone_key,zone_id,
 city_name||' ward '||zone_id AS ward_label,capacity_l,latitude,longitude,
 coordinate_origin,data_origin,source_id
 FROM dim_bin ORDER BY city_id,bin_id''',
'dim_scenario':'''SELECT scenario_key,city_id,scenario,vehicles_available,trigger_pct,demand_multiplier,
 fuel_price_multiplier,status,price_scope,
 CASE WHEN scenario='base_3_trucks' THEN TRUE ELSE FALSE END AS base_scenario
 FROM route_scenarios ORDER BY city_id,scenario''',
'fact_city_day':'''SELECT city_id,CAST(service_date_local AS DATE) AS service_date,bins,generated_l,overflow_l,
 successful_collections,missed_collections,collected_kg,scheduled_readings,received_readings,
 fill_sum_pct,overflow_slots,data_origin FROM city_daily_metrics ORDER BY city_id,service_date''',
'fact_bin_day':'''SELECT bin_key,CAST(service_date_local AS DATE) AS service_date,scheduled_readings,received_readings,
 mean_observed_fill_pct*received_readings AS fill_sum_pct,max_observed_fill_pct,
 CASE WHEN mean_observed_fill_pct IS NULL THEN 'Missing'
      WHEN mean_observed_fill_pct<20 THEN '0–19%'
      WHEN mean_observed_fill_pct<40 THEN '20–39%'
      WHEN mean_observed_fill_pct<60 THEN '40–59%'
      WHEN mean_observed_fill_pct<80 THEN '60–79%'
      ELSE '80–100%' END AS mean_fill_band,
 CASE WHEN mean_observed_fill_pct IS NULL THEN 6
      WHEN mean_observed_fill_pct<20 THEN 1 WHEN mean_observed_fill_pct<40 THEN 2
      WHEN mean_observed_fill_pct<60 THEN 3 WHEN mean_observed_fill_pct<80 THEN 4 ELSE 5 END AS mean_fill_band_sort,
 arrivals_l_simulated AS generated_l,overflow_l_simulated AS overflow_l,
 (overflow_l_simulated>0)::INT AS overflow_day_count,collected_kg_simulated AS collected_kg,
 successful_collections,missed_collections,data_origin
 FROM bin_daily_metrics ORDER BY bin_key,service_date''',
'fact_zone_day':'''SELECT zone_key,CAST(service_date_local AS DATE) AS service_date,bins,scheduled_readings,
 received_readings,arrivals_l_simulated AS generated_l,overflow_l_simulated AS overflow_l,
 collected_kg_simulated AS collected_kg,successful_collections,missed_collections,data_origin
 FROM zone_daily_metrics ORDER BY zone_key,service_date''',
'fact_collection_attempt':'''SELECT collection_key,bin_key,CAST(service_date_local AS DATE) AS service_date,
 attempted_at_utc,collection_status,collected_kg,pre_service_fill_pct,
 (collection_status IN ('collected','partial'))::INT AS successful_attempt_count,
 (collection_status IN ('collected','partial') AND pre_service_fill_pct<35)::INT AS early_success_count,
 (pre_service_fill_pct>=95 OR overflow_at_attempt)::INT AS late_risk_attempt_count,
 data_origin
 FROM collection_diagnostics ORDER BY collection_key''',
'fact_dispatch_snapshot':'''SELECT bin_key,CAST(issue_date AS DATE) AS issue_date,CAST(target_date AS DATE) AS target_date,
 current_fill_pct,prediction_pct,upper90_pct,required,forecast_trigger,network_accessible,
 in_routing_pilot,dispatch_status,priority_rank,tier,reasons,trigger_pct,data_origin
 FROM collection_priority ORDER BY bin_key''',
'fact_route_scenario':'''SELECT scenario_key,required_bins,bins_serviced,baseline_complete,baseline_km,
 optimized_km,km_saved,distance_reduction_pct,travel_hours_saved,vehicle_hours_saved,
 fuel_l_saved_assumed,fuel_cost_inr_saved_historical_proxy,tailpipe_co2_kg_saved_proxy,
 full_capacity_l_required,distance_origin,optimality,reason,data_origin
 FROM route_scenarios ORDER BY scenario_key''',
'fact_truck_route':'''SELECT route_key,scenario_key,method,vehicle,bins,distance_m/1000 AS distance_km,
 travel_seconds/60 AS travel_minutes,load_l,duration_seconds/60 AS route_minutes,
 load_kg_assumed,volume_utilization_pct,payload_utilization_pct,data_origin
 FROM fact_routes ORDER BY route_key''',
'fact_forecast_score':'''SELECT city_id,split,"group" AS evaluation_group,model,n,mae_pct_points,
 rmse_pct_points,wape_pct,near_full_recall FROM forecast_evaluation ORDER BY city_id,split,evaluation_group,model''',
'fact_counterfactual':'''SELECT scenario_key,baseline_overflow_l,optimized_overflow_l,
 overflow_l_avoided_modelled,scope,data_origin FROM overflow_comparison ORDER BY scenario_key'''
}

KEYS={'dim_city':['city_id'],'dim_date':['service_date'],'dim_zone':['zone_key'],'dim_bin':['bin_key'],
      'dim_scenario':['scenario_key'],'fact_city_day':['city_id','service_date'],
      'fact_bin_day':['bin_key','service_date'],'fact_zone_day':['zone_key','service_date'],
      'fact_collection_attempt':['collection_key'],'fact_dispatch_snapshot':['bin_key'],
      'fact_route_scenario':['scenario_key'],'fact_truck_route':['route_key'],
      'fact_forecast_score':['city_id','split','evaluation_group','model'],
      'fact_counterfactual':['scenario_key']}

def close(a,b,atol=1e-3):
    return bool(np.isclose(float(a),float(b),rtol=1e-7,atol=atol))

def run():
    c=duckdb.connect(str(DB),read_only=True)
    frames={}
    rows={}
    for name,query in QUERIES.items():
        frame=c.execute(query).df()
        assert not frame.duplicated(KEYS[name]).any(),f'duplicate grain {name}'
        frame.to_csv(OUT/(name+'.csv'),index=False,date_format='%Y-%m-%d')
        frames[name]=frame;rows[name]=len(frame)
    assert rows=={'dim_city':2,'dim_date':365,'dim_zone':300,'dim_bin':1500,'dim_scenario':18,
                  'fact_city_day':730,'fact_bin_day':547500,'fact_zone_day':109135,
                  'fact_collection_attempt':322675,'fact_dispatch_snapshot':1500,
                  'fact_route_scenario':18,'fact_truck_route':72,'fact_forecast_score':30,
                  'fact_counterfactual':8},rows
    # Every dimension link must preserve the child row count, including the
    # scenario facts. Date joins are intentionally only on 2026 operational facts.
    links=[('dim_city','city_id','dim_bin','city_id'),('dim_city','city_id','dim_zone','city_id'),
           ('dim_city','city_id','dim_scenario','city_id'),('dim_city','city_id','fact_city_day','city_id'),
           ('dim_city','city_id','fact_forecast_score','city_id'),
           ('dim_date','service_date','fact_city_day','service_date'),
           ('dim_date','service_date','fact_bin_day','service_date'),
           ('dim_date','service_date','fact_zone_day','service_date'),
           ('dim_date','service_date','fact_collection_attempt','service_date'),
           ('dim_bin','bin_key','fact_bin_day','bin_key'),
           ('dim_bin','bin_key','fact_collection_attempt','bin_key'),
           ('dim_bin','bin_key','fact_dispatch_snapshot','bin_key'),
           ('dim_zone','zone_key','fact_zone_day','zone_key'),
           ('dim_scenario','scenario_key','fact_route_scenario','scenario_key'),
           ('dim_scenario','scenario_key','fact_truck_route','scenario_key'),
           ('dim_scenario','scenario_key','fact_counterfactual','scenario_key')]
    for parent,pk,child,fk in links:
        if not frames[child][fk].isin(frames[parent][pk]).all():raise AssertionError(f'orphan {parent}->{child}')
    # Reconcile DuckDB source SQL with independent Pandas on exported CSVs.
    daily=pd.read_csv(OUT/'fact_city_day.csv');collection=pd.read_csv(OUT/'fact_collection_attempt.csv')
    routes=pd.read_csv(OUT/'fact_route_scenario.csv');scenario=pd.read_csv(OUT/'dim_scenario.csv')
    truck=pd.read_csv(OUT/'fact_truck_route.csv');dispatch=pd.read_csv(OUT/'fact_dispatch_snapshot.csv')
    scores=pd.read_csv(OUT/'fact_forecast_score.csv');bin_day=pd.read_csv(OUT/'fact_bin_day.csv')
    counterfactual=pd.read_csv(OUT/'fact_counterfactual.csv')
    counterfactual=counterfactual.merge(scenario[['scenario_key','city_id','scenario']],on='scenario_key',validate='one_to_one')
    citybin=pd.read_csv(OUT/'dim_bin.csv');geo=bin_day.merge(citybin[['bin_key','city_id']],on='bin_key',validate='many_to_one')
    merged=routes.merge(scenario[['scenario_key','city_id','scenario']],on='scenario_key',validate='one_to_one')
    truck=truck.merge(scenario[['scenario_key','city_id','scenario']],on='scenario_key',validate='many_to_one')
    dispatch=dispatch.merge(citybin[['bin_key','city_id']],on='bin_key',validate='one_to_one')
    tests=[]
    for cid in ['CHN','CBE']:
        d=daily.loc[daily.city_id==cid];g=geo.loc[geo.city_id==cid]
        co=collection.merge(citybin[['bin_key','city_id']],on='bin_key',validate='many_to_one')
        co=co.loc[co.city_id==cid]
        di=dispatch.loc[dispatch.city_id==cid]
        sc=merged.loc[(merged.city_id==cid)&(merged.scenario=='base_3_trucks')].iloc[0]
        tr=truck.loc[(truck.city_id==cid)&(truck.scenario=='base_3_trucks')]
        optimized_tr=tr.loc[tr.method=='optimized']
        spill=counterfactual.loc[(counterfactual.city_id==cid)&(counterfactual.scenario=='base_3_trucks')].iloc[0]
        score=scores.loc[(scores.city_id==cid)&(scores.split=='test')&(scores.evaluation_group=='known_bins')&(scores.model=='ridge')].iloc[0]
        checks={
          'bins':(len(citybin[citybin.city_id==cid]),c.execute('SELECT count(*) FROM dim_bin WHERE city_id=?',[cid]).fetchone()[0],0),
          'collected_kg':(co.collected_kg.sum(),c.execute('SELECT sum(collected_kg) FROM collection_diagnostics WHERE city_id=?',[cid]).fetchone()[0],.01),
          'daily_collected_kg':(d.collected_kg.sum(),c.execute('SELECT sum(collected_kg) FROM city_daily_metrics WHERE city_id=?',[cid]).fetchone()[0],.01),
          'fill_pct':(d.fill_sum_pct.sum()/d.received_readings.sum(),c.execute('SELECT sum(fill_sum_pct)/sum(received_readings) FROM city_daily_metrics WHERE city_id=?',[cid]).fetchone()[0],1e-7),
          'overflow_slot_pct':(100*d.overflow_slots.sum()/d.scheduled_readings.sum(),c.execute('SELECT 100*sum(overflow_slots)/sum(scheduled_readings) FROM city_daily_metrics WHERE city_id=?',[cid]).fetchone()[0],1e-7),
          'generated_l_per_bin_day':(d.generated_l.sum()/d.bins.sum(),c.execute('SELECT sum(generated_l)/sum(bins) FROM city_daily_metrics WHERE city_id=?',[cid]).fetchone()[0],1e-6),
          'overflow_days':(g.overflow_day_count.sum(),c.execute('SELECT count(*) FROM bin_daily_metrics WHERE city_id=? AND overflow_l_simulated>0',[cid]).fetchone()[0],0),
          'completed_collections':(co.successful_attempt_count.sum(),c.execute("SELECT count(*) FROM collection_diagnostics WHERE city_id=? AND collection_status IN ('collected','partial')",[cid]).fetchone()[0],0),
          'early_success_pct':(100*co.early_success_count.sum()/co.successful_attempt_count.sum(),c.execute("SELECT 100.0*count(*) FILTER(WHERE collection_status IN ('collected','partial') AND pre_service_fill_pct<35)/nullif(count(*) FILTER(WHERE collection_status IN ('collected','partial')),0) FROM collection_diagnostics WHERE city_id=?",[cid]).fetchone()[0],1e-7),
          'late_risk_attempt_pct':(100*co.late_risk_attempt_count.sum()/len(co),c.execute("SELECT 100.0*count(*) FILTER(WHERE pre_service_fill_pct>=95 OR overflow_at_attempt)/count(*) FROM collection_diagnostics WHERE city_id=?",[cid]).fetchone()[0],1e-7),
          'required_bins':(di.required.sum(),c.execute('SELECT count(*) FROM collection_priority WHERE city_id=? AND required',[cid]).fetchone()[0],0),
          'high_priority_bins':(len(di[(di.required)&(di.tier==1)]),c.execute('SELECT count(*) FROM collection_priority WHERE city_id=? AND required AND tier=1',[cid]).fetchone()[0],0),
          'forecast_trigger_bins':(di.forecast_trigger.sum(),c.execute('SELECT count(*) FROM collection_priority WHERE city_id=? AND forecast_trigger',[cid]).fetchone()[0],0),
          'baseline_km':(sc.baseline_km,c.execute("SELECT baseline_km FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'optimized_km':(sc.optimized_km,c.execute("SELECT optimized_km FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'saved_km':(sc.km_saved,c.execute("SELECT km_saved FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'distance_reduction_pct':(100*(sc.baseline_km-sc.optimized_km)/sc.baseline_km,c.execute("SELECT distance_reduction_pct FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'pilot_bins_serviced':(sc.bins_serviced,c.execute("SELECT bins_serviced FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],0),
          'optimized_truck_km':(tr.loc[tr.method=='optimized','distance_km'].sum(),sc.optimized_km,1e-6),
          'reserved_truck_capacity_pct':(100*optimized_tr.load_l.sum()/(12000*len(optimized_tr)),c.execute("SELECT 100.0*sum(load_l)/(12000*count(*)) FROM fact_routes WHERE city_id=? AND scenario='base_3_trucks' AND method='optimized'",[cid]).fetchone()[0],1e-7),
          'fuel_saved_l':(sc.fuel_l_saved_assumed,c.execute("SELECT fuel_l_saved_assumed FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'fuel_cost_saved_inr_proxy':(sc.fuel_cost_inr_saved_historical_proxy,c.execute("SELECT fuel_cost_inr_saved_historical_proxy FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'travel_minutes_saved':(60*sc.travel_hours_saved,c.execute("SELECT 60*travel_hours_saved FROM route_scenarios WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'modeled_spill_avoided_l':(spill.overflow_l_avoided_modelled,c.execute("SELECT overflow_l_avoided_modelled FROM overflow_comparison WHERE city_id=? AND scenario='base_3_trucks'",[cid]).fetchone()[0],1e-6),
          'forecast_known_test_mae_pp':(score.mae_pct_points,c.execute("SELECT mae_pct_points FROM forecast_evaluation WHERE city_id=? AND split='test' AND \"group\"='known_bins' AND model='ridge'",[cid]).fetchone()[0],1e-6),
          'forecast_near_full_recall_pct':(100*score.near_full_recall,c.execute("SELECT 100*near_full_recall FROM forecast_evaluation WHERE city_id=? AND split='test' AND \"group\"='known_bins' AND model='ridge'",[cid]).fetchone()[0],1e-6)}
        for k,(py,sql,tol) in checks.items():
            tests.append({'city_id':cid,'metric':k,'python_export_value':float(py),'duckdb_source_value':float(sql),'absolute_difference':abs(float(py)-float(sql)),'absolute_tolerance':tol,'relative_tolerance':1e-7,'effective_tolerance':tol+1e-7*abs(float(sql)),'tolerance':tol,'passed':close(py,sql,tol)})
    # Cross-grain collection masses should match up to float32 accumulation.
    mass=[]
    for cid in ['CHN','CBE']:
        e=collection.merge(citybin[['bin_key','city_id']],on='bin_key',validate='many_to_one')
        attempts=e.loc[e.city_id==cid,'collected_kg'].sum();daily_kg=daily.loc[daily.city_id==cid,'collected_kg'].sum()
        mass.append({'city_id':cid,'attempt_kg':float(attempts),'daily_kg':float(daily_kg),'difference_kg':float(attempts-daily_kg)})
    pd.DataFrame(tests).to_csv(OUT/'kpi_reconciliation.csv',index=False)
    receipt={'created_utc':datetime.now(timezone.utc).isoformat(),'rows':rows,'relationship_checks':len(links),
             'kpi_checks':len(tests),'all_passed':all(x['passed'] for x in tests),'mass_cross_grain':mass,
             'power_bi_desktop_execution':False,'source_database':str(DB.relative_to(ROOT)),
             'note':'All operational facts are synthetic. SQL is source calculation; Pandas independently aggregates exported model CSVs.'}
    (OUT/'qa_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    c.close()
    assert receipt['all_passed'],[x for x in tests if not x['passed']]
    print(json.dumps({'rows':rows,'links':len(links),'kpi_checks':len(tests),'mass_cross_grain':mass,'all_passed':receipt['all_passed']},indent=2))

if __name__=='__main__':run()
