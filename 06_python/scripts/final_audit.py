"""Read-only final evidence checks; writes only a compact audit receipt."""
from pathlib import Path
import csv,hashlib,json,zipfile,ast
from datetime import datetime,timezone
import duckdb
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'14_outputs/reports/final_audit';OUT.mkdir(parents=True,exist_ok=True)
def run():
 c=duckdb.connect(str(ROOT/'03_data/processed/two_city/two_city.duckdb'),read_only=True)
 counts={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for (t,) in c.execute('SHOW TABLES').fetchall()}
 cities=dict(c.execute('SELECT city_id,count(*) FROM fact_bin_readings GROUP BY city_id').fetchall())
 assert cities=={'CHN':4380000,'CBE':2190000}
 assert c.execute("SELECT count(*) FROM fact_bin_readings WHERE data_origin IS DISTINCT FROM 'synthetic'").fetchone()[0]==0
 assert c.execute('SELECT count(*)-count(DISTINCT reading_key) FROM fact_bin_readings').fetchone()[0]==0
 assert c.execute('SELECT count(*) FROM fact_bin_readings f ANTI JOIN dim_bin b USING(bin_key)').fetchone()[0]==0
 plan=c.execute("EXPLAIN ANALYZE SELECT bin_key,avg(fill_level_pct) FROM fact_bin_readings WHERE city_id='CBE' AND year=2026 AND month='01' GROUP BY bin_key").fetchone()[1]
 assert 'Total Files Read: 1' in plan
 (OUT/'partition_plan.txt').write_text(plan,encoding='utf-8')
 sources=list(csv.DictReader((ROOT/'02_research/acquisition_manifest.csv').open(encoding='utf-8-sig')))
 for row in sources:
  p=ROOT/row['local_path'];h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
  assert h.hexdigest()==row['sha256'],row['local_path']
 pbix=ROOT/'12_powerbi/Smart_Waste_Chennai_Coimbatore.pbix'
 with zipfile.ZipFile(pbix) as z:
  assert z.testzip() is None
  pages=[n for n in z.namelist() if n.endswith('/page.json')]
  assert len(pages)==5 and 'DataModel' in z.namelist()
 syntax=[]
 for p in (ROOT/'06_python').rglob('*.py'):
  ast.parse(p.read_text(encoding='utf-8-sig'));syntax.append(p.relative_to(ROOT).as_posix())
 result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'city_readings':cities,'canonical_counts':counts,'raw_assets_hash_verified':len(sources),'source_ids':len(set(x['source_id'] for x in sources)),'pbix_sha256':hashlib.sha256(pbix.read_bytes()).hexdigest(),'pbix_pages':len(pages),'python_files_syntax_checked':len(syntax),'partition_pruning':'CBE January reads one file','cloud_execution':False,'scope':'Existing pipeline outputs, canonical observations, raw hashes and saved PBIX integrity; no fresh full regeneration or fresh Desktop interaction.'}
 (OUT/'audit_receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,indent=2));c.close()
if __name__=='__main__':run()
