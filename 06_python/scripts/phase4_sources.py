"""Append untouched reference snapshots and explicit factor provenance."""
from phase4_common import ROOT,dump
import csv,hashlib,requests
from datetime import datetime,timezone

SOURCES=[
 {'source_id':'S23','dataset_name':'Retail Petrol and Diesel Price Structure — Lok Sabha Q3336','organization':'Ministry of Petroleum and Natural Gas / PPAC / Lok Sabha','url':'https://sansad.in/getFile/loksabhaquestions/annex/187/AU3336_YCAaF0.pdf?source=pqals','publication_date':'2026-03-12','geographic_scope':'India; Chennai reference','time_period':'2026-03-01 retail price reference','format':'PDF','license':'Official public document; reuse terms not established; retain attribution','variables':'Chennai IOCL diesel retail INR92.39/L; effective 2026-03-01; Annexure I page2 and Annexure II page3','quality':'Official parliamentary response citing PPAC; historical dated reference','limitations':'Not September 2026 price or municipal procurement rate; historical scenario proxy','filename':'lok_sabha_3336_diesel.pdf'},
 {'source_id':'S24','dataset_name':'Greenhouse Gas Equivalencies Calculator — calculations and references','organization':'US Environmental Protection Agency','url':'https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references','publication_date':'unknown','geographic_scope':'United States factor used as explicit proxy','time_period':'2010 EPA/DOT factor cited by current calculator page','format':'HTML','license':'US federal government webpage; retain attribution and referenced source distinctions','variables':'Diesel combustion 10180 grams CO2/US gallon; 3.785411784 L/US gallon; approx 2.689 kg CO2/L','quality':'Official EPA calculator methodology','limitations':'Fossil diesel tailpipe CO2 only; not Indian fleet certification, biofuel, lifecycle, CH4 or N2O estimate','filename':'epa_diesel_equivalencies.html'}]

def run():
    now=datetime.now(timezone.utc);day=now.date().isoformat()
    cp=ROOT/'02_research/source_catalog.csv';mp=ROOT/'02_research/acquisition_manifest.csv'
    with cp.open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);cf=r.fieldnames;catalog=list(r)
    with mp.open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);mf=r.fieldnames;manifest=list(r)
    for source in SOURCES:
        if source['source_id'] in {x['source_id'] for x in catalog}:continue
        target=ROOT/'03_data/raw'/source['source_id']/day/source['filename'];target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            response=requests.get(source['url'],timeout=90,headers={'User-Agent':'SmartWastePortfolioResearch/1.0'});response.raise_for_status();target.write_bytes(response.content)
        payload=target.read_bytes()
        if source['format']=='PDF':assert payload.startswith(b'%PDF')
        else:assert b'10,180' in payload or b'10,180' in payload.replace(b'&#44;',b',')
        rel=target.relative_to(ROOT).as_posix()
        catalog.append({k:(day if k=='date_accessed' else rel if k=='local_filename' else source[k]) for k in cf})
        entry=dict.fromkeys(mf,'not applicable')
        entry.update(asset_id=source['source_id']+'-'+day+'-'+source['filename'],source_id=source['source_id'],resource_url=source['url'],retrieved_at_utc=now.isoformat(),publication_date=source['publication_date'],coverage_start='2026-03-01' if source['source_id']=='S23' else 'unknown',coverage_end='2026-03-01' if source['source_id']=='S23' else 'unknown',native_grain='reference factor',geography_version=source['geographic_scope'],source_units=source['variables'],license_decision=source['license'],local_path=rel,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),extractor_version='phase4_sources.py v1',extraction_notes='Raw untouched; factor manually verified against official text. '+source['limitations'])
        manifest.append(entry)
    for path,fields,rows in [(cp,cf,catalog),(mp,mf,manifest)]:
        with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print('catalog sources',len(catalog),'raw assets',len(manifest))
if __name__=='__main__':run()
