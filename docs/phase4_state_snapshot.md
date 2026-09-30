# Project state

Last updated: 2026-09-24. Read this file before continuing. All work stays under this project root.

## Current Phase
**Phase 4 — advanced analytics: COMPLETE within the explicit simulation scope. STOP before Power BI and final presentation.** Tamil Nadu is the selected region; Chennai is the hypothetical routing pilot, not a municipal deployment agreement.

## Completed
- Phases 1–3 remain intact: documented architecture and 23-workstream roadmap; immutable public-source acquisition;1,000 hypothetical bins and 4,380,000 synthetic two-hour readings; CSV→Parquet; DuckDB marts; Excel QA;14 business SQL queries; EDA and two simulation-only statistical tests. The previous handoff is preserved in `docs/phase3_state_snapshot.md`.
- Phase 4 derived a directed road network from the preserved S09 PBF:309,559 nodes,651,742 edges. One-way/access/dimension restrictions and conservative turn exclusions are applied. All 1,000 assigned ward polygons match;992 bins have a network node within 100 m and 8 are exceptions. Real roads do not certify truck access.
- Forecasts use observed-only features, chronological train/validation/test, and 200 bins withheld from fitting/selection. Ridge selected on validation; known-bin test MAE8.1667 percentage points, RMSE11.0411, versus best-simple MA7 MAE19.6502; unseen-bin MAE8.1924. Nominal 90% empirical interval coverage 88.4546%; no overflow probability claim.
- Transparent priority tiers and 27 sensitivity combinations created. Frozen 23 September 2026 08:00 IST snapshot:586 bins require attention;36 required in the 60-bin pilot;545 required outside pilot;5 access-review exceptions;414 monitor. No arbitrary weighted priority score or future-truth feature.
- Constrained OR-Tools routes use directed road distances, hypothetical co-located depot/receiving site,12,000 L/5,000 kg trucks,4 min service,15 min unloading,8 h shifts and one trip per truck. Base 3-truck result visits all 36 required bins once:57.3439 km baseline versus 45.4983 km optimized,11.8456 km or 20.6570% saved. Both complete routes use identical stops/constraints; no actual Chennai route baseline is claimed.
- Nine scenarios cover 1/2/3 trucks,70/80/90% triggers,demand+20%,truck unavailable and fuel-price±20%. One/two-truck base cases are proven infeasible under full-bin reserve volume 25,160 L, not proven infeasible for true observed load. Saved solutions are feasible bounded-search results, not globally optimal certificates.
- Base estimated fuel 2.6323 L, historical diesel costINR 243.20 and fossil tailpipeCO2 proxy 7.0784 kg saved; vehicle-time 27.07 min saved. Fuel economy 4.5 km/L is assumed; historical price and EPA factor are sourced. No labor wage/annualized/realized savings asserted.
- Isolated 24 h counterfactual recomputes inventories for all 60 pilot bins and preserves mass balance. Base visit order avoids 11.0634 L simulated spill, but 70%-trigger and+20%-demand optimized orders increase spill versus their matched baseline. No unchanged fill traces reused after collection interventions.
- Final Phase 4 validation: **31 pytest checks passed;13/13 foundation checks passed**. Both interactive maps rendered; route layers tested; three charts visually inspected. Original raw hashes, forecast availability, all 3,721 matrix paths, route constraints, savings arithmetic and counterfactual balance checked.

## Files Created
- Configuration and runnable scripts: `config/phase4.json`; `06_python/scripts/phase4_common.py`, `phase4_sources.py`, `phase4_extract_roads.py`, `phase4_geospatial.py`, `phase4_forecast.py`, `phase4_priority.py`, `phase4_routing.py`, `phase4_counterfactual.py`, `phase4_document.py`, `phase4_handoff.py`; `requirements-phase4.txt`.
- `08_geospatial/phase4/`: directed roads/nodes, land-use GeoJSON, bin spatial features, POI coverage, pilot/matrix locations, directed distance/time matrix, all matrix paths and extraction/geospatial summaries.
- `09_forecasting/phase4/`: model/feature contracts, fitted ridge pipeline, baseline/advanced evaluation, held-out predictions, monthly metrics, dispatch forecasts and forecast chart.
- `10_optimization/phase4/`: priority/sensitivity tables, scenario comparison, route stops/summaries/solutions/GeoJSON, fuel sensitivity and counterfactual results/contract.
- `14_outputs/maps/phase4_geospatial.html`, `phase4_routes.html`; `14_outputs/charts/phase4/route_comparison.png`, `overflow_tradeoff.png`; `14_outputs/tables/phase4_insight_log.csv`.
- `14_outputs/reports/phase4_advanced_analytics_report.md`, `phase4_run_manifest.json`, `phase4_verification.json`, `phase4_source_factor_receipt.json`; `docs/phase4_methodology.md`, `data_dictionary_phase4.csv`, archivedPhase 3 state; `13_testing/test_phase4_advanced.py`. README/PLAN/architecture/reproducibility/decision/source/quality documents updated.

## Data Acquired
The original 18 raw assets remain unchanged. Added official S23 Lok Sabha/PPAC diesel-reference PDF and S24 EPA diesel-factor webpage, with dated originals and SHA256 provenance. Catalog now 24 sources; manifest 20 assets across 18 source IDs. S23 retail Chennai diesel 92.39 INR/L is effective 1 March 2026, not the dispatch-date or municipal procurement price. S24 fossil tailpipe factor 10.180 kg/USgallon converts to approximately 2.689 kg/L, a US proxy. No real sensor/fleet/GPS dataset was acquired. No paid services or cloud jobs ran.

## Blocked Items
- Real municipal bins, telemetry, collections, verified truck roster, depot/receiving entrances and observed comparable routes remain unavailable. Field accessibility and source redistribution terms require review before deployment/public data redistribution.
- S04 has no downloadable bin-level payload; S10/S21/S22 are references; S15 has no verified free payload; S16/S17 manual URLs returned 404 in Phase 2. Census 2011-to-current-ward crosswalk remains unresolved.
- No authenticated no-billing BigQuery project: prepared Phase 2 SQL/schema/upload guide exists, but no cloud execution or screenshot is claimed.
- A clean environment install/lockfile is unverified. Direct package pins and phase-specific output hashes exist. Git has no commit/remote. Earlier Phase 3 notebooks remain syntax-validated companions without executed notebook outputs due Windows Jupyter ACL failure; scripts ran.

## Important Decisions
Keep all operations explicitly synthetic. Geographic inputs remain real/official. Latent truth is isolated from forecast/priority/routing and used only in retrospective evaluation. Pilot selection uses geography before outcomes. Full-capacity reserves protect against fill growth but overstate some payloads. All required pilot stops are mandatory; unserved city bins and access exceptions stay visible. Do not compare the old Phase 2 route-distance formula with the new road baseline. The counterfactual is an isolated single-shift intervention with no other collections in 24 h, not an implemented recurring policy.

## Known Limitations
One synthetic seed/year/date cannot establish real forecasting accuracy, causal gains, statistical route-improvement significance or annual savings. Baseline-policy forecasts require adaptation after changed collection policies. Nominal 90% forecast bands undercover; near-full recall is 56.18%. Missing OSM restrictions, node snapping up to 100 m, assumed speeds, hypothetical depot and assumed service times prevent deployment certification. The graph conservatively removes turn via nodes rather than using a full turn-state model. OSM proximity is not population coverage. Distance-only optimization can increase spill. Historical price and US fossil emissions factor are proxies; fuel excludes idling/PTO effects. Five-second OR-Tools search can differ across reruns/hardware. Maps require online CDN/basemap access. See the methodology/report for exact caveats.

## Next Phase
Only after a later explicit instruction: proceed to Power BI/model/dashboard and final portfolio presentation, using reconciled scenario-keyed exports and preserving synthetic/proxy labels. Do not rerun Phases 1–4 unnecessarily. Any deployment-oriented extension needs real calibration and receiving-site/fleet/access verification. **Stop now before Power BI/final presentation.**

## Verification
See `14_outputs/reports/phase4_verification.json` for executed commands/stdout and `phase4_run_manifest.json` for versions/output hashes. Run `python -m pytest 13_testing -q -p no:cacheprovider` and `python 13_testing/validate_foundation.py` with project dependencies. `docs/phase4_methodology.md` gives the full dependency-ordered rerun sequence. No hidden future labels are exported to dispatch and all reported incomplete scenarios have no savings claim.
