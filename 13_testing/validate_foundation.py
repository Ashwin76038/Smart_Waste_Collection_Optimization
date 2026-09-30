"""Offline checks for Phase 1 only; no downloads, generation or analysis."""
from pathlib import Path
import csv
import json
import re
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = ['01_business','02_research','03_data/raw','03_data/external','03_data/interim','03_data/processed','03_data/synthetic','04_excel','05_sql','06_python/notebooks','06_python/scripts','06_python/utils','07_statistics','08_geospatial','09_forecasting','10_optimization','11_cloud','12_powerbi','13_testing','14_outputs/charts','14_outputs/maps','14_outputs/tables','14_outputs/reports','docs']
REQUIRED_FILES = ['README.md','PLAN.md','PROJECT_STATE.md','requirements.txt','.gitignore','02_research/source_catalog.csv','02_research/data_requirements.md','02_research/research_notes.md','02_research/data_gaps.md','02_research/methodology_proposal.md','docs/data_model.md','docs/model_contract.json','docs/data_dictionary.csv','config/project.json']
CATALOG_FIELDS = ['source_id','dataset_name','organization','url','date_accessed','publication_date','geographic_scope','time_period','format','license','variables','quality','limitations','local_filename']

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))

def validate(root=ROOT):
    checks = []
    def check(name, condition, detail):
        checks.append({'check': name, 'passed': bool(condition), 'detail': detail})
    missing = [p for p in REQUIRED_DIRS if not (root/p).is_dir()] + [p for p in REQUIRED_FILES if not (root/p).is_file()]
    check('required_structure', not missing, {'missing': missing})
    if missing:
        return checks
    sources = read_csv(root/'02_research/source_catalog.csv')
    ids = [r['source_id'] for r in sources]
    check('catalog_schema', bool(sources) and list(sources[0]) == CATALOG_FIELDS, {'rows': len(sources)})
    check('catalog_unique_sources', len(ids)==len(set(ids)), {'source_ids': ids})
    invalid = []
    for row in sources:
        for field in CATALOG_FIELDS[:-1]:
            if not row[field].strip(): invalid.append(row['source_id']+':'+field)
        if not row['url'].startswith('https://'): invalid.append(row['source_id']+':url')
        try: datetime.strptime(row['date_accessed'], '%Y-%m-%d')
        except ValueError: invalid.append(row['source_id']+':date')
    check('catalog_metadata_complete', not invalid, {'invalid': invalid, 'scope':'Metadata integrity only; does not test downloads'})
    phase=json.loads((root/'config/project.json').read_text(encoding='utf-8'))['phase']
    catalog_paths=[x for r in sources for x in r['local_filename'].split(';') if x]
    catalog_ok=all((root/x).is_file() for x in catalog_paths)
    check('catalog_acquisition_links', catalog_ok and (phase!='foundation_only' or not catalog_paths), {'linked_files':len(catalog_paths),'phase':phase})
    plan=(root/'PLAN.md').read_text(encoding='utf-8')
    sections=re.split(r'^## \d+\. ',plan,flags=re.M)[1:]
    fields=['Objective','Why it matters','Input','Tools','Exact work','Outputs','Validation','Common mistakes']
    missing_fields=[f'{i+1}:{field}' for i,s in enumerate(sections) for field in fields if f'**{field}:**' not in s]
    check('roadmap_23_complete_workstreams',len(sections)==23 and not missing_fields,{'workstreams':len(sections),'missing_fields':missing_fields})
    tables=json.loads((root/'docs/model_contract.json').read_text(encoding='utf-8'))['tables']
    lookup={t['name']:t for t in tables}
    errors=[]
    for t in tables:
        cols=[c['name'] for c in t['columns']]
        if len(cols)!=len(set(cols)): errors.append(t['name']+':duplicate column')
        if not t['grain'] or not t['expected_cardinality']: errors.append(t['name']+':missing grain/cardinality')
        if not set(t['primary_key']).issubset(cols): errors.append(t['name']+':bad PK')
        for u in t['unique_constraints']:
            if not set(u).issubset(cols): errors.append(t['name']+':bad unique')
        for c in t['columns']:
            if not c['type'] or not c['unit']: errors.append(t['name']+':missing type/unit')
        for col,target in t['foreign_keys'].items():
            tab,key=target.split('.')
            if col not in cols or tab not in lookup: errors.append(t['name']+':bad FK');continue
            if lookup[tab]['primary_key'] != [key]: errors.append(t['name']+':FK parent not independently unique')
            ct=next(c['type'] for c in t['columns'] if c['name']==col)
            pt=next(c['type'] for c in lookup[tab]['columns'] if c['name']==key)
            if ct!=pt: errors.append(t['name']+':FK type mismatch')
        if t['name']!='dim_source' and not {'data_origin','lineage_id'}.issubset(cols): errors.append(t['name']+':missing provenance')
    check('model_keys_grains_units_relationships', not errors and len(lookup)==len(tables), {'tables':len(tables),'errors':errors})
    dictionary=read_csv(root/'docs/data_dictionary.csv')
    expected={(t['name'],c['name']) for t in tables for c in t['columns']}
    actual={(r['table'],r['column']) for r in dictionary}
    check('dictionary_matches_contract',expected==actual and len(actual)==len(dictionary),{'fields':len(dictionary),'missing':sorted(expected-actual),'extra':sorted(actual-expected)})
    cfg=json.loads((root/'config/project.json').read_text(encoding='utf-8'))
    design=cfg['scenario_design']
    calculated=design['bin_count']*design['days']*design['readings_per_day']
    check('scale_design_arithmetic',calculated==design['expected_scheduled_rows']==4380000,{'scheduled_rows':calculated,'generated_rows':0})
    check('phase_and_billing_guardrails',cfg['billing_allowed'] is False and cfg['region']=='Tamil Nadu' and (phase!='foundation_only' or cfg['generation_enabled'] is False),'Billing disabled; generation follows phase status; Tamil Nadu scope')
    data_files=[str(p.relative_to(root)) for p in (root/'03_data').rglob('*') if p.is_file() and p.name!='.gitkeep']
    check('phase_data_consistency', (not data_files) if phase=='foundation_only' else bool(data_files), {'data_files':len(data_files),'phase':phase})
    state=(root/'PROJECT_STATE.md').read_text(encoding='utf-8')
    state_fields=['Current Phase','Completed','Files Created','Data Acquired','Blocked Items','Important Decisions','Known Limitations','Next Phase']
    check('state_handoff_sections',all('## '+f in state for f in state_fields),'All requested state headings present')
    broken=[]
    for file in root.rglob('*.md'):
        if 'work' in file.parts or '.git' in file.parts: continue
        for url in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if '://' in url or url.startswith('#'):continue
            if not (file.parent/url.split('#')[0]).exists():broken.append(str(file.relative_to(root))+':'+url)
    check('local_document_links',not broken,{'broken':broken})
    return checks

def main():
    checks=validate()
    result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Foundation structure, provenance metadata and design consistency only','passed':all(c['passed'] for c in checks),'checks':checks,'not_tested':['Dataset downloads and values','Analytical dependencies','Forecasts and statistical results','Routing feasibility','Cloud account and Power BI runtime']}
    output=ROOT/'14_outputs/reports/foundation_validation.json'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__':
    sys.exit(main())
