# Interview guide

## Why this project?
It connects an operational decision to data quality, prediction and constrained planning. It demonstrates analytical judgment: a shorter route can worsen overflow, and simulation cannot prove city savings.

## Why millions of rows?
1,500 bins × 365 days × 12 slots = 6,570,000 scheduled events. This gives a realistic engineering grain without claiming a real IoT installation. Canonical copies are not extra observations.

## Why Parquet and DuckDB?
Typed compressed columnar files support partition and column pruning. DuckDB aggregates locally without loading the whole fact table into Pandas or Excel. Cite the one-month benchmark, not a universal speedup; its file-size schemas differ.

## Why cloud?
Sandbox SQL demonstrates a migration path, but no authenticated BigQuery run occurred. The system works locally without billing. Do not claim cloud execution experience from prepared SQL.

## SQL decisions
Keep event, attempt, bin-day and scenario grains separate. Join on city-qualified keys; retain numerators/denominators for weighted rates. Distinguish physical overflow slots from days with any overflow and avoid double-counting alternative route methods.

## Statistical tests
Use weekly paired weekend-minus-weekday contrasts to reduce repeated-bin pseudoreplication; HAC handles serial dependence approximately. Report Holm-adjusted p-values, effect sizes and sensitivity to lag choice. With51 blocks and a programmed weekend factor, significance validates a simulator mechanism only.

## Forecast choice and leakage
Compare simple baselines before fixed-alpha Ridge. Split by target date; fit preprocessing on training; exclude latent truth/future labels; withhold bin identities. Their own past readings remain available, so this is not zero-history cold start. Report MAE alongside near-full recall and empirical interval coverage.

## OR-Tools
Mandatory visits, volume/payload dimensions, shift limits and depot returns represent a defensible constrained pilot. Use identical demand and road matrices for the baseline. Full-bin reserve may overstate fleet needs; five-second search is feasible optimization, not proof of optimality.

## Power BI
Five dimensions and nine facts with16 single-direction relationships. Thirty-five measures keep scenario metrics under single-city/scenario context.52 Desktop checks reconcile to exported data. Explain offline PBIX versus unexecuted Service refresh and local absolute source paths.

## Hardest limitations
No observed municipal telemetry/GPS, one seed/year, community boundary vintage, missing road restrictions, stale-price proxy, limited overflow recall and a24-hour counterfactual without subsequent routine service. Do not annualize a one-day saving.

## What changes with real IoT?
Validate sensor calibration, timestamps and missingness; build real bin/asset history and service labels; use actual truck GPS and legal depot access; retrain with rolling-origin validation; calibrate risk under the changed service policy; run a prospective matched pilot before making causal savings claims. Add privacy/access controls and operational monitoring only when real data warrants them.

## Honest resume discussion
Explain exactly which steps ran locally, which outputs are synthetic, which checks were independently reconciled, and why real operational deployment is outside the evidence.
