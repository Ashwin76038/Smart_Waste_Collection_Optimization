# Smart Waste — 60-second review

**Problem:** prioritize collection and route a constrained fleet without pretending simulated telemetry is municipal evidence.

**Built:** a source-documented Tamil Nadu analytics workflow with 6.57 million synthetic two-hour readings, 1,500 hypothetical bins, 300 real ward geometries, partitioned Parquet, DuckDB marts, business SQL, time-split forecasting, OR-Tools routing and an actual five-page Power BI Desktop report.

**Results:** known-bin forecast MAE 8.17/7.69 percentage points (Chennai/Coimbatore). Matched one-day synthetic route pilots reduce distance 20.66%/27.26% versus a nearest-neighbor baseline. These are model results, not realized municipal achievements.

**Engineering evidence:** immutable raw hashes, separated simulation truth, global city keys, meaningful integration tests, 52 SQL/Python KPI reconciliations and 52 historical Desktop DAX checks.

**Judgment:** report forecast recall and undercoverage; retain negative overflow outcomes; do not infer causality from one synthetic year. BigQuery was designed but not executed.

**Review order:** [README](../README.md) → [final report](../FINAL_PROJECT_REPORT.md) → [audit](FINAL_AUDIT.md) → [SQL](../05_sql/phase3_business_questions.sql) → [advanced methodology](phase4_methodology.md) → [Power BI delivery](../12_powerbi/DESKTOP_DELIVERY.md).
