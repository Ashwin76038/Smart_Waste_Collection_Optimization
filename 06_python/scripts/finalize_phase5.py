"""Document the completed offline BI handoff; never claim an executed PBIX."""
from pathlib import Path
if (Path(__file__).resolve().parents[2]/"FINAL_PROJECT_REPORT.md").exists():
    raise SystemExit("Historical finalizer disabled after final audit. Run individual pipeline and QA scripts; preserve final documentation.")
import json

ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'12_powerbi/phase5_model'

def update_section(path,content):
    p=ROOT/path;marker='## Phase 5 — business intelligence'
    body=p.read_text(encoding='utf-8').split(marker)[0].rstrip()
    p.write_text(body+'\n\n'+marker+'\n\n'+content.strip()+'\n',encoding='utf-8')

def run():
    receipt=json.loads((MODEL/'qa_receipt.json').read_text(encoding='utf-8'))
    assert receipt['all_passed'] and receipt['kpi_checks']==52 and receipt['relationship_checks']==16
    assert len(list(MODEL.glob('dim_*.csv')))==5 and len(list(MODEL.glob('fact_*.csv')))==9
    snap=ROOT/'docs/two_city_state_snapshot.md'
    if not snap.exists():snap.write_bytes((ROOT/'PROJECT_STATE.md').read_bytes())
    config=ROOT/'config/project.json';c=json.loads(config.read_text(encoding='utf-8'))
    c['phase']='phase5_bi_handoff_complete'
    c['phase5_mode']='Power BI-ready import/model/DAX/manual-build handoff; no PBIX executed'
    config.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8')
    readme=ROOT/'README.md';body=readme.read_text(encoding='utf-8')
    body=body.replace('**Status: Chennai + Coimbatore expansion complete within the documented simulation scope.** Both cities have separate geography, operations, forecasts and road-routing pilots. Phase 5 has not started. Historical Phase 2–4 sections below describe preserved Chennai results.',
       '**Status: Phase 5 business-intelligence handoff complete.** A two-city star schema, reconciled KPI exports, DAX, theme and five-page dashboard build guide are ready. Power BI Desktop was unavailable, so no PBIX was created. Historical Phase 2–4 sections below describe preserved Chennai results.')
    readme.write_text(body,encoding='utf-8')
    update_section('README.md','''Start Phase 5 review with the [BI model and relationship diagram](12_powerbi/PHASE5_MODEL.md), [DAX measures](12_powerbi/PHASE5_MEASURES.dax), [five-page wireframes](12_powerbi/PHASE5_WIREFRAMES.md), [exact Desktop build guide](12_powerbi/PHASE5_BUILD_GUIDE.md), [business recommendations](12_powerbi/PHASE5_RECOMMENDATIONS.md) and [QA receipt](12_powerbi/phase5_model/qa_receipt.json). The 14 import files are in `12_powerbi/phase5_model/`; the full 6.57M event fact remains in Parquet/DuckDB. All 52 city-specific KPI checks and 16 relationship checks pass against source SQL. No PBIX, publishing or live refresh is claimed. Stop before the final portfolio audit.''')
    update_section('PLAN.md','''Completed the Power BI preparation branch of workstreams 19–22 using the two-city canonical database: five dimensions, nine facts, 16 single-direction relationships, documented DAX, a theme, five-page layouts, import instructions, SQL/Python reconciliation and evidence-bounded recommendations. Power BI Desktop execution is unavailable in this environment; the PBIX/rendered visual QA remains a later manual step. Final portfolio audit/workstream 23 is not started. The archived prior state is `docs/two_city_state_snapshot.md`.''')
    update_section('docs/architecture.md','''Power BI import surface: `12_powerbi/phase5_model/` holds five dimensions and nine facts exported from `two_city.duckdb`. City filters cascade through bin, zone and scenario dimensions without multiple active paths; shared date filters only historical daily/attempt facts. Forecast scores are city/model evaluations and dispatch/route alternatives use fixed snapshots, so neither follows the historical date slicer. `12_powerbi/PHASE5_MODEL.md` contains the implemented Mermaid graph and grain table. No Power BI Desktop artifact or service model was executed.''')
    update_section('docs/reproducibility.md','''From the project root with existing local dependencies: set `PYTHONPATH` to `work/phase4deps;work/pydeps`, run `python 06_python/scripts/build_phase5_bi.py`, then `python 06_python/scripts/phase5_decision_support.py`, then `python 06_python/scripts/finalize_phase5.py`. The first script reads the combined DuckDB without mutation, writes 14 CSVs, and independently reconciles 52 city-specific values. The second runs `05_sql/phase5_decision_support.sql`. Manual Desktop steps and final visual QA remain in `12_powerbi/PHASE5_BUILD_GUIDE.md`. Regenerating prior synthetic city datasets is unnecessary.''')
    report=ROOT/'14_outputs/reports/phase5_business_intelligence_report.md'
    report.write_text('''# Phase 5 — business intelligence handoff

The two-city **synthetic** operations are now shaped for a five-page Power BI report. The model has five dimensions and nine facts, with 16 tested, single-direction relationship paths. The 6.57 million sensor/event rows remain available through Parquet and DuckDB; the BI import uses preaggregated, keyed analytical tables and preserves the collection-attempt detail needed for service diagnostics.

Power BI Desktop is unavailable in this environment; no PBIX, rendered Power BI dashboard or publish has been produced. The ready-to-import CSVs, star diagram, DAX, theme, wireframes and exact manual build guide are in [12_powerbi](../../12_powerbi/PHASE5_MODEL.md). The five pages are Executive Overview, Waste & Bin Analysis, Geographic Intelligence, Route Optimization, and Forecasting & Operations Planning. A normalized City Comparison panel belongs to the overview. Interactive city-specific geographic HTML maps from Phase 4 remain companion artifacts.

## Tested values and reconciliation

SQL against the canonical database and independent Pandas calculations on the exported BI CSVs agree for **52 city-specific KPI checks**. All **16 relationship/foreign-key checks** and all table-grain uniqueness checks pass. The [QA receipt](../../12_powerbi/phase5_model/qa_receipt.json) and [row-level comparison table](../../12_powerbi/phase5_model/kpi_reconciliation.csv) retain exact results and tolerances. Attempt-collected mass differs from preaggregated daily mass by 0.37 kg Chennai and 0.17 kg Coimbatore over the year due to float32 rounding; dashboard collected tonnes uses collection attempts consistently.

The base matched simulated pilot remains Chennai 57.3439→45.4983 km and Coimbatore 38.4570→27.9743 km. Measures require one city and one scenario, and infeasible alternatives leave savings blank. Early collections below 35% are a retrospective synthetic diagnostic. Physical overflow slot rate uses scheduled two-hour readings; overflow bin-day rate uses days with any spill. These are intentionally different denominators. Forecast MAE is in fill percentage points and model scores are city-specific.

## Operating decisions

The [recommendations](../../12_powerbi/PHASE5_RECOMMENDATIONS.md) propose ward field audits, a constrained three-truck pilot and threshold/forecast review with staff oversight. They point to the [ward audit candidates](../../12_powerbi/phase5_model/ward_audit_candidates.csv) and [threshold tradeoffs](../../12_powerbi/phase5_model/threshold_tradeoffs.csv). Real bin telemetry, comparable route GPS, verified fleet/depot/receiving points and local procurement prices are required before deployment or budget claims. Coimbatore's 0.9 demand multiplier is an assumption, not observed city demand. No inferential city-performance ranking is made.

Phase 5 ends here. A later Desktop session must build and visually test the PBIX, then a separate final portfolio audit may evaluate publication readiness.
''',encoding='utf-8')
    (ROOT/'PROJECT_STATE.md').write_text('''# Project state

Last updated: 2026-09-25. Read before continuing. `docs/two_city_state_snapshot.md` preserves the prior handoff. All files stay in this project root.

## Current Phase
**Phase 5 business-intelligence handoff COMPLETE within the available offline environment.** Power BI Desktop was unavailable; no PBIX or live dashboard is claimed. Stop before the final portfolio audit.

## GEOGRAPHIC COVERAGE
- **Chennai — COMPLETE for synthetic Phases 1–5 model/preparation; PARTIAL for real operations.** 1,000 hypothetical bins, 4,380,000 synthetic two-hour readings, 200 real GCC ward polygons. Original Phase 1–4 artifacts and 120 protected hashes preserved. Actual sensors, truck GPS, depot/receiving access, fleet and current ward demographics remain missing.
- **Coimbatore — COMPLETE for synthetic two-city expansion and Phase 5 model/preparation; PARTIAL for real operations.** 500 independent hypothetical bins, 2,190,000 synthetic readings, 100 OpenCity real ward geometries. Current official boundary certification, ward population, true bin/fleet/route data, receiving entrance and local procurement costs remain missing.

## Completed
- Canonical two-city 6.57M-reading Parquet/DuckDB layer from previous phase retained. Phase 5 exports 5 dimensions and 9 facts from it without changing Chennai/source artifacts. Grains, keys and 16 active single-direction relationships are documented in `12_powerbi/PHASE5_MODEL.md`.
- DAX measures for collected tonnes, weighted fill, physical overflow slots, collection completion, early-service diagnostic, dispatch priority, one-scenario road savings, assumed fuel/cost, reserved truck capacity, counterfactual spill and forecast MAE. Unsupported average delay is omitted because no independent due timestamp exists.
- Five-page dashboard wireframe, professional theme, exact Desktop build guide, City Comparison panel, operational recommendations and `14_outputs/reports/phase5_business_intelligence_report.md`.
- SQL and independent Pandas export calculations agree on 52 city-specific KPI checks. Sixteen relationship and all declared grain checks pass. Attempt/daily mass differences are 0.37/0.17 kg from float32 rounding; dashboard collected mass uses attempts.
- Within-city ward audit candidates and 70/80/90% route/spill tradeoffs saved with source SQL. Existing Chennai and Coimbatore interactive maps remain separate.

## Files Created
- `06_python/scripts/build_phase5_bi.py`, `phase5_decision_support.py`, `finalize_phase5.py`; `05_sql/phase5_decision_support.sql`.
- `12_powerbi/phase5_model/`: 14 import CSVs, `qa_receipt.json`, `kpi_reconciliation.csv`, `ward_audit_candidates.csv`, `threshold_tradeoffs.csv`.
- `12_powerbi/PHASE5_MODEL.md`, `PHASE5_MEASURES.dax`, `PHASE5_WIREFRAMES.md`, `PHASE5_BUILD_GUIDE.md`, `PHASE5_RECOMMENDATIONS.md`, `phase5_theme.json`.
- `14_outputs/reports/phase5_business_intelligence_report.md`; `docs/two_city_state_snapshot.md`. README, PLAN, architecture and reproducibility updated.

## Data Acquired
No new source downloads in Phase 5. The previous catalog remains 30 sources; 26 preserved raw assets across 24 source IDs. All operational facts are synthetic. The original city-specific geographic/source caveats remain in `docs/two_city_model.md`.

## Blocked Items
Power BI Desktop was not available in the app inventory or command path, so PBIX construction, rendered Desktop visual QA and refresh/publish could not execute. BigQuery still has no authenticated no-billing run. Real municipal telemetry, comparable GPS/baselines, verified truck/depot/receiving details and local CBE prices remain unavailable. These are external-data/runtime gaps, not hidden completions.

## Important Decisions
Keep a real star schema, not a giant joined flat table. City filters cascade through bin/ward/scenario dimensions; no ambiguous bidirectional path. Date controls historical facts only; fixed dispatch/route snapshots are visibly labeled. Route cards require one city and scenario. Do not sum duplicate city/bin/zone daily views, counterfactual alternatives, or old formula-route proxies. The historical Chennai diesel rate is a common-price proxy in both cities. City comparisons remain descriptive synthetic scenarios.

## Known Limitations
The Power BI DAX/theme and visuals have not been rendered or run in Desktop, so actual PBIX behavior needs the manual visual QA in `12_powerbi/PHASE5_BUILD_GUIDE.md`. Different random seeds, bin counts, geometry vintages and Coimbatore's assumed 0.9 demand multiplier preclude empirical city-effect claims. Forecast bands undercover and near-full recall is limited. Hypothetical depot, capacities, speeds and isolated 24-hour counterfactual limit route decisions. Early collection threshold is a diagnostic, not proof service was unnecessary. No relocation/purchase or annualized savings claim is justified.

## Verification
`12_powerbi/phase5_model/qa_receipt.json` records 16 valid links and 52/52 SQL/Python KPI checks. `kpi_reconciliation.csv` includes each exact city-level value and tolerance. The full pytest/foundation suite must be rerun after this handoff text is complete; record the final result below before stopping.

## Next Phase
**STOP before the final portfolio audit.** In a later Power BI Desktop session, follow the build guide to create and visually QA the PBIX, then update this state with the actual result. A separate user instruction can initiate final portfolio audit and publication review.
''',encoding='utf-8')
    print('Phase 5 docs and handoff state updated')

if __name__=='__main__':run()
