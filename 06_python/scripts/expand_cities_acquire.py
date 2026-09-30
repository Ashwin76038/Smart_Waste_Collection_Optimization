"""Preserve Chennai evidence, acquire Coimbatore sources, configure isolated run."""
from phase4_common import ROOT,dump
import requests,csv,json,hashlib
from datetime import datetime,timezone
from pathlib import Path

def checksum(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def run():
    audit=ROOT/'14_outputs/reports/city_expansion';audit.mkdir(parents=True,exist_ok=True)
    preserve=audit/'chennai_preservation.json'
    if not preserve.exists():
        files=[]
        for folder in ['03_data/processed','03_data/synthetic','08_geospatial/phase4','09_forecasting/phase4','10_optimization/phase4','14_outputs/charts','14_outputs/maps','14_outputs/tables']:
            for p in (ROOT/folder).rglob('*'):
                if p.is_file() and p.name!='.gitkeep':files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':checksum(p)})
        dump(preserve,{'scope':'Existing Chennai data and analytical outputs; metadata/source catalog may be extended','files':files})
    # Inspect all legacy output tables and documentation without loading large facts.
    inventory=[]
    for folder in ['01_business','02_research','docs','14_outputs','08_geospatial/phase4','09_forecasting/phase4','10_optimization/phase4']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or 'city_expansion' in p.parts:continue
            r={'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size}
            if p.suffix=='.md':r['headings']=[x for x in p.read_text(encoding='utf-8').splitlines() if x.startswith('#')]
            elif p.suffix=='.csv':
                with p.open(encoding='utf-8-sig',newline='') as f:
                    reader=csv.reader(f);r['columns']=next(reader,[]);r['rows']=sum(1 for _ in reader)
            inventory.append(r)
    dump(audit/'prior_output_inventory.json',inventory)
    now=datetime.now(timezone.utc);day=now.date().isoformat()
    catalogpath=ROOT/'02_research/source_catalog.csv';manifestpath=ROOT/'02_research/acquisition_manifest.csv'
    with catalogpath.open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);cf=r.fieldnames;catalog=list(r)
    with manifestpath.open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);mf=r.fieldnames;manifest=list(r)
    def acquire(sid,name,org,url,filename,fmt,period,variables,license,limitations,pub='unknown'):
        target=ROOT/'03_data/raw'/sid/day/filename;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            response=requests.get(url,timeout=120,headers={'User-Agent':'SmartWastePortfolioResearch/1.0'});response.raise_for_status();target.write_bytes(response.content)
        if fmt=='PDF':assert target.read_bytes().startswith(b'%PDF')
        rel=target.relative_to(ROOT).as_posix()
        if sid not in {x['source_id'] for x in catalog}:
            catalog.append(dict(zip(cf,[sid,name,org,url,day,pub,'Coimbatore, Tamil Nadu',period,fmt,license,variables,'Downloaded; immutable snapshot and SHA256 retained',limitations,rel])))
        if rel not in {x['local_path'] for x in manifest}:
            row=dict.fromkeys(mf,'not applicable');row.update(asset_id=sid+'-'+day+'-'+filename,source_id=sid,resource_url=url,retrieved_at_utc=now.isoformat(),publication_date=pub,coverage_start=period,coverage_end=period,native_grain=variables,geography_version='See source; no automatic vintage harmonization',source_units='Native source units retained',license_decision=license,local_path=rel,bytes=target.stat().st_size,sha256=checksum(target),extractor_version='expand_cities_acquire.py v1',extraction_notes=limitations);manifest.append(row)
        for path,fields,rows in [(catalogpath,cf,catalog),(manifestpath,mf,manifest)]:
            with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        print(sid,target.stat().st_size,flush=True);return target
    meta=acquire('S25','Coimbatore ward map catalog','OpenCity / contributor Vaidyanathan R','https://data.opencity.in/api/3/action/package_show?id=coimbatore-wards-map','opencity_catalog.json','JSON','2024 per resource description','ward-map resource metadata','Catalog says Other Public Domain; upstream terms require review','Community-distributed source from livingatlas.esri.in; not independently certified current municipal boundaries')
    resource=json.loads(meta.read_text())['result']['resources'][0]
    ward=acquire('S26','Coimbatore Wards Map 2024','OpenCity; source livingatlas.esri.in',resource['url'],'coimbatore_wards_2024.kml','KML','2024 per metadata','100 ward polygons','Public Domain per resource metadata; retain attribution; upstream provenance limitation','Current ward vintage not certified; compare official map and preserve source attributes','2025-11-25')
    acquire('S27','Coimbatore City Sanitation Plan','Coimbatore City Municipal Corporation','https://www.ccmc.gov.in/img/upload/swachhplan.pdf','city_sanitation_plan.pdf','PDF','2011 census context / historical plan','population; area; ward counts; land-use; facilities','Official public document; reuse terms not established','Mixed historical vintages and copied content; population/area reference only, not current calibration')
    acquire('S28','Official Coimbatore zone and ward map','Coimbatore City Municipal Corporation','https://ccmc.gov.in/img/upload/Zone%20Map.pdf','zone_map.pdf','PDF','undated official map','ward labels and five administrative zones','Official public document; reuse terms not established','Reference map only; no georeferenced polygon asserted')
    acquire('S29','CCMC comprehensive status report OA127/2022','CCMC filing hosted by National Green Tribunal','https://www.greentribunal.gov.in/sites/default/files/news_updates/OA%20No.%20127%20of%202022%20Comprehensive%20status%20report%20of%20CCMC.pdf','ccmc_status_report.pdf','PDF','Report responds to order dated2025-09-03; some2022 estimates','reported population; waste; facilities; processing','Official public filing; reuse terms not established','Statements by respondent; not independently audited municipal event data; periods must be retained')
    weather='https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR&community=AG&longitude=76.9558&latitude=11.0168&start=20250101&end=20251231&format=JSON'
    acquire('S30','NASA POWER Coimbatore daily grid weather2025','NASA POWER',weather,'coimbatore_weather_2025.json','JSON','2025','T2M Celsius; PRECTOTCORR mm/day','NASA open data; attribute NASA POWER','Grid proxy at city center, not a weather station; never future2026 forecast features')
    city=ROOT/'cities/CBE'
    for d in ['config','03_data/processed','03_data/interim','03_data/synthetic/csv','08_geospatial/phase4','09_forecasting/phase4','10_optimization/phase4','14_outputs/reports','14_outputs/maps','14_outputs/tables/phase3_eda']: (city/d).mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/phase4.json').read_text());cfg.update(city_id='CBE',city_name='Coimbatore',scenario_id='phase4_coimbatore_20260923',pilot_center_lat=11.0168,pilot_center_lon=76.9558,graph_bbox_lon_lat=[76.78,10.84,77.18,11.22],analysis_crs='EPSG:32643',boundary_path='03_data/processed/wards.geojson',boundary_label='OpenCity Coimbatore wards (2024 per metadata; unverified)',poi_filename='osm_poi_nodes.parquet',city_label='Coimbatore',currency_scope='Chennai historical diesel rate used as explicit cross-city common-price proxy, not Coimbatore retail price')
    dump(city/'config/phase4.json',cfg)
    cfg2=json.loads((ROOT/'config/project.json').read_text());cfg2['scenario_design'].update(bin_count=500,expected_scheduled_rows=2190000,seed=20260924);dump(city/'config/project.json',cfg2)
    dump(ROOT/'config/cities.json',{'CHN':{'city_name':'Chennai','root':'.','seed':20260923,'bin_count':1000},'CBE':{'city_name':'Coimbatore','root':'cities/CBE','seed':20260924,'bin_count':500,'demand_scale_assumed':.9},'comparability':'Same simulator/policy definitions; different seeded draws and an explicit0.9 demand stress scale. No actual city-difference inference.'})
    print('preserved files',len(json.loads(preserve.read_text())['files']),'inspected output/docs',len(inventory),'ward_source',ward)
if __name__=='__main__':run()
