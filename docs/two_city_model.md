> Final-audit status (2026-09-30): an actual five-page PBIX has been delivered. Earlier phase-status statements below are historical. Current entry points are README.md, FINAL_PROJECT_REPORT.md and docs/REPRODUCTION.md. Do not run historical finalizers over the final handover.

# Two-city analytical model and migration contract

The project now covers **Chennai and Coimbatore**. Chennai is retained because it is the validated first implementation; Coimbatore is added because it is the user's home city and makes geographic transfer, city-aware engineering and comparison reviewable. The addition is not evidence that either municipality operates the synthetic bins.

## Canonical and legacy entry points

- `03_data/processed/waste.duckdb` and original files remain the **Chennai-only legacy snapshot**. Existing SQL, tests, notebooks, charts and reports continue to work with their original results.
- `cities/CBE/` holds the isolated Coimbatore engine workspace. Shared source code is in `06_python/scripts/`, not copied into the city directory. Its intermediate local IDs support the existing engines.
- **Use `03_data/processed/two_city/two_city.duckdb` for all new city-filtered analysis.** Canonical Parquet readings are partitioned by `city_id`, `year`, `month`, with explicit city columns and global keys. This is a materialized city-enriched copy of the original observations; it does not represent additional observations. Combined count is 6,570,000, not the sum of physical duplicate copies.
- `12_powerbi/two_city_data/` contains city-aware serving extracts for future Phase 5. It is preparation only: no Power BI dashboard, PBIX or cloud execution is claimed.

## Keys, grains and relationships

`dim_city.city_id` is the two-row dimension key: `CHN` / `CBE`. City name, district, state, reference center, population source and origin are included. Latitude/longitude are study-center references, not authoritative municipal centroids. Current population is deliberately absent.

All local numeric/string IDs retain their source value. Global keys concatenate the city identifier and local ID, e.g. `CHN:1` and `CBE:1` are different bins. **Never join cities on local `bin_id`, `zone_id` or `reading_id` alone.** Preserve ward IDs as strings, including leading zeroes. All city-specific relations carry `city_id`; most serving tables also carry `city_name` for readable exports. Joining on a global key plus city is an additional consistency check.

| Canonical relation | Grain / primary or unique key | Foreign keys and interpretation |
|---|---|---|
| dim_city | city_id | Two study areas; conformed filter |
| dim_bin | bin_key | city_id → dim_city; zone_key → dim_zone; 1,500 synthetic bins |
| dim_zone / dim_zone_ward | zone_key | city_id → dim_city; 200 GCC + 100 OpenCity ward geometries; vintage differs |
| dim_location | location_key = bin_key | city_id → dim_city; one hypothetical bin location at a real road node |
| dim_date | date | Shared daily calendar, 2025–2026 |
| dim_vehicle | vehicle_key | city_id → dim_city; P identifies old proxy fleet, R identifies hypothetical routing fleet; never real roster |
| fact_bin_readings | reading_key; also (bin_key,timestamp_utc) | bin_key, zone_key, city_id; 6.57M synthetic scheduled readings |
| simulation_truth | reading_key | Evaluation-only latent litres; excluded from operational predictor features |
| fact_collections / collection_events | collection_key | bin_key, zone_key, city_id; one attempt including misses |
| bin_daily_metrics | (bin_key,service_date_local) | bin_key, zone_key, city_id; 547,500 bin-days |
| zone_daily_metrics | (zone_key,service_date_local) | zone_key, city_id; daily aggregation, not a reading fact |
| city_daily_metrics | (city_id,service_date_local) | 730 city-days; retains KPI numerators and denominators |
| fact_weather | (city_id,date) | 2025 NASA grid proxy; not 2026 observed weather or future predictor |
| route_daily_metrics | route_key | Legacy formula proxy, not a network route; keep separate from fact_routes |
| vehicle_daily_metrics | (vehicle_key,service_date_local) | Legacy formula-distance vehicle-day, not observed GPS operations |
| fact_routes | route_key = city:scenario:method:vehicle | scenario_key and R vehicle_key; one single-trip truck route, with depot return |
| fact_vehicle_operations | same as fact_routes | Convenience projection of the same routing results; do not sum both tables |
| route_scenarios | scenario_key | One scenario per city, fleet-level totals; no feasible savings for failed scenarios |
| route_stops | (scenario_key,method,vehicle,stop_sequence) | Explicit depot endpoints; depot has NULL bin_key; local bin_id=0 means depot only |
| forecast_evaluation | (city_id,split,group,model) | Independent model metrics; n must be retained |
| collection_priority | bin_key for frozen issue | As-of future-risk rules; city and accessibility filter; unique rank within city |

Units: fill is percent of volumetric capacity; MAE/RMSE are percentage points; WAPE percent; recall fraction. Arrival, stored, removed and overflow volume is litres. Mass uses the explicit 0.12 kg/L assumption. Network lengths are metres in route summaries, kilometres in scenario tables. Time is seconds in route summaries and hours in scenario comparisons; timestamps are UTC and `service_date_local` is Asia/Kolkata. Fuel litres, money INR, tailpipe CO2 kilograms. NULL savings means unavailable/infeasible, not zero savings. `volume_utilization_pct` is reserved full-bin volume divided by 12,000 L, not measured payload utilization.

The original `docs/model_contract.json` remains a target-design contract and now includes dim_city/city foreign keys. The implementation above and `data_dictionary_two_city.csv` govern the actual new database; do not mistake older planned tables for populated ones. Automated tests enforce the city/global keys, grain, range and fanout rules.

## Shared engines and independent city evidence

`SMART_WASTE_CITY` selects a workspace in `phase4_common.py`; no variable means original Chennai behavior. `run_city.py --city CBE --stage ...` dispatches the shared extraction, generator, converter, SQL mart, forecasting, spatial, routing and counterfactual engines. It refuses CHN regeneration by default to protect existing outputs. `generate_operations.generate` accepts root, seed and output explicitly while preserving default Chennai behavior.

Coimbatore uses seed 20260924 (Chennai 20260923), its own 500 sampled road nodes across the 100 acquired wards, its own capacities and zone/bin random factors. The factor is additionally multiplied by **0.9 as a deliberately assumed demand scenario**, not estimated from city waste statistics. Intraday/weekend/seasonality, sensor-noise and collection-policy mechanisms stay shared so the framework is comparable. Different seeds and geographic placements mean records are not duplicated. The common density/collection policy is not a claim that city operations are identical.

Forecasts are fitted separately using the same January–June / July–August / September–December target-date split and 20-hour horizon. Withhold every fifth bin: 200 Chennai bins, 100 Coimbatore bins. City models never use the other city's training data. Monthly history available at inference is allowed; latent truth and future labels are excluded. Independent model cards preserve calibration and low near-full-recall caveats.

Routes use separate graphs, study centers/depots, required-bin sets and R vehicle keys. Coimbatore uses EPSG:32643 for projected proximity; Chennai retains EPSG:32644. Both scenarios use 60 geographically selected pilot bins and shared truck/shift/service constraints. City geometry and selected required loads differ, so compare paired baseline-relative improvements, not raw km as a city efficiency ranking. All capacities/depot/service assumptions remain hypothetical. The historical Chennai INR92.39/L price is an explicitly **common-price proxy** for Coimbatore; it is not a sourced local Coimbatore rate. EPA and fuel-economy assumptions are unchanged. No routes connect the cities.

## Public context and gaps

- S25/S26: OpenCity catalog/resource, attributed to contributor Vaidyanathan R and source `livingatlas.esri.in`; metadata describes a 100-ward 2024 KML and Public Domain terms. This is a real community-distributed boundary source, **not an official current CCMC certification**. S28 official PDF is retained as a reference; a formal polygon-by-polygon vintage crosswalk is unresolved.
- S27: official CCMC sanitation plan, PDF page 17, reports area 257 km² and rounded 2011 population 16.01 lakh. The reference context keeps the rounded value and source period; it is not a current population estimate or bin-demand calibration. No current ward population/density join is made. Other sections have mixed dates/copied text and require review.
- S29: official CCMC status-report filing hosted by NGT is preserved. Much of the 205-page PDF is scanned; no unverified numerical waste/facility table is loaded into facts. It is a respondent filing, not independently audited telemetry.
- S09: the same untouched dated Southern Zone PBF covers both cities. Coimbatore extract includes real roads, access tags, POI nodes and representative points for mapped POI ways, plus residential/commercial/retail/industrial land-use ways. OSM hospitals, education, markets, shops, bus stations and rail stations are context, not bin locations. Named waste amenities exist only where mapped; actual depot/receiving access is unverified.
- S30: NASA POWER 2025 at the Coimbatore study center is comparable in date/parameters with Chennai S14. Both are grid proxies. Neither is used as future 2026 weather.

Coimbatore POI extraction is broader (nodes plus ways and more categories) than the preserved Chennai node-only subset. **Do not compare raw POI counts or POI-coverage percentages between cities.** Land-use completeness and ward effective dates also differ. Real per-capita waste, current municipal collection efficiency, fleet performance, budget savings and causal city effects remain unavailable.

## Reproduce only the expansion

Run from the existing project root with the established project-local dependencies:

```powershell
python 06_python/scripts/expand_cities_acquire.py
python 06_python/scripts/run_city.py --city CBE --stage extract
python 06_python/scripts/run_city.py --city CBE --stage prepare
python 06_python/scripts/run_city.py --city CBE --stage generate
python 06_python/scripts/run_city.py --city CBE --stage convert
python 06_python/scripts/run_city.py --city CBE --stage marts
python 06_python/scripts/run_city.py --city CBE --stage forecast
python 06_python/scripts/run_city.py --city CBE --stage geospatial
python 06_python/scripts/run_city.py --city CBE --stage routing
python 06_python/scripts/run_city.py --city CBE --stage counterfactual
python 06_python/scripts/build_two_city.py
python 06_python/scripts/run_city_sql.py
python 06_python/scripts/report_two_city.py
python 06_python/scripts/map_city_priority.py
python 06_python/scripts/finalize_two_city.py
```

Acquisition writes dated immutable snapshots and adds provenance; do not repeat a completed dated download unnecessarily. Existing city-enriched partitions are reused. If intentionally regenerating a source scenario later, refresh its canonical partitions under a new run/version rather than silently reusing stale files. The scenario remains frozen at 23 September 2026 08:00 IST despite the expansion completion date. Five-second routing search is not bitwise reproducible across hardware; preserve the saved solution/hash receipt for reported numbers. No new paid service or cloud deployment is authorized. Stop before Phase 5.
