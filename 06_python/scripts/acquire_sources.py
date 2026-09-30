"""Acquire immutable public source payloads; never edit an existing raw snapshot."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin
import csv, hashlib, json, requests, time

ROOT=Path(__file__).resolve().parents[2]
DAY=datetime.now(timezone.utc).date().isoformat()
RAW=ROOT/'03_data/raw'
MAN=ROOT/'02_research/acquisition_manifest.csv'
ATT=ROOT/'02_research/acquisition_attempts.csv'
FIELDS=['asset_id','source_id','resource_url','retrieved_at_utc','publication_date','coverage_start','coverage_end','native_grain','geography_version','source_units','crs','license_decision','local_path','bytes','sha256','extractor_version','extraction_notes']
JOBS=[
('S01','gcc_swm.html','https://chennaicorporation.gov.in/gcc/department/solid-waste-management/','HTML context','Unknown','NA','NA','Official webpage; redistribution to review'),
('S02','tnpcb_index.html','https://tnpcb.gov.in/municipalSolidWaste.php','HTML annual-report index','Tamil Nadu','NA','NA','Official webpage; redistribution to review'),
('S02','tnpcb_swm_2024_25.pdf','https://tnpcb.gov.in/PDF/Waste_Mngt/Solid-wste/AnnualRptSWM24_25.pdf','FY annual report','Tamil Nadu','metric tonnes per report','NA','Official PDF; redistribution to review'),
('S02','tnpcb_swm_2023_24.pdf','https://tnpcb.gov.in/PDF/Waste_Mngt/Solid-wste/AnnualRptSWM23_24.pdf','FY annual report','Tamil Nadu','metric tonnes per report','NA','Official PDF; redistribution to review'),
('S03','cpcb_swm_2021_22.pdf','https://cpcb.nic.in/uploads/MSW/MSW_AnnualReport_2021-22.pdf','FY annual report','India states','metric tonnes per report','NA','Official PDF; redistribution to review'),
('S04','smartcities_catalog.html','https://tn.data.gov.in/catalog/solid-waste-management-chennai-7','Catalog only; no available resource','Chennai','NA','NA','GODL metadata; no data payload'),
('S05','census_chennai_ward_2011.xlsx','https://censusindia.gov.in/nada/index.php/catalog/6794/download/9871/DDW_PCA3302_2011_MDDS%20with%20UI.xlsx','Ward/town census row','2011 Chennai district','persons/households','NA','ORGI rights; local research use; verify redistribution'),
('S06','census_handbook_chennai_2011.pdf','https://censusindia.gov.in/nada/index.php/catalog/45344/download/49474/DH_2011_3302_PART_B_DCHB_CHENNAI.pdf','2011 district handbook','2011 Chennai district','persons/households','NA','ORGI rights; local research use; verify redistribution'),
('S07','gcc_boundary_service.json','https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCPublic/GCC_AdminBoundary/MapServer?f=pjson','Service metadata','GCC','NA','EPSG:32644','Official GIS service; redistribution to review'),
('S08','gcc_ward_boundaries.geojson','https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCPublic/GCC_AdminBoundary/MapServer/4/query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson&outSR=4326&resultRecordCount=2000','One ward polygon','GCC boundary version unconfirmed','degrees','EPSG:4326','Official GIS service; redistribution to review'),
('S11','gcc_resolution_2024_06_24.pdf','https://chennaicorporation.gov.in/council/resolution/Council%20Resolution%2024.06.2024.pdf','Council resolution context','Chennai','metric tonnes where noted','NA','Official PDF; redistribution to review'),
('S12','gcc_department_expenditure_2025_26.pdf','https://chennaicorporation.gov.in/gcc/Budget_2025-2026/DEPARTMENT%20EXPENDITURE.pdf','Department budget row','Chennai','INR per stated scale','NA','Official PDF; redistribution to review'),
('S13','ppac_diesel_price_page.html','https://ppac.gov.in/retail-selling-price-rsp-of-petrol-diesel-and-domestic-lpg/rsp-of-petrol-and-diesel-in-metro-cities-since-16-6-2017','Price page context','Chennai','INR/litre','NA','Official webpage; redistribution to review'),
('S14','nasa_power_chennai_daily_2025.json','https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR&community=RE&longitude=80.2707&latitude=13.0827&start=20250101&end=20251231&format=JSON','Grid point day','Chennai grid point','degC/mm','EPSG:4326','NASA POWER acknowledgement/terms to review'),
('S16','mohua_swm_manual_part2.pdf','https://mohua.gov.in/upload/uploadfiles/files/Part2.pdf','Guidance document','India','NA','NA','Official PDF; redistribution to review'),
('S17','mohua_waste_chapter3.pdf','https://www.mohua.gov.in/upload/uploadfiles/files/chap3.pdf','Historical guidance','India','kg/person/day where noted','NA','Official PDF; redistribution to review'),
('S18','tn_dma_swm.html','https://www.tnurbantree.tn.gov.in/sanitation-solid-waste/','State municipal overview','Tamil Nadu','NA','NA','Official webpage; redistribution to review'),
('S19','gcc_tender_2026_02_12.pdf','https://www.chennaicorporation.gov.in/tender-bulletin/tenderBulletin/2026/20260212.pdf','Tender notice','Chennai','INR/asset quantity per notice','NA','Official PDF; redistribution to review'),
('S20','gcc_swm_rules.html','https://chennaicorporation.gov.in/gcc/rules-and-procedure/solid-waste-management/','Municipal procedure','Chennai','NA','NA','Official webpage; redistribution to review'),
]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(path,fields):
 if not path.exists():return []
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(path,fields,rows):
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def run(include_large=False):
 (ROOT/'work').mkdir(parents=True,exist_ok=True)
 manifest=load(MAN,FIELDS);attempts=load(ATT,['source_id','resource_url','attempted_at_utc','status','detail'])
 seen={r['local_path'] for r in manifest}
 jobs=JOBS+[('S09','southern_zone_2026_09_22.osm.pbf','https://download.geofabrik.de/asia/india/southern-zone-260922.osm.pbf','Regional OSM snapshot','Southern India','metres/tags','EPSG:4326','ODbL 1.0; credit OpenStreetMap contributors')] if include_large else JOBS
 for sid,name,url,grain,geo,units,crs,license in jobs:
  relative=f'03_data/raw/{sid}/{DAY}/{name}';dest=ROOT/relative
  if relative in seen:
   expected=next(r['sha256'] for r in manifest if r['local_path']==relative)
   if not dest.exists() or sha(dest)!=expected:
    raise ValueError('Snapshot integrity failure (missing or SHA256 mismatch): '+relative)
   print(sid,name,'existing verified');continue
  if dest.exists():
   raise ValueError('Refusing to overwrite unregistered raw snapshot: '+relative)
  dest.parent.mkdir(parents=True,exist_ok=True)
  tmp=ROOT/'work'/('download_'+name+'.part')
  try:
   with requests.get(url,timeout=(15,90),stream=True,verify=True,headers={'User-Agent':'SmartWastePortfolioResearch/1.0'}) as r:
    r.raise_for_status()
    ctype=r.headers.get('Content-Type','')
    h=hashlib.sha256();n=0;first=b''
    with tmp.open('wb') as f:
     for chunk in r.iter_content(1024*1024):
      if chunk:
       if n==0:first=chunk[:16]
       n+=len(chunk);h.update(chunk);f.write(chunk)
    if name.endswith('.pdf') and not first.startswith(b'%PDF'):raise ValueError('PDF magic mismatch '+ctype)
    if name.endswith('.xlsx') and not first.startswith(b'PK'):raise ValueError('XLSX magic mismatch '+ctype)
    if name.endswith('.geojson'):
     j=json.loads(tmp.read_text(encoding='utf-8'))
     if j.get('type')!='FeatureCollection' or not j.get('features'):raise ValueError('No GIS features')
    if name.endswith('.json'):
     j=json.loads(tmp.read_text(encoding='utf-8'))
     if 'error' in j:raise ValueError(str(j['error'])[:200])
    if name.endswith('.osm.pbf') and n<100_000_000:raise ValueError('Unexpectedly small PBF')
    if relative not in seen:
     tmp.replace(dest)
     manifest.append({'asset_id':sid+'-'+DAY+'-'+name,'source_id':sid,'resource_url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'publication_date':'unknown','coverage_start':'unknown','coverage_end':'unknown','native_grain':grain,'geography_version':geo,'source_units':units,'crs':crs,'license_decision':license,'local_path':relative,'bytes':n,'sha256':h.hexdigest(),'extractor_version':'acquire_sources.py v2','extraction_notes':'Raw untouched. TLS certificate validation enabled.'})
     seen.add(relative)
    attempts.append({'source_id':sid,'resource_url':url,'attempted_at_utc':datetime.now(timezone.utc).isoformat(),'status':'downloaded','detail':f'{n} bytes; {ctype}'})
    print(sid,name,n)
  except Exception as e:
   attempts.append({'source_id':sid,'resource_url':url,'attempted_at_utc':datetime.now(timezone.utc).isoformat(),'status':'failed','detail':type(e).__name__+': '+str(e)[:250]})
   print(sid,name,'FAILED',type(e).__name__,str(e)[:100])
  finally:
   if tmp.exists():tmp.unlink()
   save(MAN,FIELDS,manifest);save(ATT,['source_id','resource_url','attempted_at_utc','status','detail'],attempts)
if __name__=='__main__':
 import sys
 run('--large' in sys.argv)
