# Data gaps and decision gates

| Priority | Gap | Impact | Next action / defensible fallback |
|---|---|---|---|
| P0 | Pilot geography not finalized | Cannot choose matched denominator or road extract | Proposed Chennai; freeze contiguous service area and boundary version in Phase 2 |
| P0 | Bin coordinates and capacities | Cannot claim existing bin-level optimization | Investigate S04; use documented hypothetical service points on real roads if missing; origin synthetic |
| P0 | Public sensor and collection events | No observed fill forecasting target | Bounded source search; explicitly synthetic operational demonstration |
| P0 | Census-to-modern-ward crosswalk | False population density and per-capita rates | Obtain compatible historical geography; otherwise report native census geography and do not downscale |
| P0 | Usable receiving sites, depots, access | Route feasibility unknown | Verify coordinates, vehicle eligibility and hours; otherwise explicit scenario assumptions |
| P1 | Payload, volumetric capacity, fuel use, crew shifts | Uncertain cost and fleet feasibility | Extract specs/contracts where possible; maintain assumption ranges and sensitivity |
| P1 | Dated high-frequency real waste series | Real forecasting may be infeasible | Search city monthly/daily series; annual reports support context, not daily model training |
| P1 | Recent TNPCB report download failures | Latest state statistics unreviewed | Retry official linked PDFs once in acquisition; use older dated report with explicit caveat |
| P1 | Source licenses | Publication of source data may be restricted | Record terms per resource; publish code/links when redistribution unclear |
| P1 | Traffic, one-way and truck access completeness | OSM drive graph alone may be infeasible | Route audit; restriction-aware edges; mark uncertain travel times as proxy |
| P2 | Holiday/event calendar | Incorrect event date or uplift | Locate year-specific TN government calendar; verify local event dates; uplift remains unestimated |
| P2 | Free IMD weather extraction | Optional meteorological feature unavailable | NASA grid proxy or omit feature after validation |
| P2 | Cloud account / Power BI runtime | Platform evidence not yet demonstrated | Local workflow remains complete; test accounts and Desktop only in their phases |

Missing data must never be silently filled with invented official values. A source-derived estimate retains its parent sources, transformation, units and uncertainty. Any simulation using real locations still has synthetic readings.

## Two-city expansion — 25 September 2026

Coimbatore is technically complete as a simulation, but real operational evidence is partial. OpenCity 2024 ward metadata is not current CCMC certification; official zone-map PDF has no formal crosswalk. S27 rounded 2011 population is not current ward density. S29 scanned operational tables are retained but not ingested without verification. No verified municipal bins, telemetry, route GPS, fleet roster, depot/receiving gate access or CBE procurement price was obtained. POI extraction is broader in CBE than the preserved CHN extract, so counts and coverage percentages are not comparable. No city-difference inferential claim or realized savings estimate is supported.
