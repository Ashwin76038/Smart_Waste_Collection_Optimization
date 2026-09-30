"""Profile Phase 2 datasets without loading the full telemetry table into pandas."""
from pathlib import Path
import duckdb,json,glob,os
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2]
DB=R/'03_data/processed/waste.duckdb'
OUT=R/'14_outputs/reports'
KEYS={'dim_zone_ward':'zone_id','census_chennai_2011_native':None,'weather_chennai_grid_2025':'date','osm_road_nodes_chennai':'osm_node_id','osm_road_segments_chennai':None,'osm_poi_nodes_chennai':'osm_node_id','dim_bin':'bin_id','fact_bin_readings':'reading_id','simulation_truth':'reading_id','interim_readings':'reading_id','collection_events':'collection_id','bin_daily_metrics':None,'zone_daily_metrics':None,'route_daily_metrics':'route_id','vehicle_daily_metrics':None}
CATS={'dim_bin':['zone_id','capacity_l','data_origin'],'fact_bin_readings':['zone_id','sensor_status','collection_status','data_origin'],'collection_events':['zone_id','collection_status'],'osm_poi_nodes_chennai':['poi_type'],'route_daily_metrics':['vehicle_id','distance_origin']}
RANGES={'fact_bin_readings':['fill_level_pct','weight_kg','battery_pct'],'dim_bin':['latitude','longitude','capacity_l'],'osm_road_nodes_chennai':['latitude','longitude'],'osm_road_segments_chennai':['segment_length_m'],'weather_chennai_grid_2025':['temperature_c','rainfall_mm'],'route_daily_metrics':['distance_km_assumed'],'vehicle_daily_metrics':['diesel_l_assumed']}
DATES={'fact_bin_readings':'timestamp_utc','collection_events':'attempted_at_utc','bin_daily_metrics':'service_date_local','zone_daily_metrics':'service_date_local','weather_chennai_grid_2025':'date'}
def main():
 c=duckdb.connect(str(DB),read_only=True)
 profiles={};issues=[]
 for name,key in KEYS.items():
  cols=c.execute(f"PRAGMA table_info('{name}')").fetchall()
  n=c.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
  dtype={r[1]:r[2] for r in cols}
  nullparts=[f'COUNT(*) FILTER (WHERE "{r[1]}" IS NULL)' for r in cols]
  nullvals=c.execute(f'SELECT {",".join(nullparts)} FROM {name}').fetchone()
  nullpct={r[1]:round(100*v/n,4) if n else None for r,v in zip(cols,nullvals)}
  duplicates=None
  if key:duplicates=n-c.execute(f'SELECT COUNT(DISTINCT "{key}") FROM {name}').fetchone()[0]
  elif n<1_000_000:duplicates=n-c.execute(f'SELECT COUNT(DISTINCT hash(t)) FROM {name} t').fetchone()[0]
  bounds={}
  for f in RANGES.get(name,[]):
   a,b=c.execute(f'SELECT MIN("{f}"),MAX("{f}") FROM {name}').fetchone();bounds[f]={'min':a,'max':b}
  if name=='dim_zone_ward':
   for f in ['min_lon','max_lon','min_lat','max_lat']:
    a,b=c.execute(f'SELECT MIN("{f}"),MAX("{f}") FROM {name}').fetchone();bounds[f]={'min':a,'max':b}
  daterange=None
  if name in DATES:
   f=DATES[name];a,b=c.execute(f'SELECT MIN("{f}"),MAX("{f}") FROM {name}').fetchone();daterange={'min':str(a),'max':str(b)}
  cardinality={f:c.execute(f'SELECT COUNT(DISTINCT "{f}") FROM {name}').fetchone()[0] for f in CATS.get(name,[])}
  if name=='fact_bin_readings':storage=sum(p.stat().st_size for p in (R/'03_data/processed/fact_bin_readings').rglob('*.parquet'))
  elif name=='simulation_truth':storage=sum(p.stat().st_size for p in (R/'03_data/synthetic/truth').rglob('*.parquet'))
  elif name=='interim_readings':storage=sum(p.stat().st_size for p in (R/'03_data/interim/readings').rglob('*.parquet'))
  else:
   p=R/'03_data/processed'/f'{name}.parquet'
   storage=p.stat().st_size if p.exists() else None
  sample=c.execute(f'SELECT * FROM {name} LIMIT 1000').df()
  sample_bytes=int(sample.memory_usage(deep=True).sum())
  profiles[name]={'rows':n,'columns':len(cols),'dtypes':dtype,'missing_pct':nullpct,'duplicate_ids_or_rows':duplicates,'impossible_values':{},'numeric_and_geographic_range':bounds,'timestamp_range':daterange,'categorical_cardinality':cardinality,'stored_bytes':storage,'estimated_in_memory_bytes_from_1000_row_sample':round(sample_bytes*n/max(len(sample),1))}
  if duplicates and duplicates>0:issues.append(f'{name}: {duplicates} duplicate IDs/rows')
  print(name,n,flush=True)
 # Explicit key/range checks, independent of tests.
 checks={
 'reading_id_duplicates':profiles['fact_bin_readings']['duplicate_ids_or_rows'],
 'reading_zone_mismatch':c.execute('SELECT COUNT(*) FROM fact_bin_readings r JOIN dim_bin b USING(bin_id) WHERE r.zone_id<>b.zone_id').fetchone()[0],
 'reading_orphan_bin':c.execute('SELECT COUNT(*) FROM fact_bin_readings r ANTI JOIN dim_bin b USING(bin_id)').fetchone()[0],
 'bin_orphan_ward':c.execute('SELECT COUNT(*) FROM dim_bin b ANTI JOIN dim_zone_ward z USING(zone_id)').fetchone()[0],
 'invalid_fill':c.execute('SELECT COUNT(*) FROM fact_bin_readings WHERE fill_level_pct<0 OR fill_level_pct>100').fetchone()[0],
 'invalid_bin_coordinates':c.execute('SELECT COUNT(*) FROM dim_bin WHERE latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180').fetchone()[0],
 'negative_route_distance':c.execute('SELECT COUNT(*) FROM route_daily_metrics WHERE distance_km_assumed<0').fetchone()[0],
 'invalid_collection_status':c.execute("SELECT COUNT(*) FROM collection_events WHERE collection_status NOT IN ('collected','partial','missed')").fetchone()[0],
 }
 for k,v in checks.items():
  if v:issues.append(f'{k}: {v}')
 raw=[]
 for r in sorted((R/'03_data/raw').rglob('*')):
  if r.is_file() and r.name!='.gitkeep':raw.append({'file':str(r.relative_to(R)),'bytes':r.stat().st_size,'kind':r.suffix.lower()})
 overflow_slots=c.execute('SELECT COUNT(*) FROM simulation_truth WHERE overflow_l_true>0').fetchone()[0]
 model_warning=f'Synthetic overflow occurs in {overflow_slots:,} of 4,380,000 scheduled bin-slots ({100*overflow_slots/4380000:.2f}%). This is a calibration warning, not observed Chennai overflow; inspect duration/volume and sensitivity before policy or savings claims.'
 result={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'profiles':profiles,'critical_checks':checks,'issues':issues,'raw_assets':raw,'model_calibration_warning':model_warning,'notes':['Official PDFs/HTML are unstructured source snapshots; their byte counts are recorded, not fictional row counts.','2011 census geography is not mapped to current wards.','Synthetic route distance is an explicit planning assumption, not an observed road measurement.','Estimated memory is extrapolated from a sample, not a measured full-load peak.']}
 (OUT/'data_profile.json').write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
 lines=['# Phase 2 data-quality report','','Generated '+result['generated_at_utc']+'. See data_profile.json for complete column types and missing percentages.','','| Dataset | Rows | Columns | Duplicate IDs/rows | Stored bytes |','|---|---:|---:|---:|---:|']
 for name,p in profiles.items():lines.append(f'| {name} | {p["rows"]:,} | {p["columns"]} | {p["duplicate_ids_or_rows"] if p["duplicate_ids_or_rows"] is not None else "not checked by ID"} | {p["stored_bytes"] if p["stored_bytes"] is not None else "DB table"} |')
 lines+=['','## Critical checks']+[f'- {k}: {v}' for k,v in checks.items()]+['','## Issues']+([f'- {x}' for x in issues] if issues else ['- No critical key/range failures in the implemented tables.'])+['','## Model calibration warning',model_warning,'','## Interpretation limits']+[f'- {x}' for x in result['notes']]
 (OUT/'data_quality_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('issues',issues)
 c.close()
if __name__=='__main__':main()
