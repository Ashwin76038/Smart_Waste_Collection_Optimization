# Research notes — 2026-09-23

## Selection and verification
Tamil Nadu supersedes the initial NYC exploration. No NYC dataset is selected. Chennai is proposed, not user-confirmed as the final city. Source IDs refer to source_catalog.csv. URLs were checked through public web research; verification strength is explicitly recorded. A readable catalog is not proof that a full download works. Blank local_filename means **not acquired**, not a missing local file.

S01 provides operational context, including community collection and named disposal sites. Its undated, mixed-vintage page cannot be used as a dated time series. S02 lists newer annual reports, but the two recent report links returned internal errors in the research browser. Do not claim their tables were read. S03 is a historical national report lead; obtain Tamil Nadu table pages before quoting values.

S04 describes potentially useful bins and vehicle capacities, but its rendered resource section says No Result Found. Treat it as a high-priority acquisition lead, not confirmed bin data. Record exact resource IDs and coverage only after a successful download.

S05/S06 provide 2011 census evidence. Modern GCC wards cannot be joined to those wards solely by number. The expanded corporation may require 2011 tables from adjoining districts and an explicit geographic crosswalk. A current population projection will be derived with uncertainty, never relabeled census observation.

S07/S08 expose actual ward/zone metadata. The service reports EPSG:32644 and supports JSON/GeoJSON queries; layer 4 includes ward and geometry fields. Vintage, polygon validity, completeness and redistribution rights remain unverified. Save actual source CRS and reproject correctly; do not merely relabel coordinates.

S09 supplies OSM road/POI extracts. Roads and mapped POIs are community observations; POI counts used as demand predictors become proxies. Absence of a mapped hospital, market or waste site does not establish absence on the ground. Attribute OSM under S10. Truck access and turn restrictions need separate validation.

S11 offers a concrete procurement/project context for Zones V/VI. S12 distinguishes budget estimates from actuals. Neither establishes per-route variable cost. S13 supplies fuel-price references; retail price is a procurement-cost proxy. No fuel price has been copied into a model.

S14 is optional gridded weather; S15 is a preferred Indian meteorological discovery lead whose free extraction path is unresolved. Weather is only retained if backtesting adds value. Observed future weather cannot be used as known future forecast input.

S16 is planning guidance; S17 is older per-capita background, unsuitable as a modern local estimate. S18 has a jurisdiction caveat. S19 procurement notices do not establish deployed asset inventories. S20 schedules conflict with S01 in detail and need an operational date and scope.

## Technology findings
S21 currently states a 10 GiB lifetime Sandbox storage quota, 1 TiB monthly query processing, 60-day automatic expiration, and no streaming, DML or Data Transfer Service. Therefore use a small upload, retain local data, and never enable billing. S22 supports constrained routing, but heuristic solutions are not guaranteed globally optimal.

## Research gaps deliberately preserved
No verified public high-frequency Chennai IoT history, complete bin coordinate registry, GPS route log, payload-level trip history, actual municipal diesel purchase series or applicable holiday/event operational calendar was established. This does not prove those records do not exist. A bounded Phase 2 search should check S04 resources, municipal open reports and exact source metadata before adopting simulation.

## Research standard
Publication dates are unknown unless shown by the source; crawl dates are not publication dates. Format lists describe source offerings, not downloaded files. Government branding is not a blanket redistribution license. Numerical claims, extraction pages and checksums belong in a future acquisition manifest.

## Phase 4 source additions, 2026-09-24

S23 is the official 12 March 2026 Lok Sabha Q3336 reply citing PPAC: Chennai IOCL diesel INR 92.39/L effective 1 March 2026, Annexures I/II. S24 is the EPA calculator methodology:10,180 gCO2/USgallon of fossil diesel. Both originals are preserved with SHA256 in the acquisition manifest. These are historical price and tailpipe-factor proxies, not local fleet measurements. See `docs/phase4_methodology.md` for use and limitations.

## Two-city expansion — 25 September 2026

S25 OpenCity metadata and S26 KML supply 100 real Coimbatore ward polygons, contributor-attributed and described as 2024. S27 official CCMC sanitation-plan page 17 supports rounded 2011 population 16.01 lakh and area 257 km²; mixed-vintage sections are not automatically trusted. S28 official zone-map PDF and S29 NGT-hosted CCMC filing are contextual originals. S30 is NASA POWER daily 2025 at the Coimbatore study center. S09 regional OSM PBF is reused unchanged. Full URLs, access dates, licenses/limitations and local paths are in source_catalog.csv; acquisition_manifest.csv records byte hashes. No unverified scanned quantity was promoted to a fact.
