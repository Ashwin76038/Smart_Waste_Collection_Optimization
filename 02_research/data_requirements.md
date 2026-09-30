# Data requirements and acquisition contracts

This requirements contract was drafted in Phase 1. Phase 2 acquisition and gaps are recorded in `source_catalog.csv`, `acquisition_manifest.csv`, `acquisition_attempts.csv` and `../PROJECT_STATE.md`. Priority remains minimum defensible evidence, not the largest number of sources.

| Domain | Required grain / variables | Candidate source | Origin after processing | Acceptance / fallback |
|---|---|---|---|---|
| Waste | Municipality/period/stream; generated vs collected vs processed tonnes | S01–S04, S11, S18 | official; derived on conversion | Dated scope and units required; no mixing flows or summing stages |
| Population | Census area/year; persons and households | S05–S06 | official | Preserve census geography; no current-ward number join |
| Density | Matching population / land area km2 | S05–S08 | derived | Document area basis, crosswalk, vintage and uncertainty |
| Boundaries | Ward/zone polygon by boundary vintage | S07–S08 | official | CRS, valid geometry, unique IDs, coverage checks |
| Roads | Directed edge u/v/key with length and access | S09 | real; travel time proxy | Clip with routing buffer; connectivity and truck-access audit |
| POIs | Unique OSM type/id; category, coordinates | S09 | real; counts as proxy | Restaurants, markets, schools, hospitals; deduplicate node/way features |
| Land-use | Polygon category or parcel proxy | S09 | proxy for demand | Residential/commercial/industrial coverage assessed; unknown distinct from zero |
| Bins | Bin/location/version; capacity litres, stream, deployment dates | S04/S19 lead | official if obtained; otherwise synthetic/assumption | Registry unresolved; procurement count is not location inventory |
| Facilities | Receiving site/depot; type, location, waste eligibility and window | S01/S11/S18/S09 | official location if verified; otherwise proxy | Separate name evidence from entrance coordinate and capacity assumptions |
| Vehicles | Vehicle/version; payload kg, volume m3, access class, energy type | S04/S11/S19 | official if specs verified; otherwise assumption | No generic fleet count converted into actual roster |
| Fuel/cost | City/effective date; INR/L; crew INR/hour; disposal INR/tonne | S12–S13 | official price; procurement proxy; assumed rates | Separate capex/opex, actual/budget, tax inclusion and price year |
| Weather | Station/grid/local day; Celsius and mm | S14–S15 | proxy for bin conditions | Missing sentinels, geographic resolution and UTC/local day checked |
| Calendar | Local date/event/coverage | Official TN calendar to identify | official date; assumed event effect | No unverified festival dates or automatic collection closure |
| Sensor | Bin/simulation run/timestamp; fill, weight, battery, temperature | Not verified publicly | synthetic if generated | Store truth separately from noisy observations |
| Collections | Collection event/attempt/stream; mass, residual, service times | Not verified publicly | synthetic if generated | Link to route stop; retain failed and partial attempts |
| Routes | Scenario/run/vehicle/day/trip; ordered stops and legs | Not verified publicly | derived from synthetic scenario | Track all legs, unserved bins and feasibility |

## Acquisition manifest contract
Every downloaded asset needs source_id, exact resource URL/ID, retrieved_at UTC, source publication/update date if available, coverage_start/end, native grain, geography/boundary vintage, source units, CRS, license decision, local relative path, bytes, SHA256, extractor version and extraction notes. PDF-derived cells additionally need page/table/row reference and manual verification status. No assumed dates.

Keep raw source payloads immutable in 03_data/raw/source_id/retrieval_date/. Reference context files go in external/ with the same manifest. Scripts produce interim/ and processed/. Generated observations go in synthetic/ only; derived outputs retain lineage to that directory.

## Time coverage
Prefer a common historical window only after observing availability. For real forecasting, seek at least 24 months of monthly collection or 12 months of daily observations; these are planning minimums, not proof of statistical adequacy. A single annual total cannot validate a daily forecast. The synthetic year is chosen after spatial and source vintages are frozen; it is not a claim of historical observed operation.

## Two-city expansion — 25 September 2026

Coverage now includes CHN and CBE. Acquired CBE inputs: 100 real ward polygons, regional OSM roads/POIs/land-use, official contextual municipal PDFs and 2025 NASA grid weather. S27 provides rounded 2011 city population/area context only. Missing: certified current boundaries, ward population/density crosswalk, observed bins/sensors/GPS, verified fleet/depot/receiving entrances, current local costs and comparable audited waste totals. Synthetic operational requirements are met independently; these are not substitutes for municipal evidence.
