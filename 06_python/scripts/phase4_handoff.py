"""Update continuation documents and record executed final quality gates."""
from phase4_common import ROOT,CFG,GEO,FC,OPT,REPORT,dump,format_prose
import json,csv,subprocess,sys,os,hashlib
from datetime import datetime,timezone
import pandas as pd

def run():
    previous=ROOT/'docs/phase3_state_snapshot.md'
    if not previous.exists():previous.write_text((ROOT/'PROJECT_STATE.md').read_text(encoding='utf-8'),encoding='utf-8')
    edits={
      'README.md':[
       ('**Status: Phase 3 SQL, exploratory analysis and statistical testing complete.** Forecasting, optimization, measured savings and Power BI remain future phases.','**Status: Phase 4 advanced analytics complete.** Geospatial analysis, observed-only synthetic forecasting, collection priorities, constrained road routing and scenario comparisons are implemented. Stop before Power BI and final presentation.'),
       ('No savings, forecast accuracy, hypothesis-test results or hiring-quality score is claimed in this phase.','Reported forecast accuracy, tests and route savings apply only to the documented simulation. No realized municipal savings or hiring-quality score is claimed.'),
       ('These later components remain planned, not completed.','Phase 4 forecasting and simulated directed-road optimization are now complete; cloud execution, Power BI and final portfolio packaging remain later gates.')],
      'PLAN.md':[
       ('**Current delivery is Phase 3: SQL, EDA and statistical testing complete.**','**Current delivery is Phase 4: geospatial analysis, collection prioritization, forecasting and constrained route scenarios complete.**'),
       ('Stop after Phase 3; do not fit forecasts, optimize routes, create cloud resources or build dashboards yet.','Phase 4 added observed-only forecasts, transparent priority rules, directed-road CVRP scenarios and explicit proxy-cost calculations. Gates C/D are demonstrated within a synthetic scenario, not verified for municipal deployment. Stop before Power BI and final presentation; no cloud execution occurred.')]
    }
    for name,replacements in edits.items():
        path=ROOT/name;body=path.read_text(encoding='utf-8')
        for old,new in replacements:body=body.replace(old,new)
        path.write_text(body,encoding='utf-8')
    additions={
     'README.md':'\n## Phase 4 review\n\nStart with the [advanced analytics report](14_outputs/reports/phase4_advanced_analytics_report.md), [methodology and rerun contract](docs/phase4_methodology.md), [route map](14_outputs/maps/phase4_routes.html), [geospatial map](14_outputs/maps/phase4_geospatial.html) and [scenario results](10_optimization/phase4/scenario_comparison.csv). The base simulated pilot visits all 36 required bins in 45.50 km versus 57.34 km (20.66% reduction). Known-bin held-out forecast MAE is 8.17 fill percentage points versus 19.65 for the best simple baseline. These are simulation results. See the report for undercoverage and overflow tradeoffs.\n',
     'docs/architecture.md':'\n## Phase 4 implemented extension\n\nSee [Phase 4 architecture and contracts](phase4_methodology.md). A newly derived directed OSM graph supports a 61-location road matrix. Observed-only facts feed time-split forecasts and priorities; a separate truth evaluator consumes routes after optimization. Raw assets and previous marts are preserved. New route outputs replace no historical proxy table and are scenario-keyed.\n',
     'docs/reproducibility.md':'\n## Phase 4 executed workflow\n\n[Phase 4 methodology](phase4_methodology.md) lists scripts in dependency order, units, assumptions, local dependency paths and rerun limits. `requirements-phase4.txt` pins used direct versions; `14_outputs/reports/phase4_run_manifest.json` records output hashes and versions. OR-Tools uses a five-second search limit, so saved feasible routes are authoritative for the reported run. The complete pytest suite and foundation checks are recorded in `phase4_verification.json`. A clean installation remains unverified.\n',
     'docs/decision_log.md':'\n## 2026-09-24 — Phase 4\n\nUse real OSM road geometry but explicitly hypothetical operations. Forecast next-day04:00 fill from08:00 information; isolate latent truth. Select ridge only on chronological validation. Avoid weighted priority scores; use safety-rule tiers and27 sensitivity combinations. Compare identical required stops and reserve full bin capacity, including returns/unloading. Use historical PPAC diesel and a documented EPA factor proxy; retain negative overflow benefits. Stop before Power BI/final presentation.\n',
     '02_research/research_notes.md':'\n## Phase 4 source additions, 2026-09-24\n\nS23 is the official12March2026 Lok Sabha Q3336 reply citing PPAC: Chennai IOCL diesel INR92.39/L effective1March2026, Annexures I/II. S24 is the EPA calculator methodology:10,180gCO2/USgallon of fossil diesel. Both originals are preserved with SHA256 in the acquisition manifest. These are historical price and tailpipe-factor proxies, not local fleet measurements. See `docs/phase4_methodology.md` for use and limitations.\n',
     'docs/source_verification.md':'\n## Phase 4 references\n\nOfficial S23 PDF and S24 HTML were downloaded on2026-09-24 without changing older raw files. Price verified in Annexures I/II; EPA factor verified under diesel consumed. The acquisition manifest now has20 raw assets across18 catalog source IDs; the catalog has24 IDs. S09 was reprocessed locally into a directed access-filtered graph without redownloading or editing its PBF.\n',
     '14_outputs/reports/data_quality_report.md':'\n## Phase 4 extension\n\nSee `phase4_advanced_analytics_report.md` and `phase4_verification.json`. Eight bins fail the100m road-access tolerance; five are required on the frozen dispatch date and explicitly queued for access review. All1,000 ward assignments intersect official polygons. Forecast90% interval coverage is88.45%, not a guaranteed risk probability. Routes pass mandatory-stop, directed-distance, capacity and shift checks. Capacity-infeasible scenarios carry NULL savings. Counterfactual mass balance passes; distance savings can coincide with higher spill. Missing OSM restrictions remain an external data limitation.\n'
    }
    for name,extra in additions.items():
        path=ROOT/name;body=path.read_text(encoding='utf-8');heading=extra.strip().splitlines()[0]
        if heading not in body:path.write_text(body+extra,encoding='utf-8')
    # Additional map legend, shared with generator so future reruns preserve it.
    replacements=[('Annual 2026 retrospective; hypothetical bin coverage. © OpenStreetMap contributors.','Annual 2026 retrospective; hypothetical bins.<br>Overflow days: blue &lt;100; coral 100–199; red ≥200.<br>© OpenStreetMap contributors.'),('Roads require field access verification. © OpenStreetMap contributors.','Roads require field access verification.<br>Vehicles: blue 1, orange 2, green 3. Red bins required; grey monitored.<br>© OpenStreetMap contributors.')]
    for name in ['06_python/scripts/phase4_geospatial.py','06_python/scripts/phase4_routing.py','14_outputs/maps/phase4_geospatial.html','14_outputs/maps/phase4_routes.html']:
        path=ROOT/name;body=path.read_text(encoding='utf-8')
        for old,new in replacements:body=body.replace(old,new)
        path.write_text(body,encoding='utf-8')
    insights=[
     ('P4-01','Forecast','Ridge test MAE8.17pp versus MA7 19.65pp','Synthetic only; near-full recall56%; 90% interval covers88.45%','Validate on real telemetry before operational use'),
     ('P4-02','Routing','36 required pilot bins served; distance57.34→45.50km','Same-stop heuristic comparator; no real route baseline','Use as algorithm demonstration, not realized savings'),
     ('P4-03','Capacity','Reserved volume25,160L exceeds two-truck24,000L','Full-bin reserves and one trip are conservative assumptions','Validate volume reserves and multi-trip receiving constraints'),
     ('P4-04','Service tradeoff','Some distance-optimized scenarios increase24h spill','One synthetic date; isolated intervention','Consider risk deadlines or joint service objective in later work'),
     ('P4-05','Access','8/1000 bins exceed100m road-access tolerance','Missing OSM truck restrictions remain unknown','Verify bin stopping locations and actual depot entrances'),
     ('P4-06','Coverage','545 required bins outside pilot;5 access exceptions','60-bin geographical pilot is not citywide service','Do not present pilot bins-served count as city coverage')]
    pd.DataFrame(insights,columns=['insight_id','topic','finding','limitation','next_evidence']).to_csv(ROOT/'14_outputs/tables/phase4_insight_log.csv',index=False)
    # Verify archived factor contents without claiming text extraction of other PDFs.
    from pypdf import PdfReader
    pdf=next((ROOT/'03_data/raw/S23').rglob('*.pdf'));pages=[p.extract_text() for p in PdfReader(pdf).pages]
    assert '92.39' in '\n'.join(pages) and 'Chennai' in '\n'.join(pages)
    epa=next((ROOT/'03_data/raw/S24').rglob('*.html'));assert '10,180' in epa.read_text(encoding='utf-8')
    dump(REPORT/'phase4_source_factor_receipt.json',{'S23':{'file':pdf.relative_to(ROOT).as_posix(),'pages':len(pages),'verified':'Chennai IOCL 92.39INR/L; AnnexureI page2/II page3; effective2026-03-01'},'S24':{'file':epa.relative_to(ROOT).as_posix(),'verified':'Diesel 10180gCO2/USgallon; tailpipe fossil factor'},'date':'2026-09-24'})
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(ROOT/'work/phase4deps'),str(ROOT/'work/pydeps')])
    results=[]
    for args in [['-m','pytest','13_testing','-q','-p','no:cacheprovider'],['13_testing/validate_foundation.py']]:
        r=subprocess.run([sys.executable,*args],cwd=ROOT,env=env,capture_output=True,text=True)
        results.append({'command':'python '+' '.join(args),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print(r.stdout,flush=True)
    passed=all(r['exit_code']==0 for r in results)
    dump(REPORT/'phase4_verification.json',{'checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':passed,'checks':results,'visual_review':'Both Folium maps rendered in Codex browser; route layer controls exercised; legend overlap corrected. Forecast and2comparison PNGs inspected.','limitations':'No field truck-access verification, real forecast validation, global route optimality or cloud execution.'})
    if not passed:raise RuntimeError('Quality gate failed; do not mark phase complete')
    cfg=json.loads((ROOT/'config/project.json').read_text());cfg['phase']='phase4_complete';dump(ROOT/'config/project.json',cfg)
    state='''# Project state

Last updated: 2026-09-24. Read this file before continuing. All work stays under this project root.

## Current Phase
**Phase 4 — advanced analytics: COMPLETE within the explicit simulation scope. STOP before Power BI and final presentation.** Tamil Nadu is the selected region; Chennai is the hypothetical routing pilot, not a municipal deployment agreement.

## Completed
- Phases 1–3 remain intact: documented architecture and23-workstream roadmap; immutable public-source acquisition;1,000 hypothetical bins and4,380,000 synthetic two-hour readings; CSV→Parquet; DuckDB marts; Excel QA;14 business SQL queries; EDA and two simulation-only statistical tests. The previous handoff is preserved in `docs/phase3_state_snapshot.md`.
- Phase4 derived a directed road network from the preserved S09 PBF:309,559 nodes,651,742 edges. One-way/access/dimension restrictions and conservative turn exclusions are applied. All1,000 assigned ward polygons match;992 bins have a network node within100m and8 are exceptions. Real roads do not certify truck access.
- Forecasts use observed-only features, chronological train/validation/test, and200 bins withheld from fitting/selection. Ridge selected on validation; known-bin test MAE8.1667percentage points, RMSE11.0411, versus best-simple MA7 MAE19.6502; unseen-bin MAE8.1924. Nominal90% empirical interval coverage88.4546%; no overflow probability claim.
- Transparent priority tiers and27 sensitivity combinations created. Frozen23September2026 08:00IST snapshot:586 bins require attention;36 required in the60-bin pilot;545 required outside pilot;5 access-review exceptions;414 monitor. No arbitrary weighted priority score or future-truth feature.
- Constrained OR-Tools routes use directed road distances, hypothetical co-located depot/receiving site,12,000L/5,000kg trucks,4min service,15min unloading,8h shifts and one trip per truck. Base3-truck result visits all36 required bins once:57.3439km baseline versus45.4983km optimized,11.8456km or20.6570% saved. Both complete routes use identical stops/constraints; no actual Chennai route baseline is claimed.
- Nine scenarios cover1/2/3trucks,70/80/90% triggers,demand+20%,truck unavailable and fuel-price±20%. One/two-truck base cases are proven infeasible under full-bin reserve volume25,160L, not proven infeasible for true observed load. Saved solutions are feasible bounded-search results, not globally optimal certificates.
- Base estimated fuel2.6323L, historical diesel costINR243.20 and fossil tailpipeCO2 proxy7.0784kg saved; vehicle-time27.07min saved. Fuel economy4.5km/L is assumed; historical price and EPA factor are sourced. No labor wage/annualized/realized savings asserted.
- Isolated24h counterfactual recomputes inventories for all60 pilot bins and preserves mass balance. Base visit order avoids11.0634L simulated spill, but70%-trigger and+20%-demand optimized orders increase spill versus their matched baseline. No unchanged fill traces reused after collection interventions.
- Final Phase4 validation: **31pytest checks passed;13/13 foundation checks passed**. Both interactive maps rendered; route layers tested; three charts visually inspected. Original raw hashes, forecast availability, all3,721 matrix paths, route constraints, savings arithmetic and counterfactual balance checked.

## Files Created
- Configuration and runnable scripts: `config/phase4.json`; `06_python/scripts/phase4_common.py`, `phase4_sources.py`, `phase4_extract_roads.py`, `phase4_geospatial.py`, `phase4_forecast.py`, `phase4_priority.py`, `phase4_routing.py`, `phase4_counterfactual.py`, `phase4_document.py`, `phase4_handoff.py`; `requirements-phase4.txt`.
- `08_geospatial/phase4/`: directed roads/nodes, land-use GeoJSON, bin spatial features, POI coverage, pilot/matrix locations, directed distance/time matrix, all matrix paths and extraction/geospatial summaries.
- `09_forecasting/phase4/`: model/feature contracts, fitted ridge pipeline, baseline/advanced evaluation, held-out predictions, monthly metrics, dispatch forecasts and forecast chart.
- `10_optimization/phase4/`: priority/sensitivity tables, scenario comparison, route stops/summaries/solutions/GeoJSON, fuel sensitivity and counterfactual results/contract.
- `14_outputs/maps/phase4_geospatial.html`, `phase4_routes.html`; `14_outputs/charts/phase4/route_comparison.png`, `overflow_tradeoff.png`; `14_outputs/tables/phase4_insight_log.csv`.
- `14_outputs/reports/phase4_advanced_analytics_report.md`, `phase4_run_manifest.json`, `phase4_verification.json`, `phase4_source_factor_receipt.json`; `docs/phase4_methodology.md`, `data_dictionary_phase4.csv`, archivedPhase3state; `13_testing/test_phase4_advanced.py`. README/PLAN/architecture/reproducibility/decision/source/quality documents updated.

## Data Acquired
The original18 raw assets remain unchanged. Added official S23 Lok Sabha/PPAC diesel-reference PDF and S24 EPA diesel-factor webpage, with dated originals and SHA256 provenance. Catalog now24 sources; manifest20 assets across18source IDs. S23 retail Chennai diesel92.39INR/L is effective1March2026, not the dispatch-date or municipal procurement price. S24 fossil tailpipe factor10.180kg/USgallon converts to approximately2.689kg/L, a US proxy. No real sensor/fleet/GPS dataset was acquired. No paid services or cloud jobs ran.

## Blocked Items
- Real municipal bins, telemetry, collections, verified truck roster, depot/receiving entrances and observed comparable routes remain unavailable. Field accessibility and source redistribution terms require review before deployment/public data redistribution.
- S04 has no downloadable bin-level payload; S10/S21/S22 are references; S15 has no verified free payload; S16/S17 manual URLs returned404 in Phase2. Census2011-to-current-ward crosswalk remains unresolved.
- No authenticated no-billing BigQuery project: prepared Phase2 SQL/schema/upload guide exists, but no cloud execution or screenshot is claimed.
- A clean environment install/lockfile is unverified. Direct package pins and phase-specific output hashes exist. Git has no commit/remote. Earlier Phase3 notebooks remain syntax-validated companions without executed notebook outputs due Windows Jupyter ACL failure; scripts ran.

## Important Decisions
Keep all operations explicitly synthetic. Geographic inputs remain real/official. Latent truth is isolated from forecast/priority/routing and used only in retrospective evaluation. Pilot selection uses geography before outcomes. Full-capacity reserves protect against fill growth but overstate some payloads. All required pilot stops are mandatory; unserved city bins and access exceptions stay visible. Do not compare the old Phase2 route-distance formula with the new road baseline. The counterfactual is an isolated single-shift intervention with no other collections in24h, not an implemented recurring policy.

## Known Limitations
One synthetic seed/year/date cannot establish real forecasting accuracy, causal gains, statistical route-improvement significance or annual savings. Baseline-policy forecasts require adaptation after changed collection policies. Nominal90% forecast bands undercover; near-full recall is56.18%. Missing OSM restrictions, node snapping up to100m, assumed speeds, hypothetical depot and assumed service times prevent deployment certification. The graph conservatively removes turn via nodes rather than using a full turn-state model. OSM proximity is not population coverage. Distance-only optimization can increase spill. Historical price and US fossil emissions factor are proxies; fuel excludes idling/PTO effects. Five-second OR-Tools search can differ across reruns/hardware. Maps require online CDN/basemap access. See the methodology/report for exact caveats.

## Next Phase
Only after a later explicit instruction: proceed to Power BI/model/dashboard and final portfolio presentation, using reconciled scenario-keyed exports and preserving synthetic/proxy labels. Do not rerun Phases1–4 unnecessarily. Any deployment-oriented extension needs real calibration and receiving-site/fleet/access verification. **Stop now before Power BI/final presentation.**

## Verification
See `14_outputs/reports/phase4_verification.json` for executed commands/stdout and `phase4_run_manifest.json` for versions/output hashes. Run `python -m pytest 13_testing -q -p no:cacheprovider` and `python 13_testing/validate_foundation.py` with project dependencies. `docs/phase4_methodology.md` gives the full dependency-ordered rerun sequence. No hidden future labels are exported to dispatch and all reported incomplete scenarios have no savings claim.
'''
    (ROOT/'PROJECT_STATE.md').write_text(format_prose(state),encoding='utf-8')
    print('Phase4 handoff complete; stop before Power BI/final presentation')
if __name__=='__main__':run()
