"""Measure comparable January scan tasks in fresh processes."""
from pathlib import Path
import subprocess,sys,time,json,psutil
R=Path(__file__).resolve().parents[2]
RESULT=[]
for mode in ['pandas_full','pandas_chunked','duckdb_csv','duckdb_parquet']:
 p=subprocess.Popen([sys.executable,str(R/'06_python/scripts/benchmark_worker.py'),mode],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=R)
 peak=0;start=time.perf_counter()
 while p.poll() is None:
  try:peak=max(peak,psutil.Process(p.pid).memory_info().rss)
  except psutil.NoSuchProcess:pass
  time.sleep(.02)
 stdout,stderr=p.communicate()
 if p.returncode:raise RuntimeError(mode+' '+stderr[-1000:])
 result=json.loads(stdout);result['elapsed_wall_seconds']=round(time.perf_counter()-start,4);result['peak_rss_bytes_sampled']=peak
 RESULT.append(result);print(result)
base=RESULT[0]
for x in RESULT:
 if x['rows']!=base['rows'] or x['observed']!=base['observed'] or abs(x['sum_fill_pct']-base['sum_fill_pct'])>max(.1,abs(base['sum_fill_pct'])*1e-5):raise AssertionError('Benchmark queries disagree')
cp=R/'03_data/synthetic/csv/readings_2026_01.csv';pp=R/'03_data/processed/fact_bin_readings/year=2026/month=01/part-000.parquet'
result={'task':'January 2026: count rows, nonmissing fill values and sum fill percentage; identical month/scope','results':RESULT,'csv_bytes':cp.stat().st_size,'parquet_observed_bytes':pp.stat().st_size,'caveat':'Parquet excludes latent truth fields present in CSV; file-size ratio is descriptive rather than an identical-schema compression ratio.'}
(R/'14_outputs/reports/large_data_benchmark.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
