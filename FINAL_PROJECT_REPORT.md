# Final project report

## Problem and scope
Fixed waste-collection schedules can mismatch demand. This portfolio demonstrates the complete decision chain: acquire geographic/context data; simulate clearly labelled operations; validate and aggregate; explore patterns; forecast fill; prioritize bins; route a constrained fleet; present auditable management KPIs.

## Data and methods
The two-city canonical fact contains6,570,000 synthetic readings (4,380,000 Chennai;2,190,000 Coimbatore). Twenty-six raw assets from24 source IDs were SHA256-verified in the final audit. Real ward geometry and OSM roads anchor hypothetical deployments. Census2011 and NASA2025 context are not current operational calibration. Observations and simulation truth are separated.

Monthly CSV is converted through interim to observed Parquet. DuckDB partition pruning, typed marts and city-qualified keys support SQL/Python analysis and a Power BI model. Forecasts use chronological training/validation/test target dates and baselines before Ridge. Priority uses explicit risk/telemetry/service-gap rules rather than arbitrary weighted scores. Directed-road routing enforces capacity, payload, shifts and return-to-depot constraints.

## Results
Known-bin test forecast MAE is8.16665pp Chennai and7.68679pp Coimbatore; near-full recall is56.18%/57.97%. Nominal90% bands cover88.45%/88.22%, so operational thresholds need caution.

The matched three-truck pilot serves36/34 required bins. Distance changes from57.34388 to45.49833km Chennai and38.45702 to27.97431km Coimbatore:20.66%/27.26% lower. At assumed4.5km/L and historical INR92.39/L, fuel-cost differences are INR243.20/215.22. They are one-date hypothetical benefits, not realized savings.

Two51-week HAC tests reproduce programmed weekend differences, with effect sizes and confidence intervals. They do not establish real municipal behavior. Separately reconstructed counterfactual records agree to numerical precision; some route scenarios increase overflow, so distance is not a sufficient service objective.

## Dashboard and validation
The actual local PBIX contains five pages,14 imported analytical tables,16 relationships and35 measures. Historical Desktop DAX checks passed52/52; the final audit rechecked archive integrity and unchanged SHA256. SQL/Python52-KPI reconciliation and16 links were rerun. Test/coverage details and limitations are in [FINAL_AUDIT](docs/FINAL_AUDIT.md).

## Recommendations
1. Start with a shadow pilot: verify hypothetical bin/road/depot assumptions and record actual sensor and truck performance.
2. Review high-risk and stale-telemetry bins manually; limited near-full recall makes autonomous dispatch premature.
3. Compare thresholds using spill, service completion and distance jointly; retain negative outcomes.
4. Use ward candidates as field-audit leads, not evidence to relocate assets or purchase trucks.
5. Establish real fuel, wage, vehicle and transfer-station constraints before financial appraisal; do not annualize these pilot savings.

## Limitations and readiness
Share as an auditable analytics simulation. It is not production-ready municipal decision software. Real operational data, clean-machine end-to-end replay, executed cloud analytics, extensive UI acceptance and causal policy evaluation remain gaps. Source repository excludes large data, binaries and uncertain-license raw downloads; reproduction steps describe the remaining external dependencies.
