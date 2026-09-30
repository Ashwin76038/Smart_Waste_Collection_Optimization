# BigQuery Sandbox handoff

**Execution status: not run.** No Google Cloud account, project, dataset, table, job or screenshot was created in Phase 2. A browser login and account setup are unavailable through the local pipeline, and no billing service was enabled.

Official current documentation: https://docs.cloud.google.com/bigquery/docs/sandbox (S21). As reviewed in Phase 1, Sandbox has 10 GiB lifetime storage, 1 TiB monthly query processing and 60-day table expiration; features such as DML, streaming and Data Transfer Service are unavailable. Recheck before use. Deletion does not restore lifetime storage quota.

The reproducible local export `11_cloud/zone_daily_sample.csv` contains a complete January subset of the synthetic zone daily mart. Its rows are **synthetic** and route-distance values are excluded. The sample is enough to demonstrate SQL syntax and local/cloud parity, not real city performance.

Steps for a future no-billing owner:
1. Open the BigQuery console and confirm the project explicitly shows Sandbox status with **no billing account attached**. If it requests billing, stop and keep the DuckDB result.
2. Create a dataset named `smart_waste_demo` in an allowed location. Use the console's local-file upload for `zone_daily_sample.csv`, CSV header skip 1, and set the exact schema in `bigquery_sandbox_demo.sql`. Choose the date partition and zone cluster if the console upload supports them. If not, create the table with the SQL DDL first and then load via a supported console path.
3. Inspect the upload job and record job ID, actual bytes, row count, table expiration and screenshot of no-billing Sandbox status, query result and estimated bytes scanned. Redact account identifiers in portfolio screenshots. Save evidence in `11_cloud/evidence/`.
4. Run the two SELECTs in the SQL file after replacing `YOUR_PROJECT_ID`. Compare row count and scheduled/received/collected sums to the local `11_cloud/local_sample_controls.json`, allowing only a declared floating-point tolerance. Never count a created table as a verified query.
5. Export screenshots/query job details before automatic expiration. Do not enable free trial, cloud storage or paid billing for this project.

SQL file is an exact template with a project-ID placeholder because no user account is available. A future operator must fill the placeholder; no false cloud execution claim is made.

## Two-city expansion — 25 September 2026

Prepared only; no cloud execution occurred. `two_city_daily_upload.csv` contains 730 city-days. In an existing no-billing BigQuery Sandbox, create the `smart_waste` dataset, run the CREATE TABLE in `two_city_sandbox.sql` (replace YOUR_PROJECT with the actual project ID), then use Create table / Upload / CSV into that table, skip one header row and retain the exact schema. Set write disposition to append only for the first load; avoid duplicate reloads. Confirm 730 rows and 365 per city using the saved query. Inspect estimated bytes before querying and use the city/date predicates. Capture later screenshots of no-billing sandbox status, schema, row reconciliation and query results. Do not activate billing or claim successful execution from this local preparation.
