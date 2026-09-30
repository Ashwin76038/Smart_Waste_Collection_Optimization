# Project state

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
**Executed: 39 passed in 18.55s; 13/13 foundation checks passed. All 120 protected Chennai files match their saved hashes.**

Final acceptance results are written by `finalize_two_city.py` to `14_outputs/reports/city_expansion/verification.json`. Completion requires all pytest checks and all 13 foundation checks to pass, including original Chennai hashes, city keys/fanout, row counts, coordinates, forecast availability, route paths/capacity/depot and counterfactual mass balance. See the receipt for the actual executed result; the script exits nonzero on failure.

## Next Phase
**STOP. Do not begin Phase 5 automatically.** A later explicit request may build the Power BI city slicer and City Comparison page using the prepared contract and reconciled exports. Do not regenerate prior phases without a specific need.
