"""Reuse tested engines with explicit city context; default never regenerates Chennai."""
import argparse,os,sys,importlib
parser=argparse.ArgumentParser();parser.add_argument('--city',choices=['CHN','CBE'],required=True);parser.add_argument('--stage',choices=['extract','prepare','generate','convert','marts','forecast','geospatial','routing','counterfactual'],required=True)

def main():
    args=parser.parse_args()
    if args.city=='CHN':raise SystemExit('Chennai is preserved. Use legacy scripts only for a deliberately requested regeneration.')
    os.environ['SMART_WASTE_CITY']=args.city
    from phase4_common import ROOT,PROJECT_ROOT,dump
    if args.stage=='generate':
        import generate_operations as engine
        engine.N=500
        engine.generate(days=365,bins=500,output=ROOT/'03_data/synthetic/csv',root=ROOT,seed=20260924)
    elif args.stage=='convert':
        import convert_events as engine
        engine.ROOT=ROOT;engine.CSV=ROOT/'03_data/synthetic/csv';engine.INTER=ROOT/'03_data/interim/readings';engine.FACT=ROOT/'03_data/processed/fact_bin_readings';engine.TRUTH=ROOT/'03_data/synthetic/truth';engine.main()
    elif args.stage=='marts':
        import duckdb
        c=duckdb.connect(str(ROOT/'03_data/processed/waste.duckdb'));c.execute('SET threads=4')
        # Shared SQL mart definitions; omit Chennai-only external context statements.
        sql=(PROJECT_ROOT/'05_sql/phase2_marts.sql').read_text().replace('{{ROOT}}',ROOT.as_posix())
        omitted=['census_chennai_2011_native','weather_chennai_grid_2025','osm_road_nodes_chennai','osm_road_segments_chennai','osm_poi_nodes_chennai']
        for statement in sql.split(';'):
            if statement.strip() and not any('TABLE '+name+' AS' in statement for name in omitted):c.execute(statement)
        c.execute("CREATE OR REPLACE TABLE weather_grid_2025 AS SELECT * FROM read_parquet(?)",[str(ROOT/'03_data/processed/weather_grid_2025.parquet')])
        annual=c.execute('''SELECT b.bin_id,b.zone_id,b.latitude,b.longitude,b.capacity_l,b.demand_factor,avg(d.arrivals_l_simulated) AS mean_arrival_l_day,count(*) FILTER(WHERE d.overflow_l_simulated>0) AS overflow_days FROM dim_bin b JOIN bin_daily_metrics d USING(bin_id) GROUP BY ALL''').df()
        annual.to_csv(ROOT/'14_outputs/tables/phase3_eda/bin_annual_summary.csv',index=False)
        dump(ROOT/'14_outputs/reports/mart_counts.json',{t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['fact_bin_readings','dim_bin','collection_events','bin_daily_metrics','zone_daily_metrics','route_daily_metrics','vehicle_daily_metrics']});c.close()
    else:
        module={'extract':'phase4_extract_roads','prepare':'prepare_city','forecast':'phase4_forecast','geospatial':'phase4_geospatial','routing':'phase4_routing','counterfactual':'phase4_counterfactual'}[args.stage]
        importlib.import_module(module).run()
    # All newly created city CSVs carry city identity, never filenames alone.
    if args.stage in ['forecast','geospatial','routing','counterfactual']:
        import pandas as pd
        folder={'forecast':'09_forecasting/phase4','geospatial':'08_geospatial/phase4','routing':'10_optimization/phase4','counterfactual':'10_optimization/phase4'}[args.stage]
        for p in (ROOT/folder).glob('*.csv'):
            d=pd.read_csv(p,dtype={'zone_id':'string'});d['city_id']=args.city;d['city_name']='Coimbatore';d.to_csv(p,index=False)
        if args.stage in ['geospatial','routing']:
            for p in (ROOT/'14_outputs/maps').glob('*.html'):
                body=p.read_text(encoding='utf-8').replace('real GCC/OSM geography','Coimbatore · real OpenCity/OSM geography').replace('SIMULATED dispatch ·','Coimbatore · SIMULATED dispatch ·');p.write_text(body,encoding='utf-8')
if __name__=='__main__':main()
