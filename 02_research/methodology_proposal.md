# Methodology proposal

## Two evidence tracks
Track A profiles official municipal waste and demographics at their native grain. Track B tests a hypothetical bin collection system on real Chennai geography, with documented operational assumptions. Link them for context, not by falsely allocating all municipal waste to bins. Calibration is conditional on matching waste streams, period and geography; otherwise use broad scenario ranges and disclose the mismatch.

## Baselines and estimands
Compare (A) fixed calendar collection with a reproducible simple route, (B) observed-fill threshold collection with the same routing heuristic, and (C) forecast-informed selection with constrained routing. Add fixed selection + optimized routes to isolate routing from collection-selection effects. Baseline frequencies are scenario assumptions unless actual schedules are acquired. Compare the same demand realization, fleet, service area, initial bin inventory and cost period. End-of-horizon waste and mandatory service obligations must be included.

Primary estimand: paired difference in total variable operating cost over an evaluation horizon, conditional on satisfying predeclared service constraints. Report distance, overflow bin-hours, missed service, labour and payload utilization alongside cost. A lower cost with materially worse service is not an efficiency win.

## Synthetic design for a later phase
Target 1,000 bins x 365 days x 12 two-hour slots = 4,380,000 scheduled readings for one baseline run. Counts are design choices, not actual Chennai asset counts. A 500-bin design yields 2,190,000 rows; a 1,200-bin design yields 5,256,000 rows. Do not inflate volume by duplicating rows or scenarios. Availability flags preserve scheduled rows; a separate received-message view excludes dropouts.

Generate shared exogenous waste-arrival processes using seeded random streams per bin and day. Use nonnegative compound Poisson/Gamma arrivals with bin-specific random effects, weekday and intraday patterns, optional seasonal effects, and uncertain event/POI effects. Proposed distribution choices require calibration or sensitivity; no coefficients are currently estimated.

State transition in kg: inventory_next = inventory_previous + arrivals - removed - overflow_loss. Maintain volume with a separately documented density/composition model. Sensor fill is clipped to 0–100%; latent over-capacity mass and overflow duration remain in simulation truth. Include residual after collection, partial/failed service, sensor noise, drift, stuck readings, missing messages, late arrivals and battery resets with configurable rates. Bin temperature is a simulated measurement, not copied weather under a real label.

Store latent arrivals/true inventory separately from observed readings. Forecast training and prioritization may only read as-of observations. Counterfactual policies replay the same arrivals but recompute inventory, collections and overflow: do not reuse baseline fill traces unchanged after altering service decisions. Same seed and configuration must reproduce stable rows regardless of chunk order. Do not make the generator use the same equations as the forecasting model and call that independent validation.

Generate later in bin/month chunks, enforce unique (simulation_run_id, bin_id, timestamp_utc), write Parquet by run/year/month, avoid partitioning by each bin, and record actual rows/bytes/runtime/peak RAM. First run a 10-bin, 7-day smoke scenario, then a representative chunk to estimate storage. No performance measurements or full data generation in Phase 1.

## Forecasting and prioritization
Predict next-24-hour arrivals or fill conditional on planned collection; alternatively estimate probability of capacity exceedance before next service. Separate these targets. Begin with persistence and seasonal naive benchmarks, then regularized lag-feature regression/gradient boosting only if gains justify complexity. Use rolling-origin splits, final untouched time holdout and a spatial/bin holdout. Fit imputers and scalers on training folds only. Evaluate MAE/WAPE, quantile coverage/pinball loss and downstream service performance. Future realized rainfall is unavailable at dispatch time; use lagged weather or a documented forecast source.

Priority combines predicted overflow risk with maximum time since service and any sensitive-site constraints. Freeze thresholds on validation data. Stale/missing sensors trigger a conservative fallback policy; no skipped service just because telemetry vanished. Record override reasons and exclude protected personal information.

## Statistics and hypothesis tests
Primary simulation hypothesis: candidate policy has no reduction in paired total variable cost across independent demand replications. Analyze one paired horizon result per seed, not millions of dependent readings. Predeclare two-sided alpha 0.05, practical effect threshold, confidence intervals and replication/power planning; use paired t-test only if differences are appropriate, otherwise paired permutation/bootstrap. Rejecting a simulation null is not evidence of field savings.

Secondary service non-inferiority hypothesis uses an explicitly chosen overflow margin; define it before evaluation. For real observations, compare waste across calendar groups using area/time adjustment and block bootstrap or regression with clustered errors. Require enough independent clusters and check autocorrelation, heteroskedasticity, outliers and missingness. Pre-register a small primary test set; use Holm correction for multiple secondary tests. Correlation between POI density and waste is associational. No valid test will be forced when data are insufficient.

## Geospatial and routing
Preserve source boundaries; derive bin assignment with a spatial join, retaining unmatched and boundary points for review. Use EPSG:4326 for display and EPSG:32644 metres for Chennai distance/area processing. Road distance comes from directed network paths, not Euclidean map lines. Snap stops to legal accessible edges with a maximum-distance rule. Use real facility entrances if verified.

Start with 50–150 selected stops, a small fleet and one depot. OR-Tools CVRPTW constraints: vehicle payload kg and volume, waste compatibility, stop service time, shift and receiving windows, directed travel times, start/end depots and mandatory service. Initially model one disposal trip per route; multi-trip reload is a later explicit extension, not an implicit capacity reset. Export separate stops and legs to audit paths. Scale to zones after feasibility tests, while reporting cross-zone restrictions and decomposition tradeoffs.

Set reproducible solver seed where supported, wall-clock limit and search configuration; record status, objective, unserved mandatory stops and solver bound only if available. Never label a time-limited feasible solution globally optimal. Straight-line distance is only a sanity lower bound, not the route-cost matrix.

## Costs and robustness
Fuel litres = road km / assumed or measured km_per_litre + idle_hours * idle_litres_per_hour. For battery vehicles use separate kWh/km and tariffs; do not apply diesel factors to them. Labour is crew-size times paid hours times hourly cost. Add only non-overlapping maintenance/disposal components. Separate theoretical variable savings from cash-releasing savings and capital/sensor/software lifecycle costs. Price year and source are mandatory; sensitivity must include fuel, demand, service time, fleet downtime and sensor error.

Report low/base/high assumption sets and uncertainty bands across replications. Do not choose scenarios merely to guarantee improvement. If candidate routes cannot meet service constraints, report infeasibility and the needed fleet/service changes.

## Two-city expansion — 25 September 2026

Implemented two-city methods are in `docs/two_city_model.md` (project-root path). Shared simulation mechanisms use distinct seeds/locations and a clearly assumed CBE 0.9 demand scale. Comparisons normalize by bin-days/readings and retain denominators. Different city layouts and pilot stops prohibit interpreting raw route distances as municipal efficiency. Independent chronological forecasting, within-city matched route baselines and scenario-specific capacity checks are used. No empirical city-effect significance test is valid from these assumed demand differences. Historic Chennai price is only a common-price proxy in CBE. Full observed-data calibration remains a future requirement.
