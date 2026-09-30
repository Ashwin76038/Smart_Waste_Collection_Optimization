# Phase 5 — business intelligence handoff

The two-city **synthetic** operations are now shaped for a five-page Power BI report. The model has five dimensions and nine facts, with 16 tested, single-direction relationship paths. The 6.57 million sensor/event rows remain available through Parquet and DuckDB; the BI import uses preaggregated, keyed analytical tables and preserves the collection-attempt detail needed for service diagnostics.

Power BI Desktop is unavailable in this environment; no PBIX, rendered Power BI dashboard or publish has been produced. The ready-to-import CSVs, star diagram, DAX, theme, wireframes and exact manual build guide are in [12_powerbi](../../12_powerbi/PHASE5_MODEL.md). The five pages are Executive Overview, Waste & Bin Analysis, Geographic Intelligence, Route Optimization, and Forecasting & Operations Planning. A normalized City Comparison panel belongs to the overview. Interactive city-specific geographic HTML maps from Phase 4 remain companion artifacts.

## Tested values and reconciliation

SQL against the canonical database and independent Pandas calculations on the exported BI CSVs agree for **52 city-specific KPI checks**. All **16 relationship/foreign-key checks** and all table-grain uniqueness checks pass. The [QA receipt](../../12_powerbi/phase5_model/qa_receipt.json) and [row-level comparison table](../../12_powerbi/phase5_model/kpi_reconciliation.csv) retain exact results and tolerances. Attempt-collected mass differs from preaggregated daily mass by 0.37 kg Chennai and 0.17 kg Coimbatore over the year due to float32 rounding; dashboard collected tonnes uses collection attempts consistently.

The base matched simulated pilot remains Chennai 57.3439→45.4983 km and Coimbatore 38.4570→27.9743 km. Measures require one city and one scenario, and infeasible alternatives leave savings blank. Early collections below 35% are a retrospective synthetic diagnostic. Physical overflow slot rate uses scheduled two-hour readings; overflow bin-day rate uses days with any spill. These are intentionally different denominators. Forecast MAE is in fill percentage points and model scores are city-specific.

## Operating decisions

The [recommendations](../../12_powerbi/PHASE5_RECOMMENDATIONS.md) propose ward field audits, a constrained three-truck pilot and threshold/forecast review with staff oversight. They point to the [ward audit candidates](../../12_powerbi/phase5_model/ward_audit_candidates.csv) and [threshold tradeoffs](../../12_powerbi/phase5_model/threshold_tradeoffs.csv). Real bin telemetry, comparable route GPS, verified fleet/depot/receiving points and local procurement prices are required before deployment or budget claims. Coimbatore's 0.9 demand multiplier is an assumption, not observed city demand. No inferential city-performance ranking is made.

Phase 5 ends here. A later Desktop session must build and visually test the PBIX, then a separate final portfolio audit may evaluate publication readiness.
