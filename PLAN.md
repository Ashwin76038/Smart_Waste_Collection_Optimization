> Final-audit status (2026-09-30): an actual five-page PBIX has been delivered. Earlier phase-status statements below are historical. Current entry points are README.md, FINAL_PROJECT_REPORT.md and docs/REPRODUCTION.md. Do not run historical finalizers over the final handover.

# Project roadmap

## Phase boundary and dependency gates
**Current delivery is Phase 4: geospatial analysis, collection prioritization, forecasting and constrained route scenarios complete.** The 23 workstreams below describe the eventual project; they are not 23 completed phases. See `PROJECT_STATE.md` for executed scope and quality-gate evidence.

Phase 1 established the plan and contracts. Phase 2 acquired and profiled legitimate sources, generated clearly labelled synthetic operations where real IoT data was unavailable, and built Parquet/DuckDB marts. Phase 3 answered business questions in SQL, performed bounded Python EDA and two simulation-only weekly hypothesis tests. Phase 4 added observed-only forecasts, transparent priority rules, directed-road CVRP scenarios and explicit proxy-cost calculations. Gates C/D are demonstrated within a synthetic scenario, not verified for municipal deployment. Stop before Power BI and final presentation; no cloud execution occurred.

- Gate A: pilot boundary/stream, source terms, census alignment and viable acquisition established.
- Gate B: curated dimensions pass QA; simulation assumptions frozen; then scale engineering.
- Gate C: trustworthy baseline SQL/Excel/EDA; then inference and forecast backtesting.
- Gate D: forecast and route feasibility verified; then cost/scenario comparisons.
- Gate E: reconciled marts; then optional cloud and Power BI delivery.
- Gate F: independent reconciliation and reproducibility; then recommendations and portfolio packaging.

Testing runs throughout, even though its dedicated workstream appears near the end. Geospatial preparation can precede synthetic placement. Cloud is optional and cannot block the core project. If real demand history is inadequate, the real-data track stops at descriptive context while forecasting/optimization remain explicitly simulated.

Effort should be estimated after acquisition profiling, not promised from an unknown source situation. Project lead records gates and decisions in PROJECT_STATE.md; analyst owns metrics, analytics engineer owns transformations, operations analyst owns feasibility, and data architect owns contracts. These are responsibilities, not claims that a team was hired.

## 1. Business understanding

**Objective:** Define a measurable municipal collection decision.

**Why it matters:** Prevents a dashboard without an operational purpose.

**Input:** User brief; S01/S16/S18/S20; business charter.

**Tools:** Stakeholder mapping; Markdown; KPI specification.

**Exact work:** Freeze Chennai pilot, waste stream, dispatcher decision cadence, service guardrails and baseline definitions. Separate operational process types and record exclusions.

**Outputs:** 01_business/business_charter.md; decision and KPI register.

**Validation:** Every KPI has a unit, denominator, scope and intended action; no unsupported numeric targets.

**Common mistakes:** Calling all municipal waste bin waste; promising savings before baseline evidence.

## 2. Data requirements

**Objective:** Turn decisions into minimum evidence contracts.

**Why it matters:** Determines whether planned conclusions are identifiable.

**Input:** Charter; data gaps; preliminary source catalog.

**Tools:** Schema design; source-to-requirement matrix.

**Exact work:** Confirm pilot choice, compatible spatial vintages, event grain, coverage period, critical fields and stop/go criteria. Rank essential versus optional enrichment.

**Outputs:** 02_research/data_requirements.md; updated gap register.

**Validation:** Each business question maps to a source, grain and fallback; no silent missing requirement.

**Common mistakes:** Specifying millions of rows before defining a useful grain; assuming catalog titles prove availability.

## 3. Data acquisition

**Objective:** Obtain traceable source snapshots.

**Why it matters:** Reproducibility starts at the original bytes.

**Input:** Approved requirements; S01–S20; source licenses.

**Tools:** requests; browser downloads; GIS REST; checksums; PDF extraction where needed.

**Exact work:** Test S04 resources and S07/S08 query pagination; retrieve Census and dated waste reports; clip OSM responsibly. Capture manifests and exact extraction pages. Use bounded retry/backoff and no paid API.

**Outputs:** 03_data/raw and external snapshots; acquisition_manifest.csv; updated source_catalog local filenames.

**Validation:** Files open; declared format matches content; pagination totals reconcile; checksum and license captured.

**Common mistakes:** Overwriting raw files; extracting a PDF number without its period/unit; treating a failed URL as acquired data.

## 4. Data profiling

**Objective:** Understand grain, coverage and defects before transformation.

**Why it matters:** Prevents incorrect joins and false patterns.

**Input:** Raw snapshots and dictionaries.

**Tools:** DuckDB; pandas; compact profiling scripts.

**Exact work:** Measure rows, distinct IDs, duplicates, date coverage, missingness, value distributions and native units. Check geography overlaps, boundary vintage and source revisions.

**Outputs:** 03_data/interim/profile tables; data-quality log.

**Validation:** Reconcile totals to source; show unresolved null/duplicate rates and row-count differences.

**Common mistakes:** Dropping duplicates without knowing whether they are revisions; calling missing values zeros.

## 5. Data cleaning

**Objective:** Produce validated canonical records.

**Why it matters:** Reliable metrics require controlled transformations.

**Input:** Profile log; raw source; unit map.

**Tools:** Python; DuckDB; GeoPandas.

**Exact work:** Parse dates and IDs without losing leading zeros; normalize only verified units; quarantine invalid rows; version dimensions; preserve source values and conversion rules.

**Outputs:** Clean Parquet in interim; reject log; transformation lineage.

**Validation:** Input = accepted + rejected accounting; PK/FK tests; no overlapping SCD intervals; CRS validation.

**Common mistakes:** Mutating raw; relabeling CRS; joining modern ward IDs to 2011 IDs.

## 6. Large-scale data engineering

**Objective:** Build a practical reproducible fact layer.

**Why it matters:** Shows scale without artificial data inflation.

**Input:** Accepted dimensions; synthetic design; assumptions.

**Tools:** PyArrow; NumPy; Parquet; DuckDB.

**Exact work:** Implement seeded stateful generator only after acquisition gate. Smoke test then benchmark a chunk; scale baseline to 4.38M scheduled records. Partition by run/year/month and enforce watermarks, idempotent outputs and schema contracts.

**Outputs:** 03_data/synthetic; curated Parquet; manifests; performance report.

**Validation:** Deterministic IDs; mass conservation; row count; valid missingness; identical result under chunk-size change; measured memory/time.

**Common mistakes:** Independent random fill values; regenerating without config hashes; partitioning by every bin; claiming synthetic scale is observed IoT.

## 7. SQL analytics

**Objective:** Answer operational questions with auditable SQL.

**Why it matters:** Demonstrates analyst reasoning and efficient data access.

**Input:** Curated facts/dimensions and KPI contracts.

**Tools:** DuckDB SQL; optional BigQuery dialect later.

**Exact work:** Write joins and CASE classifications, GROUP BY/HAVING coverage checks, CTE priority pipelines, correlated/subqueries, LAG/LEAD service intervals, rolling windows, ROW_NUMBER deduplication, RANK zone demand and date/calendar analysis. Handle ties and missing days explicitly.

**Outputs:** 05_sql numbered queries; expected-grain notes; serving marts.

**Validation:** Compare key aggregates with independent Python calculations; inspect query plans and avoid fact fanout.

**Common mistakes:** Windowing across mixed scenarios; counting messages as unique bins; averaging percentages unweighted.

## 8. Excel validation

**Objective:** Provide inspectable human QA.

**Why it matters:** Hiring reviewers can audit formulas and reconcile systems.

**Input:** Small stratified extracts and SQL aggregates.

**Tools:** Excel; Power Query; PivotTables; XLOOKUP; COUNTIFS; SUMIFS; data validation.

**Exact work:** Export a bounded sample plus full-data aggregate controls. Build origin/zone validation lists, dimension lookup checks, duplicates/missing checks, KPI PivotTables and formula-driven reconciliation cells. Document sample seed and extraction SQL.

**Outputs:** 04_excel QA workbook and formula map.

**Validation:** Recalculate in Excel; confirm lookup exceptions and Pivot refresh; workbook totals match declared SQL controls.

**Common mistakes:** Loading multi-million rows into a worksheet; confusing a sample subtotal with full-data total; unchecked cached formula values.

## 9. EDA

**Objective:** Explore variation and service patterns.

**Why it matters:** Focuses forecasting and optimization on plausible drivers.

**Input:** Validated marts, observations and optional proxies.

**Tools:** pandas; matplotlib; seaborn; DuckDB.

**Exact work:** Study seasonality, missingness, zone differences, fill trajectories, service intervals and distributions. Separate real and synthetic panels; annotate sample sizes and time windows.

**Outputs:** 06_python/notebooks EDA; 14_outputs/charts; observations log.

**Validation:** Every chart has unit, grain, denominator, source/origin and uncertainty where relevant.

**Common mistakes:** Presenting simulated patterns as discovered city behavior; charting aggregates with incompatible coverage.

## 10. Descriptive statistics

**Objective:** Summarize central tendency and operational variability.

**Why it matters:** Averages alone hide peak demand and reliability risks.

**Input:** EDA-reviewed records.

**Tools:** NumPy; SciPy; weighted aggregates.

**Exact work:** Report median, quantiles, dispersion, coefficient of variation where meaningful, and weighted district summaries. Compute bootstrap intervals using independent blocks rather than individual readings.

**Outputs:** 07_statistics descriptive tables and assumptions.

**Validation:** Cross-check count and percentile definitions; units consistent; small groups flagged.

**Common mistakes:** Unweighted average of zone rates; treating autocorrelated sensor records as independent samples.

## 11. Hypothesis testing

**Objective:** Evaluate a few predeclared business claims.

**Why it matters:** Adds disciplined uncertainty rather than decorative p-values.

**Input:** Independent replication outcomes or suitable real clustered observations.

**Tools:** SciPy; statsmodels; block/paired bootstrap.

**Exact work:** Pre-register primary cost hypothesis and service non-inferiority margin. Plan replication count/power; inspect paired differences and choose defensible tests; adjust secondary multiplicity; report effect sizes and intervals.

**Outputs:** 07_statistics analysis protocol and later results.

**Validation:** Check dependence, sample size, outliers and test assumptions; keep holdout untouched.

**Common mistakes:** Millions of readings as independent n; causal claims from association; p-hacking simulated parameters.

## 12. Geospatial analytics

**Objective:** Create valid service geography and road paths.

**Why it matters:** Distance and access drive route feasibility.

**Input:** Versioned boundaries, OSM, sites and bins.

**Tools:** GeoPandas; OSMnx; NetworkX dependency; Folium.

**Exact work:** Validate geometry, derive areas, spatially assign bins, quantify unmatched points and POI coverage; construct directed drive graph with buffers and restrictions; audit snapping and facility entrances.

**Outputs:** 08_geospatial graph/geometry artifacts; maps and QA.

**Validation:** Review representative paths and disconnected nodes; map attribution; distance in correct projected/network units.

**Common mistakes:** Euclidean routes; assuming generic drive means truck-safe; treating sparse OSM tags as absence.

## 13. Waste-demand forecasting

**Objective:** Predict demand before collection decisions.

**Why it matters:** Can prevent overflow while avoiding unnecessary visits.

**Input:** Time-stamped observations, known-as-of features and service interventions.

**Tools:** scikit-learn; statsmodels; naive baselines.

**Exact work:** Define target and horizon; create lag/rolling features; rolling-origin backtests and spatial holdout; benchmark simple methods; calibrate uncertainty; isolate future service and weather knowledge.

**Outputs:** 09_forecasting model card; forecasts; backtest report.

**Validation:** MAE/WAPE/pinball/interval coverage; no split leakage; compare downstream decision impact.

**Common mistakes:** Random train/test split; target leakage from latent truth or future collection; claiming field accuracy from synthetic tests.

## 14. Collection prioritization

**Objective:** Convert forecasts into service decisions.

**Why it matters:** Operational value depends on actions, not forecast scores alone.

**Input:** As-of predictions; capacity; service history; guardrails.

**Tools:** Python rules; SQL ranking.

**Exact work:** Implement fixed, threshold and risk-based policies; mandatory max-gap rule; stale sensor fallback; capacity-aware selection and reason codes. Freeze parameters on validation split.

**Outputs:** 10_optimization priority lists and policy configuration.

**Validation:** Every due bin served or explicitly unserved; boundary and missing-sensor cases tested.

**Common mistakes:** Dropping low-priority bins indefinitely; changing thresholds after seeing holdout gains.

## 15. Vehicle route optimization

**Objective:** Find feasible assignments and ordered paths.

**Why it matters:** Turns collection choices into a dispatchable scenario.

**Input:** Due bins, graph matrix, fleet and facility rules.

**Tools:** OR-Tools CVRPTW; route evaluator.

**Exact work:** Start 50–150 stops; implement payload/volume, time windows, compatibility, service duration, depot and disposal legs. Record timeout/status and unserved demand; compare simple routing; scale by documented zones.

**Outputs:** 10_optimization solver config; routes/stops/legs; route maps.

**Validation:** Independent constraint checker; sum leg distance; verify no duplicated mandatory visits; tiny known-feasible/infeasible cases.

**Common mistakes:** Calling a feasible solution optimal; free disposal trips; capacity reset without unloading; routing entire year of readings.

## 16. Cost/fuel analysis

**Objective:** Translate route changes into comparable economics.

**Why it matters:** Distance reduction alone is not a budget saving.

**Input:** Feasible routes; vehicle operations; price and assumption register.

**Tools:** Python; SQL; financial reconciliation.

**Exact work:** Calculate diesel or electric consumption separately, idle use, paid crew time, maintenance and disposal. Separate fixed costs and capex. Match fuel price dates, INR units and cost scope.

**Outputs:** 14_outputs/tables cost bridge; cost model documentation.

**Validation:** Recompute independent sample; reconcile quantities x rates; avoid double-counting contract cost and its components.

**Common mistakes:** Using retail price as actual procurement; treating all saved hours as cash savings; mixing lakh with INR.

## 17. Scenario analysis

**Objective:** Expose sensitivity and operational tradeoffs.

**Why it matters:** Prevents a single optimistic result driving recommendations.

**Input:** Frozen policies, cost ranges and independent demand seeds.

**Tools:** Monte Carlo replication; paired comparisons; sensitivity charts.

**Exact work:** Evaluate demand surges, monsoon disruptions, fuel variation, fleet downtime, sensor failure and service thresholds. Replay shared arrivals and recalculate inventory. Include terminal waste and service failures.

**Outputs:** Scenario comparison tables; uncertainty and tradeoff report.

**Validation:** Matched seeds and budgets; enough replications; worst-case service shown; rerun reproducibility.

**Common mistakes:** Reusing fixed baseline fill traces under altered collection; tuning simulation for guaranteed savings.

## 18. Cloud implementation

**Objective:** Demonstrate warehouse SQL with no billing.

**Why it matters:** Shows portability while keeping costs controlled.

**Input:** Validated compact local marts and SQL.

**Tools:** BigQuery Sandbox browser; local Parquet; documented SQL.

**Exact work:** Recheck S21; confirm no billing; upload only a small frozen sample/aggregate once; use supported queries, scan estimates and partition filters; record job IDs, bytes and reconciliation. Preserve local evidence before expiration.

**Outputs:** 11_cloud SQL, setup notes and evidence.

**Validation:** Local/cloud row and metric parity within stated tolerance; no streaming/DML dependency; account remains unbilled.

**Common mistakes:** Activating a trial or attaching billing; assuming deleting data refunds lifetime storage; treating cloud as backup.

## 19. Power BI data model

**Objective:** Build a clear semantic layer.

**Why it matters:** Prevents inconsistent dashboard measures.

**Input:** Reconciled daily and route marts.

**Tools:** Power BI Desktop; Power Query; DAX.

**Exact work:** Import serving marts, conformed dimensions and proper dates; set single-direction relationships; separate real and simulated measures; implement weighted KPI measures and origin labels.

**Outputs:** 12_powerbi model specification; later PBIX/PBIP where supported.

**Validation:** Unique dimension keys; no ambiguous filters; SQL/DAX totals agree by date/zone/scenario.

**Common mistakes:** Many-to-many shortcuts; summing inventory over time; importing every raw reading by default.

## 20. Dashboard development

**Objective:** Make operational findings usable and reviewable.

**Why it matters:** A portfolio needs a coherent decision narrative.

**Input:** Validated semantic model and scenario evidence.

**Tools:** Power BI Desktop.

**Exact work:** Create executive service/cost view, collection priority map, fleet/route view, forecast evaluation, and provenance/quality page. Add meaningful slicers, accessible colors, tooltips and explicit simulation banners.

**Outputs:** 12_powerbi dashboard; 14_outputs screenshots and user guide.

**Validation:** Test slicer combinations, zero/missing states, refresh, map attribution and screen readability.

**Common mistakes:** Decorative KPIs; unsupported savings headlines; omitting limitations; assuming paid publishing is required.

## 21. Testing and QA

**Objective:** Prove the analytical chain is consistent.

**Why it matters:** Trust requires more than code running.

**Input:** Contracts and every implemented stage.

**Tools:** pytest; DuckDB assertions; independent reconciliation; CI later.

**Exact work:** Test PK/FK, units, null status, temporal leakage, simulation mass balance, route feasibility, cost arithmetic and Python/SQL/Excel/BI parity. Include corrupt fixtures and expected failures. QA runs throughout earlier workstreams.

**Outputs:** 13_testing suite; quality report; reproducibility log.

**Validation:** All critical checks pass; tolerances and exclusions documented; fresh-environment rerun.

**Common mistakes:** Tests that mirror implementation; passing tests on only happy paths; claiming scaffold checks validate nonexistent data.

## 22. Business recommendations

**Objective:** Turn evidence into bounded decisions.

**Why it matters:** Connects technical work to an implementable pilot.

**Input:** Validated scenarios and uncertainty.

**Tools:** Decision memo; scenario tradeoff matrix.

**Exact work:** Identify where collection policy helps, where it fails, fleet/bin allocation implications and field-pilot design. Distinguish modeled benefits, requirements and measured evidence; cost sensors and change management.

**Outputs:** 14_outputs/reports recommendation memo and pilot measurement plan.

**Validation:** Every claim traceable; tradeoffs and service risks visible; no causal/realized savings claim from simulation.

**Common mistakes:** Presenting a simulation as municipal deployment; promising financial return without lifecycle costs.

## 23. GitHub portfolio packaging

**Objective:** Create a reproducible hiring-quality evidence package.

**Why it matters:** Reviewers need to inspect reasoning and rerun key work.

**Input:** Validated scripts, reports, notebooks, tests and attribution.

**Tools:** Git/GitHub; Markdown; small licensed sample; CI.

**Exact work:** Polish README with business question, architecture, screenshots, real/synthetic split, results and limitations. Add setup lock, test commands, data-acquisition instructions, commits and a short walkthrough. Check licenses/secrets/large files; publish only when requested.

**Outputs:** Versioned repository; portfolio case study; reproducibility release checklist.

**Validation:** Clean clone/sample run succeeds; links work; every claimed skill has a verifiable artifact.

**Common mistakes:** Committing raw restricted data or secrets; fake results/screenshots; technology lists without analytical evidence.

## Two-city expansion — 25 September 2026

Completed expansion across the existing workstreams without repeating Chennai generation: six additional sources; 500 Coimbatore bins and 2.19M readings; city/global-key canonical model; 24 parameterized SQL executions; descriptive comparison with inference withheld; independent forecasting, spatial and routing pipelines; two-city Power BI exports/specification. The 23-workstream roadmap remains intact. Historical phase completion figures refer to Chennai; current totals and open deployment gaps are in PROJECT_STATE.md. Next authorized scope is a later explicitly requested Phase 5, not automatic dashboard construction.

## Phase 5 — business intelligence

Completed the Power BI preparation branch of workstreams 19–22 using the two-city canonical database: five dimensions, nine facts, 16 single-direction relationships, documented DAX, a theme, five-page layouts, import instructions, SQL/Python reconciliation and evidence-bounded recommendations. Power BI Desktop execution is unavailable in this environment; the PBIX/rendered visual QA remains a later manual step. Final portfolio audit/workstream 23 is not started. The archived prior state is `docs/two_city_state_snapshot.md`.
