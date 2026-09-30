"""Canonical city-aware layer; never overwrite the legacy Chennai database/files."""
from phase4_common import PROJECT_ROOT as ROOT,dump
import duckdb,pandas as pd,json,time

OUT=ROOT/'03_data/processed/two_city'
EXPORT=ROOT/'12_powerbi/two_city_data'
CITY={'CHN':('Chennai',ROOT),'CBE':('Coimbatore',ROOT/'cities/CBE')}

def tag(df,cid):
    d=df.copy();d['city_id']=cid;d['city_name']=CITY[cid][0]
    for local,key in [('bin_id','bin_key'),('zone_id','zone_key'),('reading_id','reading_key')]:
        if local in d:d[key]=cid+':'+d[local].astype(str)
    return d

def run():
    OUT.mkdir(parents=True,exist_ok=True);EXPORT.mkdir(parents=True,exist_ok=True)
    c=duckdb.connect(str(OUT/'two_city.duckdb'));c.execute('SET threads=4');c.execute("SET memory_limit='3GB'")
    cities=pd.DataFrame([{'city_id':cid,'city_name':name,'district':name,'state':'Tamil Nadu','latitude':13.0827 if cid=='CHN' else 11.0168,'longitude':80.2707 if cid=='CHN' else 76.9558,'population_source':'S05;native2011 geography' if cid=='CHN' else 'S27;rounded2011 city profile','data_origin':'derived','coordinate_origin':'assumed study-center reference','operational_data_origin':'synthetic'} for cid,(name,_) in CITY.items()])
    def table(name,df,export=True):
        c.register('_frame',df);c.execute(f'CREATE OR REPLACE TABLE {name} AS SELECT * FROM _frame');c.unregister('_frame');df.to_parquet(OUT/(name+'.parquet'),index=False,compression='zstd')
        if export:df.to_csv(EXPORT/(name+'.csv'),index=False)
    table('dim_city',cities)
    for name,file in [('dim_bin','dim_bin.parquet'),('dim_zone','dim_zone_ward.parquet')]:
        frames=[tag(pd.read_parquet(root/'03_data/processed'/file),cid) for cid,(_,root) in CITY.items()]
        df=pd.concat(frames,ignore_index=True);table(name,df.drop(columns=['geometry_wkb'],errors='ignore'))
        if name=='dim_bin':
            loc=df[['bin_key','bin_id','city_id','city_name','latitude','longitude','osm_node_id','coordinate_origin','data_origin']].copy();loc['location_key']=loc.bin_key;table('dim_location',loc)
    table('dim_date',pd.DataFrame({'date':pd.date_range('2025-01-01','2026-12-31')}))
    for cid,(cityname,root) in CITY.items():
        for src in sorted((root/'03_data/processed/fact_bin_readings').glob('year=*/month=*/*.parquet')):
            month=src.parent.name.split('=')[1];dest=OUT/'fact_bin_readings'/f'city_id={cid}'/'year=2026'/f'month={month}'/'part-000.parquet';dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():
                q=f"SELECT *, '{cid}' AS city_id, '{cityname}' AS city_name, '{cid}:'||bin_id::VARCHAR AS bin_key, '{cid}:'||zone_id AS zone_key, '{cid}:'||reading_id::VARCHAR AS reading_key FROM read_parquet('{src.as_posix()}',hive_partitioning=false)"
                c.execute(f"COPY ({q}) TO '{dest.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        print('city partitions ready',cid,flush=True)
    c.execute(f"CREATE OR REPLACE VIEW fact_bin_readings AS SELECT * FROM read_parquet('{(OUT/'fact_bin_readings').as_posix()}/city_id=*/year=*/month=*/*.parquet',hive_partitioning=true)")
    truth=[]
    for cid,(name,root) in CITY.items():truth.append(f"SELECT *, '{cid}' AS city_id, '{name}' AS city_name, '{cid}:'||reading_id::VARCHAR AS reading_key,'{cid}:'||bin_id::VARCHAR AS bin_key FROM read_parquet('{(root/'03_data/synthetic/truth').as_posix()}/year=*/month=*/*.parquet',hive_partitioning=true)")
    c.execute('CREATE OR REPLACE VIEW simulation_truth AS '+' UNION ALL BY NAME '.join(truth))
    for name in ['bin_daily_metrics','zone_daily_metrics','collection_events','route_daily_metrics','vehicle_daily_metrics']:
        frames=[]
        for cid,(_,root) in CITY.items():
            source=duckdb.connect(str(root/'03_data/processed/waste.duckdb'),read_only=True);df=tag(source.execute('SELECT * FROM '+name).df(),cid);source.close()
            if 'collection_id' in df:df['collection_key']=cid+':'+df.collection_id.astype(str)
            if 'route_id' in df:df['route_key']=cid+':P:'+df.route_id.astype(str)
            if 'vehicle_id' in df:df['vehicle_key']=cid+':P:'+df.vehicle_id.astype(str)
            frames.append(df)
        table(name,pd.concat(frames,ignore_index=True))
    c.execute('CREATE OR REPLACE VIEW fact_collections AS SELECT * FROM collection_events')
    c.execute('CREATE OR REPLACE VIEW dim_zone_ward AS SELECT * FROM dim_zone')
    weather=[]
    for cid,(_,root) in CITY.items():weather.append(tag(pd.read_parquet(root/'03_data/processed'/('weather_chennai_grid_2025.parquet' if cid=='CHN' else 'weather_grid_2025.parquet')),cid))
    table('fact_weather',pd.concat(weather,ignore_index=True))
    # Dashboard daily measures: aggregate FIRST, then join at city/date, never fan out readings.
    c.execute('''CREATE OR REPLACE TABLE city_daily_metrics AS
      WITH observed AS (SELECT city_id,service_date_local,count(*) AS scheduled_readings,count(fill_level_pct) AS received_readings,sum(fill_level_pct) AS fill_sum_pct FROM fact_bin_readings GROUP BY ALL),
      truth AS (SELECT city_id,service_date_local,count(*) FILTER(WHERE overflow_l_true>0) AS overflow_slots FROM simulation_truth GROUP BY ALL),
      daily AS (SELECT city_id,city_name,service_date_local,count(*) AS bins,sum(arrivals_l_simulated) AS generated_l,sum(overflow_l_simulated) AS overflow_l,sum(successful_collections) AS successful_collections,sum(missed_collections) AS missed_collections,sum(collected_kg_simulated) AS collected_kg FROM bin_daily_metrics GROUP BY ALL)
      SELECT d.*,o.scheduled_readings,o.received_readings,o.fill_sum_pct,o.fill_sum_pct/nullif(o.received_readings,0) AS mean_fill_pct,t.overflow_slots,100.0*t.overflow_slots/o.scheduled_readings AS overflow_slot_pct,d.generated_l/d.bins AS generated_l_per_bin_day,1.0*d.successful_collections/d.bins AS collections_per_bin_day,'synthetic' AS data_origin
      FROM daily d JOIN observed o USING(city_id,service_date_local) JOIN truth t USING(city_id,service_date_local)''')
    table('city_daily_metrics',c.execute('SELECT * FROM city_daily_metrics').df())
    optional={'forecast_evaluation':('09_forecasting/phase4/forecast_evaluation.csv','model'),'collection_priority':('10_optimization/phase4/collection_priority.csv','priority'),'route_scenarios':('10_optimization/phase4/scenario_comparison.csv','scenario'),'fact_routes':('10_optimization/phase4/route_summary.csv','route'),'route_stops':('10_optimization/phase4/route_stops.csv','stop'),'overflow_comparison':('10_optimization/phase4/overflow_comparison.csv','overflow')}
    for name,(file,kind) in optional.items():
        if not all((root/file).exists() for _,root in CITY.values()):continue
        frames=[]
        for cid,(_,root) in CITY.items():
            df=tag(pd.read_csv(root/file,dtype={'zone_id':'string'}),cid)
            if 'scenario' in df:df['scenario_key']=cid+':'+df.scenario
            if 'vehicle' in df:df['vehicle_key']=cid+':R:'+df.vehicle.astype(str)
            if kind=='route':
                df['route_key']=df.scenario_key+':'+df.method+':'+df.vehicle.astype(str);df['volume_utilization_pct']=100*df.load_l/12000;df['payload_utilization_pct']=100*df.load_kg_assumed/5000
            if kind=='stop':df['bin_key']=df['bin_key'].where(df.bin_id.ne(0),None)
            df['price_scope']='Historical Chennai common-price proxy; not local Coimbatore price' if cid=='CBE' else 'Historical Chennai price proxy'
            frames.append(df)
        table(name,pd.concat(frames,ignore_index=True))
    if c.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='fact_routes'").fetchone()[0]:
        table('fact_vehicle_operations',c.execute('SELECT * FROM fact_routes').df())
        # Separate proxy fleet identifiers from routing fleet identifiers.
        vehicles=c.execute("SELECT DISTINCT city_id,city_name,vehicle_key,'formula_proxy' AS fleet_scope,NULL::DOUBLE AS capacity_l FROM vehicle_daily_metrics UNION ALL SELECT DISTINCT city_id,city_name,vehicle_key,'routing_scenario',12000.0 FROM fact_routes").df();table('dim_vehicle',vehicles)
    # Truth-derived timing flags are retrospective diagnostics only.
    c.execute('''CREATE OR REPLACE TABLE collection_diagnostics AS SELECT e.*,100*(t.inventory_l_true+t.removed_l_true)/t.capacity_l AS pre_service_fill_pct,t.overflow_l_true>0 AS overflow_at_attempt FROM fact_collections e JOIN simulation_truth t ON e.collection_key=t.reading_key AND e.city_id=t.city_id''')
    table('collection_diagnostics',c.execute('SELECT * FROM collection_diagnostics').df(),False)
    plan=c.execute("EXPLAIN ANALYZE SELECT bin_key,avg(fill_level_pct) FROM fact_bin_readings WHERE city_id='CBE' AND year=2026 AND month='01' GROUP BY bin_key").fetchone()[1]
    (ROOT/'14_outputs/reports/city_expansion/city_partition_query_plan.txt').write_text(plan,encoding='utf-8')
    assert 'Total Files Read: 1' in plan
    tables=[r[0] for r in c.execute('SHOW TABLES').fetchall()];dictionary=[]
    for name in tables:
        for col,dtype,*_ in c.execute('DESCRIBE '+name).fetchall():dictionary.append({'table':name,'field':col,'type':dtype,'city_filter':'city_id via dim_city; date shared','unit_note':'See docs/two_city_model.md; local IDs are not global keys'})
    pd.DataFrame(dictionary).to_csv(ROOT/'docs/data_dictionary_two_city.csv',index=False)
    dump(ROOT/'14_outputs/reports/city_expansion/build_receipt.json',{'counts':{name:c.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in tables},'city_partitions':24,'pruning':'CBE January reads1of24 files','legacy_chennai_db':'unchanged; current combined database is separate','database':str((OUT/'two_city.duckdb').relative_to(ROOT))})
    c.close();print('Combined model ready',flush=True)
if __name__=='__main__':run()
