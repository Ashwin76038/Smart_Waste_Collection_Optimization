"""Worker for isolated January benchmark runs."""
import sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
mode=sys.argv[1]
csv_path=R/'03_data/synthetic/csv/readings_2026_01.csv'
parq=R/'03_data/processed/fact_bin_readings/year=2026/month=01/part-000.parquet'
t=time.perf_counter()
if mode=='pandas_full':
 import pandas as pd
 d=pd.read_csv(csv_path,usecols=['zone_id','fill_level_pct'])
 ans=(len(d),int(d.fill_level_pct.count()),float(d.fill_level_pct.sum()))
elif mode=='pandas_chunked':
 import pandas as pd
 n=k=0;s=0.0
 for d in pd.read_csv(csv_path,usecols=['zone_id','fill_level_pct'],chunksize=50_000):
  n+=len(d);k+=int(d.fill_level_pct.count());s+=float(d.fill_level_pct.sum())
 ans=(n,k,s)
elif mode in ('duckdb_csv','duckdb_parquet'):
 import duckdb
 c=duckdb.connect(':memory:')
 if mode=='duckdb_csv': q=f"SELECT COUNT(*),COUNT(fill_level_pct),SUM(fill_level_pct) FROM read_csv_auto('{csv_path.as_posix()}')"
 else:q=f"SELECT COUNT(*),COUNT(fill_level_pct),SUM(fill_level_pct) FROM read_parquet('{parq.as_posix()}')"
 ans=c.execute(q).fetchone()
else:raise ValueError(mode)
print(json.dumps({'mode':mode,'rows':int(ans[0]),'observed':int(ans[1]),'sum_fill_pct':float(ans[2]),'worker_seconds':round(time.perf_counter()-t,4)}))
