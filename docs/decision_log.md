# Decision log

| ID | Decision | Rationale / status |
|---|---|---|
| D01 | Tamil Nadu region | Explicit user preference; NYC exploration superseded |
| D02 | Chennai proposed pilot | Official geometry and municipal sources found; exact service area deferred |
| D03 | Local Parquet + DuckDB core | Appropriate for millions of events without cloud charges |
| D04 | Synthetic operations if verified public events unavailable | No fictional readings labeled as real; preserve real spatial context |
| D05 | Separate official context from simulated operations | Prevent false calibration across geography/stream/time |
| D06 | 4.38 M scheduled rows design | 1000 x 365 x 12; practical chunking benchmark required later |
| D07 | Explicit stops/legs/crosswalk/population tables | Needed to avoid fact fanout and verify route costs |
| D08 | config/ and work/ added | Versioned assumptions and ignored local caches/intermediates |
| D09 | BigQuery optional compact Sandbox demo | Current lifetime-storage limit; no billing |
| D10 | No dependency lock asserted yet | No analytical environment installation in this phase |
| D11 | Stop after foundation | Explicit user phase boundary; no Phase 2 execution |

## 2026-09-24 — Phase 4

Use real OSM road geometry but explicitly hypothetical operations. Forecast next-day 04:00 fill from 08:00 information; isolate latent truth. Select ridge only on chronological validation. Avoid weighted priority scores; use safety-rule tiers and 27 sensitivity combinations. Compare identical required stops and reserve full bin capacity, including returns/unloading. Use historical PPAC diesel and a documented EPA factor proxy; retain negative overflow benefits. Stop before Power BI/final presentation.

## Two-city expansion — 25 September 2026

Keep original Chennai artifacts immutable; add isolated CBE workspace and canonical city-keyed views/materializations. Use separate random seeds, geography, models, depot and fleet keys. Preserve explicit synthetic/proxy origins and separate old route proxies from network routes. Decline city-effect hypothesis tests because demand differences are partially encoded by simulation. Do not compare POI counts from unequal extraction scopes. Prepare city-slicer exports and specification only; stop before Phase 5.
