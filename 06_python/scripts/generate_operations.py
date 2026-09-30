"""Generate explicitly synthetic bin telemetry and collection attempts.
One chronological stream; fixed seed; no observed operational values are inferred.
"""
from pathlib import Path
import csv,json,hashlib,sys,time
from datetime import datetime,timedelta,timezone,date
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'config/project.json').read_text(encoding='utf-8'))
S=CFG['scenario_design'];N=S['bin_count'];SEED=S['seed']
OUT=ROOT/'03_data/synthetic/csv';OUT.mkdir(parents=True,exist_ok=True)
INTER=ROOT/'03_data/interim'
FIELDS=['reading_id','bin_id','timestamp_utc','service_date_local','zone_id','fill_level_pct','weight_kg','temperature_c','battery_pct','sensor_status','collection_status','arrivals_l_true','inventory_l_true','overflow_l_true','removed_l_true','capacity_l','data_origin']
def generate(days=365,bins=N,output=OUT,root=ROOT,seed=SEED):
 import pandas as pd
 b=pd.read_parquet(root/'03_data/processed/dim_bin.parquet').iloc[:bins].copy().sort_values('bin_id')
 assert len(b)==bins
 ids=b.bin_id.to_numpy();zones=b.zone_id.to_numpy();cap=b.capacity_l.to_numpy(dtype=np.float32);factors=b.demand_factor.to_numpy(dtype=np.float32)
 rng=np.random.default_rng(seed);inventory=rng.uniform(.05,.35,size=bins).astype(np.float32)*cap
 battery=rng.uniform(80,100,size=bins).astype(np.float32);since=np.zeros(bins,dtype=np.int16)
 density=.12;rows=0;collected=0;missed=0;overflows=0
 start=date(2026,1,1);current_month=None;file=None;writer=None
 started=time.perf_counter()
 try:
  for d in range(days):
   local_day=start+timedelta(days=d);month=local_day.month
   if month!=current_month:
    if file:file.close();(output/f'readings_2026_{current_month:02d}.csv.part').replace(output/f'readings_2026_{current_month:02d}.csv')
    current_month=month;output.mkdir(parents=True,exist_ok=True)
    file=(output/f'readings_2026_{month:02d}.csv.part').open('w',newline='',encoding='utf-8')
    writer=csv.writer(file);writer.writerow(FIELDS)
   weekday=local_day.weekday();week_factor=1.12 if weekday>=5 else 1.0
   seasonal=1+.12*np.cos(2*np.pi*(d-300)/365)
   for slot in range(12):
    hour=slot*2
    hour_factor=.6 if hour<6 else (1.25 if 10<=hour<20 else 1.0)
    mean=(cap/24)*factors*week_factor*seasonal*hour_factor
    # Gamma shape 2 provides bursty nonnegative arrivals with the requested expectation.
    arrivals=rng.gamma(2,mean/2).astype(np.float32)
    inventory+=arrivals
    overflow=np.maximum(inventory-cap,0).astype(np.float32);inventory=np.minimum(inventory,cap)
    overflows+=int(np.count_nonzero(overflow))
    status=np.full(bins,'none',dtype=object)
    removed=np.zeros(bins,dtype=np.float32)
    since+=1
    if slot==3:
     due=(inventory>=.72*cap)|(since>=24)
     miss=due & (rng.random(bins)<.04)
     success=due & ~miss
     partial=success & (rng.random(bins)<.03)
     removed[success]=inventory[success]*.95
     removed[partial]=inventory[partial]*.45
     inventory-=removed
     since[success]=0
     status[miss]='missed';status[success]='collected';status[partial]='partial'
     collected+=int(success.sum());missed+=int(miss.sum())
    battery-=.003
    reset=rng.random(bins)<.00002
    battery[reset]=100.0
    battery=np.maximum(battery,1)
    noise=rng.normal(0,2,bins)
    observed=np.clip(100*inventory/cap+noise,0,100)
    stuck=rng.random(bins)<.002
    observed[stuck]=np.clip(100*inventory[stuck]/cap[stuck]-10,0,100)
    dropout=rng.random(bins)<.015
    sensor=np.full(bins,'ok',dtype=object);sensor[stuck]='stuck';sensor[dropout]='missing'
    temp=29+3*np.cos(2*np.pi*(d-120)/365)+rng.normal(0,1.5,bins)
    weight=np.maximum(inventory*density+rng.normal(0,.35,bins),0)
    stamp=(datetime(local_day.year,local_day.month,local_day.day,hour,tzinfo=timezone(timedelta(hours=5,minutes=30)))).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    ordinal=d*12+slot
    for i in range(bins):
     writer.writerow([ordinal*N+int(ids[i]),int(ids[i]),stamp,local_day.isoformat(),str(zones[i]),'' if dropout[i] else round(float(observed[i]),2),'' if dropout[i] else round(float(weight[i]),3),'' if dropout[i] else round(float(temp[i]),2),round(float(battery[i]),3),sensor[i],status[i],round(float(arrivals[i]),5),round(float(inventory[i]),5),round(float(overflow[i]),5),round(float(removed[i]),5),int(cap[i]),'synthetic'])
    rows+=bins
   if (d+1)%30==0:print('days',d+1,'rows',rows,flush=True)
 finally:
  if file:
   file.close();(output/f'readings_2026_{current_month:02d}.csv.part').replace(output/f'readings_2026_{current_month:02d}.csv')
 report={'rows':rows,'bins':bins,'days':days,'seed':seed,'collected_attempts':collected,'missed_attempts':missed,'overflow_slots':overflows,'seconds':round(time.perf_counter()-started,2),'description':'Synthetic operational data generated for scalability, analytics and optimization demonstration. No real sensor records.'}
 (output/'generation_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(report)
 return report
if __name__=='__main__':generate(int(sys.argv[1]) if len(sys.argv)>1 else 365)
