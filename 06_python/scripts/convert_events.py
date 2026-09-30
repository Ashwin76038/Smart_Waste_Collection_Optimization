"""CSV -> typed interim Parquet -> observed-only fact and isolated truth Parquet."""
from pathlib import Path
import pandas as pd, json, time
ROOT=Path(__file__).resolve().parents[2]
CSV=ROOT/'03_data/synthetic/csv'
INTER=ROOT/'03_data/interim/readings'
FACT=ROOT/'03_data/processed/fact_bin_readings'
TRUTH=ROOT/'03_data/synthetic/truth'
OBS=['reading_id','bin_id','timestamp_utc','service_date_local','zone_id','fill_level_pct','weight_kg','temperature_c','battery_pct','sensor_status','collection_status','data_origin']
TRUE=['reading_id','bin_id','timestamp_utc','service_date_local','arrivals_l_true','inventory_l_true','overflow_l_true','removed_l_true','capacity_l','data_origin']
DTYPE={'reading_id':'int64','bin_id':'int32','zone_id':'string','fill_level_pct':'float32','weight_kg':'float32','temperature_c':'float32','battery_pct':'float32','sensor_status':'category','collection_status':'category','arrivals_l_true':'float32','inventory_l_true':'float32','overflow_l_true':'float32','removed_l_true':'float32','capacity_l':'int16','data_origin':'category'}
def main():
 started=time.perf_counter();total=0;files=[]
 for f in sorted(CSV.glob('readings_2026_??.csv')):
  month=f.stem[-2:];df=pd.read_csv(f,dtype=DTYPE,parse_dates=['timestamp_utc','service_date_local'])
  if df.reading_id.duplicated().any():raise ValueError('duplicate reading id in '+f.name)
  if not df.data_origin.eq('synthetic').all():raise ValueError('origin mismatch')
  if not df.fill_level_pct.dropna().between(0,100).all():raise ValueError('fill out of range')
  if not df.capacity_l.gt(0).all():raise ValueError('capacity not positive')
  if not df.sensor_status.eq('missing').equals(df.fill_level_pct.isna()):raise ValueError('missing-status mismatch')
  sub=Path('year=2026')/f'month={month}'
  for directory,cols in [(INTER,list(df.columns)),(FACT,OBS),(TRUTH,TRUE)]:
   target=directory/sub;target.mkdir(parents=True,exist_ok=True)
   dest=target/'part-000.parquet';tmp=target/'part-000.tmp.parquet'
   df[cols].to_parquet(tmp,index=False,compression='zstd');tmp.replace(dest)
  total+=len(df);files.append({'csv':f.name,'rows':len(df),'csv_bytes':f.stat().st_size,'parquet_bytes':(FACT/sub/'part-000.parquet').stat().st_size,'peak_month_df_bytes':int(df.memory_usage(deep=True).sum())})
  print(month,len(df),flush=True)
 report={'rows':total,'months':files,'seconds':round(time.perf_counter()-started,2),'origin':'synthetic','csv_to_parquet':True}
 (ROOT/'03_data/processed/conversion_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('total',total)
if __name__=='__main__':main()
