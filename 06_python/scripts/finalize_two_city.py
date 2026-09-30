"""Update the expansion handoff and record offline acceptance without regenerating cities."""
from pathlib import Path
if (Path(__file__).resolve().parents[2]/"FINAL_PROJECT_REPORT.md").exists():
    raise SystemExit("Historical finalizer disabled after final audit. Run individual pipeline and QA scripts; preserve final documentation.")
import csv, hashlib, json, os, subprocess, sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / '14_outputs/reports/city_expansion'

def write(path, text):
    (ROOT/path).write_text(text.strip()+'\n', encoding='utf-8')

def append(path, text):
    p=ROOT/path
    marker='## Two-city expansion — 25 September 2026'
    old=p.read_text(encoding='utf-8').split(marker)[0].rstrip()
    p.write_text(old+'\n\n'+marker+'\n\n'+text.strip()+'\n',encoding='utf-8')

def documents():
    snapshot=ROOT/'docs/phase4_state_snapshot.md'
    if not snapshot.exists(): snapshot.write_bytes((ROOT/'PROJECT_STATE.md').read_bytes())
    p=ROOT/'docs/model_contract.json'; model=json.loads(p.read_text(encoding='utf-8'))
    model['status']='Target-design contract, extended for two cities; actual populated schema is docs/data_dictionary_two_city.csv and docs/two_city_model.md'
    if not any(t['name']=='dim_city' for t in model['tables']):
        cols=[('city_id','VARCHAR','identifier/category'),('city_name','VARCHAR','identifier/category'),('district','VARCHAR','identifier/category'),('state','VARCHAR','identifier/category'),('latitude','DOUBLE','degrees north; reference center'),('longitude','DOUBLE','degrees east; reference center'),('population_source','VARCHAR','source reference; not current population'),('data_origin','VARCHAR','provenance category'),('lineage_id','VARCHAR','lineage identifier')]
        model['tables'].insert(1,{'name':'dim_city','grain':'One geographic study city','primary_key':['city_id'],'expected_cardinality':'2: CHN Chennai and CBE Coimbatore','columns':[{'name':n,'type':t,'unit':u} for n,t,u in cols],'foreign_keys':{},'unique_constraints':[]})
    for t in model['tables']:
        if t['name'] not in ['dim_source','dim_date','dim_city','dim_waste_type']:
            if not any(c['name']=='city_id' for c in t['columns']): t['columns'].append({'name':'city_id','type':'VARCHAR','unit':'city identifier'})
            t['foreign_keys']['city_id']='dim_city.city_id'
        if t['name']=='dim_source':t['expected_cardinality']='30 catalog sources; 24 have acquired assets'
    p.write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/data_dictionary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['table','column','logical_type','unit','primary_key','references','nullability'])
        for t in model['tables']:
            for c in t['columns']:w.writerow([t['name'],c['name'],c['type'],c['unit'],'yes' if c['name'] in t['primary_key'] else 'no',t['foreign_keys'].get(c['name'],''),'PK required; otherwise see nullability policy'])
    p=ROOT/'config/project.json';cfg=json.loads(p.read_text(encoding='utf-8'))
    cfg.update(phase='two_city_expansion_complete',proposed_pilot='Chennai and Coimbatore',cities=['CHN','CBE'],canonical_database='03_data/processed/two_city/two_city.duckdb',combined_scenario={'bin_count':1500,'expected_scheduled_rows':6570000,'note':'scenario_design above remains the preserved Chennai contract; CBE uses config/cities.json'})
    p.write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    p=ROOT/'README.md';text=p.read_text(encoding='utf-8')
    lines=text.splitlines();lines[0]='# Smart Waste Collection Intelligence & Route Optimization — Chennai and Coimbatore'
    text='\n'.join(lines)+'\n'
    old='**Status: Phase 4 advanced analytics complete.** Geospatial analysis, observed-only synthetic forecasting, collection priorities, constrained road routing and scenario comparisons are implemented. Stop before Power BI and final presentation.'
    text=text.replace(old,'**Status: Chennai + Coimbatore expansion complete within the documented simulation scope.** Both cities have separate geography, operations, forecasts and road-routing pilots. Phase 5 has not started. Historical Phase 2–4 sections below describe preserved Chennai results.')
    text=text.replace('Tamil Nadu is the user-selected geography. Chennai is the proposed operational pilot.','Tamil Nadu is the user-selected geography. Chennai preserves the first implementation; Coimbatore, the user’s home city, demonstrates transfer to a second geographic study area and city-filtered comparison.')
    text=text.replace('it cannot establish realized savings for Chennai.','it cannot establish realized savings for either municipality.')
    p.write_text(text,encoding='utf-8')
    append('README.md','''The canonical model contains **6,570,000 synthetic readings, 1,500 hypothetical bins and 300 real ward geometries**, with `dim_city`, global keys and 24 city/month Parquet partitions. Chennai's 120 preserved data/output files retain their original SHA256 hashes. Coimbatore adds independently generated records (seed 20260924), real local roads and separately fitted forecasts.

Start with the [two-city report](14_outputs/reports/city_expansion/comparison_report.md), [actual model and reproducibility contract](docs/two_city_model.md), [actual data dictionary](docs/data_dictionary_two_city.csv), [verification receipt](14_outputs/reports/city_expansion/verification.json) and [City Comparison specification](12_powerbi/CITY_COMPARISON_SPEC.md). Open Coimbatore's [geographic map](cities/CBE/14_outputs/maps/phase4_geospatial.html), [priority map](cities/CBE/14_outputs/maps/phase4_priority.html) and [route map](cities/CBE/14_outputs/maps/phase4_routes.html). Existing Chennai maps remain under `14_outputs/maps/`.

Coimbatore's matched 34-bin, three-truck scenario decreases road distance from 38.46 to 27.97 km (27.26%). These are simulated planning results, not measured municipal savings. Raw city volumes, POI counts and route lengths are not an efficiency league table. The assumed Coimbatore demand factor is 0.9; no empirical city-difference significance test is claimed. BigQuery and Power BI files are prepared only. Stop before Phase 5.''')
    append('PLAN.md','''Completed expansion across the existing workstreams without repeating Chennai generation: six additional sources; 500 Coimbatore bins and 2.19M readings; city/global-key canonical model; 24 parameterized SQL executions; descriptive comparison with inference withheld; independent forecasting, spatial and routing pipelines; two-city Power BI exports/specification. The 23-workstream roadmap remains intact. Historical phase completion figures refer to Chennai; current totals and open deployment gaps are in PROJECT_STATE.md. Next authorized scope is a later explicitly requested Phase 5, not automatic dashboard construction.''')
    append('docs/architecture.md','''The original Chennai workspace/database is retained. Shared Python engines select `SMART_WASTE_CITY`; Coimbatore runs in `cities/CBE/`. The new canonical database is `03_data/processed/two_city/two_city.duckdb`. `dim_city` filters city-specific facts and dimensions; namespaced keys prevent local-ID collisions. Actual grains, unit conventions and relationships are in `two_city_model.md` and `data_dictionary_two_city.csv`.

```mermaid
flowchart LR
  A[Immutable source snapshots + provenance] --> B[Preserved Chennai workspace]
  A --> C[Independent Coimbatore workspace]
  B --> D[City/month Parquet + global keys]
  C --> D
  D --> E[Two-city DuckDB + dim_city]
  E --> F[City-filtered SQL and bounded exports]
  B --> G[Chennai forecast and routing]
  C --> H[Coimbatore forecast and routing]
  G --> F
  H --> F
  F --> I[Comparison report and Phase 5 preparation]
```

There is no intercity route and no pooled forecast. Latent truth remains evaluation-only. Canonical Parquet is a city-enriched materialization, not additional observations. Legacy route proxies and road-network scenario routes remain separate fact domains.''')
    append('docs/data_model.md','''The initial design above remains historical context. `model_contract.json` now adds the city dimension and city FKs to the target design. The populated implementation differs from that planned model; use `two_city_model.md` and `data_dictionary_two_city.csv` for the actual DuckDB contract. Never join CHN/CBE using unqualified local IDs. City-specific serving tables carry city_id and global keys; dim_date is shared. The preserved Chennai-only files are not silently migrated.''')
    append('docs/reproducibility.md','''Expansion commands and isolated workspaces are documented in `two_city_model.md`. Existing Chennai outputs are protected by 120 saved hashes. `finalize_two_city.py` updates documentation, runs pytest and offline foundation checks, and writes verification and artifact hashes without rerunning generators or models. The CBE seed is 20260924; CHN remains 20260923. A regenerated scenario needs a new version of canonical partitions; the builder deliberately reuses existing partitions. Dependencies and clean-install limitations remain unchanged. No billing/cloud activation occurred.''')
    append('docs/large_data_handling.md','''The combined logical event dataset is 6.57M rows, partitioned by city/year/month in 24 Parquet files. A CBE January projection/filter reads one file, recorded in `14_outputs/reports/city_expansion/city_partition_query_plan.txt`. Original benchmark measurements remain Chennai-only; they are not represented as new combined benchmarks. The 730-row city-day CSV is the bounded cloud handoff. Counts of physical copies must not be added to logical row counts.''')
    append('02_research/data_requirements.md','''Coverage now includes CHN and CBE. Acquired CBE inputs: 100 real ward polygons, regional OSM roads/POIs/land-use, official contextual municipal PDFs and 2025 NASA grid weather. S27 provides rounded 2011 city population/area context only. Missing: certified current boundaries, ward population/density crosswalk, observed bins/sensors/GPS, verified fleet/depot/receiving entrances, current local costs and comparable audited waste totals. Synthetic operational requirements are met independently; these are not substitutes for municipal evidence.''')
    append('02_research/methodology_proposal.md','''Implemented two-city methods are in `docs/two_city_model.md` (project-root path). Shared simulation mechanisms use distinct seeds/locations and a clearly assumed CBE 0.9 demand scale. Comparisons normalize by bin-days/readings and retain denominators. Different city layouts and pilot stops prohibit interpreting raw route distances as municipal efficiency. Independent chronological forecasting, within-city matched route baselines and scenario-specific capacity checks are used. No empirical city-effect significance test is valid from these assumed demand differences. Historic Chennai price is only a common-price proxy in CBE. Full observed-data calibration remains a future requirement.''')
    append('02_research/data_gaps.md','''Coimbatore is technically complete as a simulation, but real operational evidence is partial. OpenCity 2024 ward metadata is not current CCMC certification; official zone-map PDF has no formal crosswalk. S27 rounded 2011 population is not current ward density. S29 scanned operational tables are retained but not ingested without verification. No verified municipal bins, telemetry, route GPS, fleet roster, depot/receiving gate access or CBE procurement price was obtained. POI extraction is broader in CBE than the preserved CHN extract, so counts and coverage percentages are not comparable. No city-difference inferential claim or realized savings estimate is supported.''')
    append('02_research/research_notes.md','''S25 OpenCity metadata and S26 KML supply 100 real Coimbatore ward polygons, contributor-attributed and described as 2024. S27 official CCMC sanitation-plan page 17 supports rounded 2011 population 16.01 lakh and area 257 km²; mixed-vintage sections are not automatically trusted. S28 official zone-map PDF and S29 NGT-hosted CCMC filing are contextual originals. S30 is NASA POWER daily 2025 at the Coimbatore study center. S09 regional OSM PBF is reused unchanged. Full URLs, access dates, licenses/limitations and local paths are in source_catalog.csv; acquisition_manifest.csv records byte hashes. No unverified scanned quantity was promoted to a fact.''')
    append('docs/source_verification.md','''The six Coimbatore assets S25–S30 were acquired on 2026-09-24 and added to the acquisition manifest/catalog. Total: 30 catalog sources, 26 raw assets across 24 source IDs. HTTP acquisition receipts and SHA256 identify the exact preserved versions; source authority/vintage limitations remain in the catalog. The regional OSM S09 original was reused without mutation. S27 PDF page 17 was checked for the rounded population/area context; S29 scanned quantities were not asserted as verified structured facts. Tests recheck acquired file hashes.''')
    append('docs/decision_log.md','''Keep original Chennai artifacts immutable; add isolated CBE workspace and canonical city-keyed views/materializations. Use separate random seeds, geography, models, depot and fleet keys. Preserve explicit synthetic/proxy origins and separate old route proxies from network routes. Decline city-effect hypothesis tests because demand differences are partially encoded by simulation. Do not compare POI counts from unequal extraction scopes. Prepare city-slicer exports and specification only; stop before Phase 5.''')
    append('11_cloud/README.md','''Prepared only; no cloud execution occurred. `two_city_daily_upload.csv` contains 730 city-days. In an existing no-billing BigQuery Sandbox, create the `smart_waste` dataset, run the CREATE TABLE in `two_city_sandbox.sql` (replace YOUR_PROJECT with the actual project ID), then use Create table / Upload / CSV into that table, skip one header row and retain the exact schema. Set write disposition to append only for the first load; avoid duplicate reloads. Confirm 730 rows and 365 per city using the saved query. Inspect estimated bytes before querying and use the city/date predicates. Capture later screenshots of no-billing sandbox status, schema, row reconciliation and query results. Do not activate billing or claim successful execution from this local preparation.''')
    write('PROJECT_STATE.md','''# Project state

Last updated: 2026-09-25. Read this file before continuing. All files remain within this project root.

## Current Phase
**Chennai + Coimbatore expansion COMPLETE within the documented synthetic demonstration scope. STOP before Phase 5.** Prior phases are preserved; `docs/phase4_state_snapshot.md` records the previous handoff.

## GEOGRAPHIC COVERAGE
- **Chennai — COMPLETE for the existing simulation and Phase 1–4 analyses; PARTIAL for real operational coverage.** 1,000 bins, 4,380,000 readings, 200 real GCC ward geometries. Existing results and 120 protected data/output files preserved. Missing real sensor/GPS/fleet/depot records and current ward Census crosswalk; 8 access exceptions remain.
- **Coimbatore — COMPLETE for this expansion's simulation, forecasting, geography and routes; PARTIAL for real operational coverage.** 500 independently generated bins, 2,190,000 readings, 100 real OpenCity ward geometries. Missing certified current polygon crosswalk, current ward population, real bins/sensors/GPS/fleet/depot/receiving entrances and local procurement costs. Official contextual PDFs are acquired, but scanned waste quantities are not treated as verified facts.

## Completed
- 6,570,000 synthetic readings across 1,500 bins, 300 ward geometries and 24 city/month Parquet partitions. Canonical city dimension, namespaced keys and DuckDB with 730 city-days and 547,500 bin-days. CBE January predicate reads one partition of 24.
- CBE seed 20260924, own locations/capacities/demand factors and collection records. Shared simulation mechanisms, explicit 0.9 assumed demand multiplier; no copied Chennai records or empirical demand calibration claim.
- Eight city-aware SQL files executed for BOTH/CHN/CBE (24 executions). Normalized descriptive comparisons and autocorrelation diagnostics; no forced inferential city-difference test. Old Chennai SQL remains usable against its unchanged database.
- Coimbatore real road graph: 258,080 nodes, 561,940 directed edges; 82,523 road nodes within acquired wards and 2,662 mapped POIs. All 500 hypothetical bins match their wards and pass 100 m network screening. Separate geography, priority and route maps; no intercity routes.
- Independently fitted CBE ridge: known-bin test MAE 7.6868 fill percentage points versus seven-day baseline 20.5733; unseen-bin MAE 7.5631; 100 held-out bins. Nominal 90% interval coverage 88.22%. Chennai metrics unchanged: 8.1667 versus 19.6502, unseen 8.1924 and 88.45% coverage.
- CBE 60-bin pilot: 34 required stops, three hypothetical trucks; matched baseline 38.4570 km versus optimized 27.9743 km, 10.4827 km (27.2583%) saved. All mandatory stops served once. Full-bin reserve 25,180 L; one/two-truck base cases infeasible. Nine scenarios use identical methodological constraints per city.
- CBE base estimates: 33.08 vehicle-minutes and 2.3295 L fuel saved; INR 215.22 using the historical Chennai common-price proxy, 6.2640 kg fossil CO2 proxy. Isolated 24-hour counterfactual avoids 6.0995 L simulated spill. These are not realized or annual municipal savings.
- City-aware serving extracts, City Comparison specification and bounded 730-row BigQuery upload/schema prepared. No Power BI report built or cloud execution claimed.

## Files Created
- Shared expansion scripts: expand_cities_acquire.py, prepare_city.py, run_city.py, build_two_city.py, run_city_sql.py, report_two_city.py, finalize_two_city.py in `06_python/scripts/`; configurations in `config/cities.json` and `cities/CBE/config/`.
- `cities/CBE/`: isolated data, local database, spatial/forecast/routing outputs and interactive maps. `03_data/processed/two_city/`: canonical Parquet and two_city.duckdb.
- `05_sql/city/`, `14_outputs/tables/city_comparison/`, `07_statistics/two_city_descriptive_diagnostics.csv`, `07_statistics/two_city_statistical_scope.md`.
- `14_outputs/reports/city_expansion/`: comparison_report.md, build/query receipts, profiles, preservation manifest and final verification/hashes. Two charts in `14_outputs/charts/city_comparison/`.
- `docs/two_city_model.md`, `docs/data_dictionary_two_city.csv`, updated target model/dictionary and source/methodology/architecture docs; `13_testing/test_two_city.py`.
- `12_powerbi/two_city_data/`, `12_powerbi/CITY_COMPARISON_SPEC.md`, `11_cloud/two_city_sandbox.sql` and two_city_daily_upload.csv. Prepared only.

## Data Acquired
Catalog has 30 sources; acquisition manifest has 26 raw assets across 24 source IDs. Added S25 OpenCity metadata, S26 Coimbatore KML, S27 official CCMC sanitation plan, S28 official zone-map PDF, S29 NGT-hosted CCMC filing and S30 NASA 2025 weather. Regional S09 OSM PBF reused unchanged. S27 page 17 rounded 2011 population 16.01 lakh and area 257 km² are reference context only. Raw files retain original hashes; no real operational telemetry acquired.

## Blocked Items
No authenticated no-billing cloud run, actual fleet/GPS/bin inventory, verified receiving-site access, current ward population crosswalk or real operational calibration. Earlier missing-source URLs and clean-install/notebook Windows ACL limitations remain in the archived handoff. Git has no committed published portfolio. These do not block the explicitly synthetic demonstration.

## Important Decisions
Use `03_data/processed/two_city/two_city.duckdb` for new analysis. Legacy `waste.duckdb` stays Chennai-only. Join on global keys and city, never local bin/ward IDs alone. Keep legacy formula-distance marts separate from network routes. Operational data_origin remains synthetic; official/geographic/proxy references retain their distinct origins. Truth is evaluation-only. Forecasts and routing are independent by city. No unsupported city-effect significance test or municipality ranking. No paid services.

## Known Limitations
One seed per city, hypothetical 2026 operations and an assumed CBE demand multiplier cannot establish real city differences. Weather is 2025 grid context, not observed 2026 weather. CBE POI extraction is broader than preserved Chennai extraction: raw counts/coverage are not comparable. Boundary vintages differ. Both forecast bands undercover and near-full recall is limited. Hypothetical depots, service/speed/fuel assumptions and missing OSM restrictions prevent deployment certification. Counterfactual is one isolated shift; distance improvement can increase spill in preserved Chennai stress scenarios. CBE fuel price is a historical Chennai proxy, not local verified procurement. Maps require online libraries/tiles. Five-second solver results may vary by hardware; preserve saved solutions. Canonical materialized copies are not additional observations.

## Verification
Final acceptance results are written by `finalize_two_city.py` to `14_outputs/reports/city_expansion/verification.json`. Completion requires all pytest checks and all 13 foundation checks to pass, including original Chennai hashes, city keys/fanout, row counts, coordinates, forecast availability, route paths/capacity/depot and counterfactual mass balance. See the receipt for the actual executed result; the script exits nonzero on failure.

## Next Phase
**STOP. Do not begin Phase 5 automatically.** A later explicit request may build the Power BI city slicer and City Comparison page using the prepared contract and reconciled exports. Do not regenerate prior phases without a specific need.
''')

def validate():
    # The README links this receipt; create an explicitly pending record before
    # checking documentation links, then replace it with the executed result.
    (REPORT/'verification.json').write_text(json.dumps({'passed':False,'status':'validation running'})+'\n',encoding='utf-8')
    env=os.environ.copy();env.pop('SMART_WASTE_CITY',None)
    env['PYTHONPATH']=str(ROOT/'work/phase4deps')+os.pathsep+str(ROOT/'work/pydeps')
    test=subprocess.run([sys.executable,'-m','pytest','13_testing','-q','-p','no:cacheprovider'],cwd=ROOT,env=env,capture_output=True,text=True)
    sys.path.insert(0,str(ROOT/'13_testing'))
    from validate_foundation import validate as foundation
    checks=foundation()
    result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':test.returncode==0 and all(x['passed'] for x in checks),'pytest_exit_code':test.returncode,'pytest_stdout':test.stdout,'pytest_stderr':test.stderr,'foundation_checks':checks,'scope':'Two-city expansion plus preserved Chennai regression suite. Cloud execution and real municipal validity are not asserted.'}
    (REPORT/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(test.stdout);print('Foundation:',sum(x['passed'] for x in checks),'/',len(checks))
    if not result['passed']:
        print(test.stderr);print([x for x in checks if not x['passed']]);raise SystemExit(1)
    state=ROOT/'PROJECT_STATE.md';s=state.read_text(encoding='utf-8')
    summary=next(line for line in reversed(test.stdout.splitlines()) if ' passed' in line)
    s=s.replace('## Verification\n',f'## Verification\n**Executed: {summary.strip()}; {len(checks)}/{len(checks)} foundation checks passed. All 120 protected Chennai files match their saved hashes.**\n\n')
    state.write_text(s,encoding='utf-8')
    paths=[]
    for folder in ['config','06_python/scripts','05_sql/city','13_testing','docs','03_data/processed/two_city','cities/CBE/config','cities/CBE/08_geospatial','cities/CBE/09_forecasting','cities/CBE/10_optimization','cities/CBE/14_outputs','12_powerbi','11_cloud','14_outputs/reports/city_expansion','14_outputs/charts/city_comparison','14_outputs/tables/city_comparison']:
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='expansion_run_manifest.json')
    paths.extend(ROOT/p for p in ['README.md','PLAN.md','PROJECT_STATE.md','02_research/source_catalog.csv'])
    files=[]
    for p in sorted(set(paths)):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
        files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
    (REPORT/'expansion_run_manifest.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'files':files},indent=2)+'\n',encoding='utf-8')
    print('Acceptance complete;',len(files),'artifacts hashed. Stop before Phase 5.')

if __name__=='__main__':
    documents();validate()
